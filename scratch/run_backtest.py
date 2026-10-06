import sys
import os
sys.path.append(os.path.abspath("."))
from services.trainer.bot_trainer import BotTrainer

trainer = BotTrainer()
print("Running ML Backtest and Walk-Forward Validation...")
result = trainer.train_bot(iterations=1000)
print(result)
