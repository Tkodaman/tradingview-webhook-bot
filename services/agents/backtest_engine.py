import os
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List, Dict, Any
from core.config import settings
from core.logger import logger
import traceback

try:
    import alpaca_trade_api as tradeapi
except ImportError:
    tradeapi = None

class BacktestResult(BaseModel):
    threshold: int
    total_trades: int
    win_rate: float
    avg_rr: float
    max_drawdown_pct: float
    total_pnl_pct: float
    sharpe_ratio: float

class BacktestEngine:
    def __init__(self, symbols: List[str], timeframe='15Min', days_back=30):
        self.symbols = symbols
        self.timeframe = timeframe
        self.days_back = days_back
        
        api_key = settings.alpaca_api_key or os.getenv("ALPACA_API_KEY", "")
        secret_key = settings.alpaca_secret_key or os.getenv("ALPACA_SECRET_KEY", "")
        base_url = 'https://paper-api.alpaca.markets'
        self.api = tradeapi.REST(api_key, secret_key, base_url, api_version='v2')
        
    def fetch_data(self, symbol: str) -> pd.DataFrame:
        end = datetime.now()
        start = end - timedelta(days=self.days_back)
        
        tf_map = {
            '1Min': tradeapi.TimeFrame.Minute,
            '5Min': tradeapi.TimeFrame(5, tradeapi.TimeFrameUnit.Minute),
            '15Min': tradeapi.TimeFrame(15, tradeapi.TimeFrameUnit.Minute),
            '1Hour': tradeapi.TimeFrame.Hour,
            '1Day': tradeapi.TimeFrame.Day,
        }
        
        tf = tf_map.get(self.timeframe, tradeapi.TimeFrame.Minute)
        try:
            bars = self.api.get_bars(
                symbol, 
                tf, 
                start=start.strftime('%Y-%m-%d'), 
                end=end.strftime('%Y-%m-%d'), 
                feed='iex',
                limit=10000,
                adjustment='all'
            ).df
            
            if bars.empty:
                return pd.DataFrame()
            
            # Reset index to make timestamp a column
            bars = bars.reset_index()
            return bars
        except Exception as e:
            logger.error(f"Backtest Fetch Error for {symbol}: {e}")
            return pd.DataFrame()
            
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate the 9 Decision Engine indicators using pandas-ta"""
        # RSI
        df['RSI'] = ta.rsi(df['close'], length=14)
        
        # MACD
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        if macd is not None:
            df['MACD'] = macd['MACD_12_26_9']
        else:
            df['MACD'] = 0.0
            
        # EMAs
        df['EMA20'] = ta.ema(df['close'], length=20)
        df['EMA50'] = ta.ema(df['close'], length=50)
        df['EMA200'] = ta.ema(df['close'], length=200)
        
        # Stoch K
        stoch = ta.stoch(df['high'], df['low'], df['close'])
        if stoch is not None:
            df['StochK'] = stoch['STOCHk_14_3_3']
        else:
            df['StochK'] = 50.0
            
        # ADX
        adx = ta.adx(df['high'], df['low'], df['close'])
        if adx is not None:
            df['ADX'] = adx['ADX_14']
        else:
            df['ADX'] = 0.0
            
        # ATR
        df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        
        # CMF (Chaikin Money Flow)
        df['CMF'] = ta.cmf(df['high'], df['low'], df['close'], df['volume'], length=20)
        
        # Volume Ratio (Current volume vs 50 period average volume as a proxy for 10-day)
        df['VolAvg'] = ta.sma(df['volume'], length=50)
        df['VolRatio'] = df['volume'] / df['VolAvg']
        
        # Change Pct
        df['ChangePct'] = df['close'].pct_change() * 100
        
        return df.dropna()
        
    def simulate_trades(self, df: pd.DataFrame, threshold: int) -> dict:
        in_position = False
        entry_price = 0.0
        
        trades = []
        equity_curve = [10000.0]
        current_equity = 10000.0
        
        for idx, row in df.iterrows():
            close = row['close']
            high = row['high']
            low = row['low']
            
            # Logic variables
            rsi = row['RSI']
            macd = row['MACD']
            ema20 = row['EMA20']
            ema50 = row['EMA50']
            ema200 = row['EMA200']
            vwap = row['vwap']
            stoch_k = row['StochK']
            adx = row['ADX']
            atr = row['ATR']
            cmf = row['CMF']
            vol_ratio = row['VolRatio']
            chg = row['ChangePct']
            
            atr_pct = (atr / close) * 100 if close > 0 else 1.5
            
            if in_position:
                # Check exit conditions
                # Fixed SL/TP for simulation (local risk manager)
                tp = entry_price * 1.03
                sl = entry_price * 0.985
                
                exit_price = 0.0
                reason = ""
                
                if high >= tp:
                    exit_price = tp
                    reason = "TP"
                elif low <= sl:
                    exit_price = sl
                    reason = "SL"
                elif rsi > 72.0 or macd < -1.5:
                    exit_price = close
                    reason = "SIGNAL_EXIT"
                    
                if exit_price > 0:
                    in_position = False
                    pnl_pct = (exit_price - entry_price) / entry_price
                    pnl_amt = current_equity * pnl_pct
                    current_equity += pnl_amt
                    trades.append({
                        'entry': entry_price,
                        'exit': exit_price,
                        'pnl_pct': pnl_pct,
                        'reason': reason
                    })
            else:
                # Check entry conditions
                score = 0
                if 40.0 <= rsi <= 72.0: score += 1
                if macd >= -0.50: score += 1
                if ema20 > ema50 > ema200: score += 1
                if close >= vwap: score += 1
                if vol_ratio >= 0.70: score += 1
                if 20.0 <= stoch_k <= 90.0: score += 1
                if adx >= 15.0: score += 1
                if atr_pct <= 6.0: score += 1
                if cmf > 0.05: score += 1
                
                if chg >= 1.2 and vol_ratio >= 0.8: 
                    score += 3
                    
                if score >= threshold:
                    in_position = True
                    entry_price = close
                    
            equity_curve.append(current_equity)
            
        # Metrics Calculation
        total_trades = len(trades)
        if total_trades > 0:
            winning_trades = len([t for t in trades if t['pnl_pct'] > 0])
            win_rate = (winning_trades / total_trades) * 100
            
            winners = [t['pnl_pct'] for t in trades if t['pnl_pct'] > 0]
            losers = [abs(t['pnl_pct']) for t in trades if t['pnl_pct'] < 0]
            avg_win = sum(winners)/len(winners) if winners else 0
            avg_loss = sum(losers)/len(losers) if losers else 0
            avg_rr = avg_win / avg_loss if avg_loss > 0 else 0
        else:
            win_rate = 0.0
            avg_rr = 0.0
            
        total_pnl_pct = ((current_equity - 10000.0) / 10000.0) * 100
        
        equity_series = pd.Series(equity_curve)
        rolling_max = equity_series.cummax()
        drawdowns = (equity_series - rolling_max) / rolling_max
        max_drawdown = abs(drawdowns.min() * 100)
        
        returns = equity_series.pct_change().dropna()
        sharpe = (returns.mean() / returns.std() * np.sqrt(252 * (len(df)/252))) if returns.std() != 0 else 0
        
        return {
            'threshold': threshold,
            'total_trades': total_trades,
            'win_rate': round(win_rate, 2),
            'avg_rr': round(avg_rr, 2),
            'max_drawdown_pct': round(max_drawdown, 2),
            'total_pnl_pct': round(total_pnl_pct, 2),
            'sharpe_ratio': round(sharpe, 2)
        }
        
    def run_sweep(self) -> List[BacktestResult]:
        results = []
        thresholds = [4, 5, 6, 7, 8]
        
        for sym in self.symbols:
            logger.info(f"[BACKTEST] Fetching {sym}...")
            df = self.fetch_data(sym)
            if df.empty:
                continue
                
            logger.info(f"[BACKTEST] Calculating indicators for {sym}...")
            df = self.calculate_indicators(df)
            
            for th in thresholds:
                res = self.simulate_trades(df, th)
                results.append(res)
                
        # Aggregate by threshold
        agg = []
        for th in thresholds:
            th_results = [r for r in results if r['threshold'] == th]
            if not th_results:
                continue
            
            total_tr = sum(r['total_trades'] for r in th_results)
            avg_wr = sum(r['win_rate'] for r in th_results) / len(th_results)
            avg_pnl = sum(r['total_pnl_pct'] for r in th_results) / len(th_results)
            avg_dd = sum(r['max_drawdown_pct'] for r in th_results) / len(th_results)
            avg_rr = sum(r['avg_rr'] for r in th_results) / len(th_results)
            avg_sh = sum(r['sharpe_ratio'] for r in th_results) / len(th_results)
            
            agg.append(BacktestResult(
                threshold=th,
                total_trades=total_tr,
                win_rate=round(avg_wr, 2),
                avg_rr=round(avg_rr, 2),
                max_drawdown_pct=round(avg_dd, 2),
                total_pnl_pct=round(avg_pnl, 2),
                sharpe_ratio=round(avg_sh, 2)
            ))
            
        return agg

backtest_engine = BacktestEngine(symbols=["SPY"])
