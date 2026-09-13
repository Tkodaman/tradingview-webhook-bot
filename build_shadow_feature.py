import os

def patch_live_stream():
    path = "services/market_feed/live_stream.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add shadow_positions to __init__
    if "self.shadow_positions: Dict[str, ActivePosition] = {}" not in content:
        content = content.replace(
            "self.positions: Dict[str, ActivePosition] = {}",
            "self.positions: Dict[str, ActivePosition] = {}\n        self.shadow_positions: Dict[str, ActivePosition] = {}"
        )

    # 2. Add open_shadow_position method
    new_method = """
    def open_shadow_position(self, symbol: str, side: str, tp_pct: float, sl_pct: float, entry_price_override: float, reason: str):
        market = market_hours_validator.get_market_type(symbol)
        pos_id = f"SHADOW-{symbol}-{int(time.time())}"
        target_profit_price = round(entry_price_override * (1 + (tp_pct / 100)), 4)
        stop_loss_price = round(entry_price_override * (1 - (sl_pct / 100)), 4)

        pos = ActivePosition(
            id=pos_id,
            symbol=symbol,
            market=market,
            side=side,
            entry_price=entry_price_override,
            current_price=entry_price_override,
            quantity=0,
            nominal_value=0,
            target_profit_price=target_profit_price,
            stop_loss_price=stop_loss_price,
            break_even_trigger_price=0,
            opened_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            status=f"SHADOW_OPEN ({reason})"
        )
        self.shadow_positions[pos_id] = pos
        logger.info(f"[SHADOW TRADE] {symbol} sanal olarak işleme alındı. Neden: {reason}")
        return pos
"""
    if "def open_shadow_position" not in content:
        content = content.replace("def open_position(", new_method + "\n    def open_position(")

    # 3. Add shadow check in update_market_price
    shadow_check = """
        # --- SHADOW POSITION CHECK ---
        for pid, pos in list(self.shadow_positions.items()):
            if "SHADOW_OPEN" not in pos.status:
                continue
            curr = self.market_prices.get(pos.symbol, {}).get("price", pos.entry_price)
            pos.current_price = curr
            pnl_pct = round(((curr - pos.entry_price) / pos.entry_price) * 100.0, 2)
            
            is_closed = False
            is_success = False
            if pnl_pct >= ((pos.target_profit_price - pos.entry_price)/pos.entry_price)*100:
                is_closed = True
                is_success = True
            elif pnl_pct <= ((pos.stop_loss_price - pos.entry_price)/pos.entry_price)*100:
                is_closed = True
                is_success = False
                
            if is_closed:
                pos.status = "SHADOW_CLOSED"
                try:
                    from services.engine.trade_journal_learning import trade_journal_engine
                    opened_dt = datetime.strptime(pos.opened_at, "%Y-%m-%d %H:%M UTC")
                    duration = int((datetime.now(timezone.utc).replace(tzinfo=None) - opened_dt).total_seconds() / 60)
                    trade_journal_engine.evaluate_shadow_trade_autopsy(
                        symbol=pos.symbol, side=pos.side, entry_price=pos.entry_price,
                        exit_price=curr, pnl_pct=pnl_pct, duration_mins=duration, success=is_success
                    )
                except Exception as e:
                    logger.error(f"[SHADOW EVAL ERROR] {e}")
                del self.shadow_positions[pid]
        # -----------------------------
"""
    if "# --- SHADOW POSITION CHECK ---" not in content:
        # inject inside update_market_price loop or end of update_market_price
        content = content.replace("self.save_state()", shadow_check + "\n        self.save_state()", 1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def patch_trade_journal():
    path = "services/engine/trade_journal_learning.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if "self.shadow_journal_entries: List[Dict[str, Any]] = []" not in content:
        content = content.replace("self.journal_entries: List[Dict[str, Any]] = []", "self.journal_entries: List[Dict[str, Any]] = []\n        self.shadow_journal_entries: List[Dict[str, Any]] = []")

    shadow_method = """
    def evaluate_shadow_trade_autopsy(self, symbol: str, side: str, entry_price: float, exit_price: float, pnl_pct: float, duration_mins: int, success: bool):
        from services.intelligence.llm_market_intelligence import LLMMarketIntelligenceEngine
        llm = LLMMarketIntelligenceEngine()
        
        status_text = "BAŞARILI (Kâr Alındı)" if success else "BAŞARISIZ (Stop Oldu)"
        
        prompt = f"Sen profesyonel bir Wall Street Quant analistisin. Botumuz {symbol} için güçlü bir alım sinyali üretti ancak bütçe limiti veya risk blokajı nedeniyle bu varlığı alamadık. Sanal olarak izledik. Giriş: ${entry_price}, Çıkış: ${exit_price}. PnL: %{pnl_pct}. Süre: {duration_mins} dk. Sonuç: {status_text}. Bu işlemin neden böyle sonuçlandığına dair (hacim, sahte kırılım, piyasa trendi) 1-2 cümlelik çok kısa ve net bir makine öğrenimi otopsi çıkarımı yaz."
        
        lesson = llm.generate_insight(prompt)
        if not lesson or "API ERROR" in lesson:
            lesson = f"{symbol} hacim/fiyat dinamikleri {'beklenen ivmeyi koruyarak hedefe ulaştı' if success else 'beklenen ivmeyi kaybederek stop seviyesine geriledi'}."
            
        entry = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl_pct": pnl_pct,
            "duration_mins": duration_mins,
            "success": success,
            "lesson": lesson
        }
        self.shadow_journal_entries.append(entry)
        if len(self.shadow_journal_entries) > 50:
            self.shadow_journal_entries.pop(0)
        logger.info(f"[SHADOW AUTOPSY] {symbol} {status_text} -> {lesson}")
"""
    if "def evaluate_shadow_trade_autopsy" not in content:
        content += "\n" + shadow_method

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def patch_auto_runner():
    path = "services/engine/auto_runner.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Block 1: GLOBAL LIMIT BLOCK
    old_global = """msg = f"[GLOBAL LIMIT BLOCK] {sym} reddedildi. Sistem genelinde maksimum ({total_open_pos}/{global_max_pos}) açık pozisyon limitine ulaşıldı."
                logger.info(msg)
                try:
                    experience_memory_engine.add_live_log(market_type, "BLOCK", msg)
                except Exception:
                    pass
                continue"""
    new_global = """msg = f"[GLOBAL LIMIT BLOCK] {sym} reddedildi. Sistem genelinde maksimum ({total_open_pos}/{global_max_pos}) açık pozisyon limitine ulaşıldı."
                logger.info(msg)
                try:
                    experience_memory_engine.add_live_log(market_type, "BLOCK", msg)
                    live_trade_manager.open_shadow_position(sym, "BUY", base_tp, base_sl, price, "Global Limit")
                except Exception:
                    pass
                continue"""
    content = content.replace(old_global, new_global)

    # Block 2: BUDGET LIMIT BLOCK
    old_budget = """msg = f"[BUDGET LIMIT BLOCK] {sym} reddedildi. {settings.base_portfolio_size}$ bütçe limitine ulaşıldı (Mevcut Yatırım: ${total_invested:.2f})."
                logger.info(msg)
                try:
                    experience_memory_engine.add_live_log(market_type, "BLOCK", msg)
                except Exception:
                    pass
                continue"""
    new_budget = """msg = f"[BUDGET LIMIT BLOCK] {sym} reddedildi. {settings.base_portfolio_size}$ bütçe limitine ulaşıldı (Mevcut Yatırım: ${total_invested:.2f})."
                logger.info(msg)
                try:
                    experience_memory_engine.add_live_log(market_type, "BLOCK", msg)
                    live_trade_manager.open_shadow_position(sym, "BUY", base_tp, base_sl, price, "Budget Limit")
                except Exception:
                    pass
                continue"""
    content = content.replace(old_budget, new_budget)

    # Block 3: MARKET LIMIT BLOCK
    old_market = """logger.info(f"[MARKET LIMIT BLOCK] {sym} ({market_type}) piyasasında max pozisyon sayısına ulaşıldı ({open_pos_in_market}/{max_pos_for_market}).")
                continue"""
    new_market = """logger.info(f"[MARKET LIMIT BLOCK] {sym} ({market_type}) piyasasında max pozisyon sayısına ulaşıldı ({open_pos_in_market}/{max_pos_for_market}).")
                try:
                    live_trade_manager.open_shadow_position(sym, "BUY", base_tp, base_sl, price, "Market Limit")
                except Exception:
                    pass
                continue"""
    content = content.replace(old_market, new_market)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def patch_engine_router():
    path = "routers/engine_router.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    new_endpoint = """
@router.get("/shadow-trades")
def get_shadow_trades():
    from services.engine.trade_journal_learning import trade_journal_engine
    return {"status": "success", "shadow_trades": trade_journal_engine.shadow_journal_entries}
"""
    if "/shadow-trades" not in content:
        content += "\n" + new_endpoint

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def patch_dashboard():
    path = "templates/dashboard.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # UI Injection for Shadow Trades Table
    html_inject = """
            <!-- SHADOW TRADES LEARNING WINDOW -->
            <div class="glass-panel" style="margin-top:24px;">
                <div class="panel-header">
                    <h2><span style="color: #c084fc;">👻</span> Gölge İşlemler (Sanal Olarak İzlenip Kaçan Fırsatlar) & Yapay Zeka Otopsisi</h2>
                </div>
                <div style="overflow-x:auto;">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Tarih</th>
                                <th>Sembol</th>
                                <th>Giriş / Çıkış</th>
                                <th>Süre (Dk)</th>
                                <th>Durum (PnL)</th>
                                <th>🧠 Yapay Zeka Dersi (Ne Olurdu?)</th>
                            </tr>
                        </thead>
                        <tbody id="uiShadowTradesBody">
                            <tr><td colspan="6" style="text-align:center; padding:15px; color:#64748b;">Henüz sonuçlanmış bir gölge işlem yok. Limitlere takılan işlemler arka planda izleniyor.</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
    """
    if "uiShadowTradesBody" not in content:
        # insert before </script> or end of layout
        content = content.replace("<!-- END OF MAIN CONTENT -->", html_inject + "\n        <!-- END OF MAIN CONTENT -->")

    # JS Injection
    js_inject = """
        async function fetchShadowTrades() {
            try {
                const res = await fetch('/api/engine/shadow-trades');
                if (!res.ok) return;
                const data = await res.json();
                const tbody = document.getElementById('uiShadowTradesBody');
                if (tbody && data.shadow_trades && data.shadow_trades.length > 0) {
                    tbody.innerHTML = [...data.shadow_trades].reverse().map(t => {
                        const isWin = t.success;
                        const sign = isWin ? '+' : '';
                        const color = isWin ? 'var(--up-color)' : 'var(--down-color)';
                        const badge = isWin ? '<span class="inner-box-badge badge-reward">BAŞARILI OLURDUK</span>' : '<span class="inner-box-badge badge-block">ZARAR EDERDİK</span>';
                        return `<tr>
                            <td style="color:var(--text-secondary); font-size:11px;">${t.timestamp.split(' ')[1] || t.timestamp}</td>
                            <td style="font-weight:700; color:#fff;">${t.symbol}</td>
                            <td style="color:#94a3b8; font-size:12px;">$${t.entry_price.toFixed(2)} → $${t.exit_price.toFixed(2)}</td>
                            <td>${t.duration_mins}m</td>
                            <td style="color:${color}; font-weight:700;">
                                ${sign}${t.pnl_pct}%<br>
                                ${badge}
                            </td>
                            <td style="color:var(--text-primary); font-size:12px; font-style:italic;">"${t.lesson}"</td>
                        </tr>`;
                    }).join('');
                }
            } catch (err) {}
        }
        setInterval(fetchShadowTrades, 8000);
        fetchShadowTrades();
    """
    if "fetchShadowTrades" not in content:
        content = content.replace("setInterval(fetchPositions, 2000);", "setInterval(fetchPositions, 2000);\n" + js_inject)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    try:
        patch_live_stream()
        print("Patched live_stream.py")
    except Exception as e: print("Error live_stream:", e)
    
    try:
        patch_trade_journal()
        print("Patched trade_journal.py")
    except Exception as e: print("Error trade_journal:", e)
    
    try:
        patch_auto_runner()
        print("Patched auto_runner.py")
    except Exception as e: print("Error auto_runner:", e)
    
    try:
        patch_engine_router()
        print("Patched engine_router.py")
    except Exception as e: print("Error engine_router:", e)

    try:
        patch_dashboard()
        print("Patched dashboard.html")
    except Exception as e: print("Error dashboard.html:", e)

