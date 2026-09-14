import sys
import os
sys.path.append(os.getcwd())
import asyncio
from services.market_feed.live_stream import live_trade_manager

def check_smci():
    for pid, pos in live_trade_manager.positions.items():
        if pos.symbol == 'SMCI':
            print(f"ID: {pid}")
            print(f"Status: {pos.status}")
            print(f"Side: {pos.side}")
            print(f"Entry: {pos.entry_price}")
            print(f"Current: {pos.current_price}")
            print(f"Qty: {pos.quantity}")
            print(f"TP: {pos.target_profit_price}")
            print(f"SL: {pos.stop_loss_price}")
            print(f"Unrealized PnL: {pos.unrealized_pnl}")
            return
            
    print("SMCI not found in active positions.")

if __name__ == '__main__':
    check_smci()
