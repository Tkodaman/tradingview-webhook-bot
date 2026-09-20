from core.config import Settings


def test_conservative_mode_has_stricter_hard_ceiling():
    settings = Settings(passphrase="test")
    settings.apply_risk_mode("NORMAL")
    normal_limit = settings.max_risk_score_allowed

    settings.apply_risk_mode("CONSERVATIVE")

    assert settings.max_risk_score_allowed < normal_limit
    assert settings.max_capital_per_trade_pct < 10.0