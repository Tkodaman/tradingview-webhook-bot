import os
import sys
sys.path.append(os.path.abspath('.'))
from core.database import DatabaseManager

db_manager = DatabaseManager()
db_manager.set_store("wallet_state", {"positions": {}})
print("wallet_state positions cleared!")
