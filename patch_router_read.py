with open('routers/position_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

fallback_read = """
            except Exception as e:
                import logging
                logging.error(f"Alpaca entegrasyon hatası (Dashboard): {e}. Fallback to Simulation Engine.")
"""

if 'import logging' not in content:
    content = content.replace('except Exception as e:', fallback_read)

with open('routers/position_router.py', 'w', encoding='utf-8') as f:
    f.write(content)
