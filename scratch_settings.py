from core.config import settings
print("Mode:", settings.trading_mode)
print("Autonomous Enabled:", getattr(settings, 'is_autonomous_enabled', 'N/A'))
