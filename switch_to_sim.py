with open('.env', 'r', encoding='utf-8') as f:
    env_content = f.read()
env_content = env_content.replace('TRADING_MODE=PAPER', 'TRADING_MODE=SIMULATION')
with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content)
