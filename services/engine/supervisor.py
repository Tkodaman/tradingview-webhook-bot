import time
from datetime import datetime, timezone, timedelta
from core.logger import logger
from services.broker.alpaca_client import alpaca_client
from services.market_feed.live_stream import live_trade_manager

class SupervisorAgent:
    def __init__(self):
        self.dynamic_risk_multiplier = 1.0  # 1.0 means 15% budget (default)
        self.last_eod_report_date = None

    def monitor_positions(self):
        """
        Runs every 1-5 minutes to fetch active positions from Alpaca 
        and evaluate PnL trajectories.
        """
        logger.info("👁️ [SUPERVISOR] Position Monitoring Cycle Started...")
        open_positions = alpaca_client.sync_open_positions()
        
        if not open_positions:
            logger.info("👁️ [SUPERVISOR] No open positions currently.")
            return

        total_unrealized_pnl = 0.0
        for pos in open_positions:
            sym = pos.get("symbol")
            pnl = float(pos.get("unrealized_pl", 0.0))
            pnl_pct = float(pos.get("unrealized_plpc", 0.0)) * 100
            total_unrealized_pnl += pnl

            # Basic trajectory analysis
            if pnl_pct > 2.0:
                logger.info(f"📈 [SUPERVISOR] {sym} performing well (+{pnl_pct:.2f}%). Target approaching.")
            elif pnl_pct < -2.0:
                logger.warning(f"📉 [SUPERVISOR] {sym} struggling ({pnl_pct:.2f}%). Stop-loss risk elevated.")
            else:
                logger.info(f"⚖️ [SUPERVISOR] {sym} in consolidation ({pnl_pct:.2f}%).")

        logger.info(f"👁️ [SUPERVISOR] Portfolio Total Unrealized PnL: $")

    def calculate_dynamic_risk(self):
        """
        Estimates market volatility (simplified here as we lack a direct VIX feed, 
        using average spread or proxy from active assets) and adjusts the risk multiplier.
        Base budget is 15%. Max is 20% (Multiplier: 1.33). Min is 5% (Multiplier: 0.33).
        """
        logger.info("⚖️ [SUPERVISOR] Evaluating Dynamic Risk/Volatility...")
        
        # We can use the bid-ask spread of SPY or QQQ as a proxy for volatility.
        # Higher spread = higher volatility = lower risk budget.
        spy_spread = alpaca_client.get_bid_ask_spread("SPY")
        qqq_spread = alpaca_client.get_bid_ask_spread("QQQ")
        
        avg_spread = (spy_spread + qqq_spread) / 2.0 if (spy_spread > 0 and qqq_spread > 0) else 0.05
        
        # Heuristic: 
        # Normal spread for SPY/QQQ is ~0.02%. 
        # High volatility spread > 0.10%.
        if avg_spread >= 0.10:
            self.dynamic_risk_multiplier = 0.33  # 5% budget
            logger.warning(f"⚠️ [SUPERVISOR] High Volatility Detected (Spread: {avg_spread:.3f}%). Reducing budget to 5%.")
        elif avg_spread <= 0.03:
            self.dynamic_risk_multiplier = 1.33  # ~20% budget
            logger.info(f"✅ [SUPERVISOR] Low Volatility Detected (Spread: {avg_spread:.3f}%). Increasing budget to 20%.")
        else:
            self.dynamic_risk_multiplier = 1.0   # 15% budget
            logger.info(f"⚖️ [SUPERVISOR] Normal Volatility (Spread: {avg_spread:.3f}%). Budget remains at 15%.")

        return self.dynamic_risk_multiplier

    def generate_eod_report(self):
        """
        Generates an End-of-Day performance report summarizing closed trades, PnL, and sequential stop-losses.
        """
        today = datetime.now(timezone.utc).date()
        if self.last_eod_report_date == today:
            return  # Already generated today

        logger.info("📊 [SUPERVISOR EOD REPORT] Generating Daily Portfolio Summary...")
        
        if not alpaca_client.api_key:
            logger.info("📊 [SUPERVISOR] Simulated Mode: EOD Data not available.")
            return

        try:
            import requests
            headers = {
                "APCA-API-KEY-ID": alpaca_client.api_key,
                "APCA-API-SECRET-KEY": alpaca_client.api_secret,
                "accept": "application/json"
            }
            
            # Fetch today's closed orders
            url = f"{alpaca_client.base_url}/orders?status=closed&limit=500"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                orders = response.json()
                filled_orders = [o for o in orders if o.get("status") == "filled" and today.isoformat() in o.get("filled_at", "")]
                
                # Simplified PnL tracking for EOD (since Alpaca orders don't directly show trade PnL, 
                # we count filled buy/sell pairs or rely on account equity delta)
                account_url = f"{alpaca_client.base_url}/account"
                acc_resp = requests.get(account_url, headers=headers)
                
                if acc_resp.status_code == 200:
                    acc_data = acc_resp.json()
                    equity = float(acc_data.get("equity", 0.0))
                    last_equity = float(acc_data.get("last_equity", equity))
                    daily_pnl = equity - last_equity
                    
                    logger.info("=" * 40)
                    logger.info("📈 END OF DAY REPORT")
                    logger.info(f"📅 Date: {today}")
                    logger.info(f"💵 Daily PnL: $")
                    logger.info(f"📝 Total Filled Orders Today: {len(filled_orders)}")
                    logger.info(f"💰 Account Equity: $")
                    logger.info("=" * 40)
                    
                    self.last_eod_report_date = today
            else:
                logger.error(f"❌ [SUPERVISOR EOD] Failed to fetch orders: {response.text}")
        except Exception as e:
            logger.error(f"❌ [SUPERVISOR EOD] Network Error: {e}")

supervisor_agent = SupervisorAgent()
