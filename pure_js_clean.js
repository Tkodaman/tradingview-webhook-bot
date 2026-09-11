
        let pnlChart = null;
        let latestSummaryData = null;
        let currentFilter = 'ALL';
        let prevPriceMap = {};
        let lastAlpacaBalance = 1000.0; // Önceki fiyatları tutarak tick animasyonunu hesaplar

        // TOAST ENGINE
        function showToast(message, type = 'info') {
            const container = document.getElementById('toastContainer');
            if (!container) return;
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            const icon = type === 'success' ? '✅' : (type === 'error' ? '❌' : (type === 'warn' ? '⚠️' : 'ℹ️'));
            toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
            container.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                toast.style.transition = '0.3s';
                setTimeout(() => toast.remove(), 300);
            }, 3500);
        }

        // MODAL HELPERS
        function openModal(id) {
            const m = document.getElementById(id);
            if (m) m.classList.add('active');
        }
        function closeModal(id) {
            const m = document.getElementById(id);
            if (m) m.classList.remove('active');
        }
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                e.target.classList.remove('active');
            }
        });

        // CHART INITIALIZATION
        function initChart() {
            const canvas = document.getElementById('pnlChart');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const gradient = ctx.createLinearGradient(0, 0, 0, 220);
            gradient.addColorStop(0, 'rgba(8, 153, 129, 0.35)');
            gradient.addColorStop(1, 'rgba(8, 153, 129, 0.0)');

            pnlChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Başlangıç'],
                    datasets: [{
                        label: 'Tüm Zamanlar Kümülatif PnL ($)',
                        data: [1000],
                        borderColor: '#089981',
                        borderWidth: 2.5,
                        backgroundColor: gradient,
                        fill: true,
                        tension: 0.35,
                        pointRadius: 3,
                        pointBackgroundColor: '#089981',
                        pointHoverRadius: 6,
                        pointHoverBackgroundColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#1e222d',
                            borderColor: 'rgba(255,255,255,0.1)',
                            borderWidth: 1,
                            titleColor: '#fff',
                            bodyColor: '#d1d4dc',
                            padding: 10,
                            callbacks: {
                                title: (c) => `⏰ Zaman: ${c[0].label}`,
                                label: (c) => ` 💵 Kasa Bakiyesi: $${parseFloat(c.raw).toFixed(2)}`
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(255,255,255,0.04)' },
                            ticks: { 
                                color: '#787b86', 
                                font: { family: 'JetBrains Mono', size: 10 },
                                maxRotation: 45,
                                minRotation: 0,
                                maxTicksLimit: 12
                            }
                        },
                        y: {
                            grid: { color: 'rgba(255,255,255,0.04)' },
                            ticks: {
                                color: '#787b86',
                                font: { family: 'JetBrains Mono', size: 10 },
                                callback: (v) => '$' + v
                            }
                        }
                    }
                }
            });
        }

        function updatePnlChart(history) {
            if (!pnlChart || !history || history.length === 0) return;
            
            const labels = history.map((item, idx) => {
                if (typeof item === 'object' && item.time) return item.time;
                return idx === 0 ? 'Start' : 'Islem #' + idx;
            });
            const data = history.map(item => typeof item === 'object' ? parseFloat(item.value) : parseFloat(item));
            
            // Senkronizasyon: Kümülatif PnL Eğrisinin sonuna CANLI Alpaca Kasasını bağlayalım
            labels.push('Canlı Kasa');
            data.push(lastAlpacaBalance);
            
            pnlChart.data.labels = labels;
            pnlChart.data.datasets[0].data = data;
            
            const lastVal = data[data.length - 1];
            const firstVal = data[0];
            const isProfit = lastVal >= firstVal;
            const lineColor = isProfit ? '#089981' : '#f23645';
            pnlChart.data.datasets[0].borderColor = lineColor;
            pnlChart.data.datasets[0].pointBackgroundColor = lineColor;
            
            // Text güncellemesini fetchPositions da yapıyor ama burada da Alpaca değeriyle eşitleyelim
            const chartEquity = document.getElementById('chartLatestEquity');
            if (chartEquity) {
                chartEquity.innerText = `$${lastAlpacaBalance.toFixed(2)}`;
                chartEquity.style.color = lineColor;
            }
            pnlChart.update();
        }

        // ==========================================
        // FETCH DATA & LIVE STREAM
        // ==========================================

        // 1. FETCH SUMMARY
        async function fetchSummary() {
            try {
                const res = await fetch('/api/experience-memory/summary');
                const json = await res.json();
                if (json.status !== 'success' || !json.data) return;
                
                const data = json.data;
                latestSummaryData = data;

                // Top Header Buttons
                const btnSuccess = document.getElementById('btnCumSuccess');
                if (btnSuccess) {
                    btnSuccess.innerHTML = `<span>📈</span> Kümülatif Başarı: %${data.win_rate_historical.toFixed(1)} (PF: ${data.profit_factor_historical.toFixed(2)})`;
                }

                const btnMult = document.getElementById('btnDynMultiplier');
                if (btnMult) {
                    btnMult.innerHTML = `<span>⚡</span> Dinamik Tecrübe Çarpanı: ${data.dynamic_experience_multiplier.toFixed(2)}x`;
                }

                // Chart Update
                if (data.cumulative_pnl_history) {
                    updatePnlChart(data.cumulative_pnl_history);
                }

                // Render Rules & Summary
                renderRules(data.learned_rules_and_insights);
                renderSummary(data.daily_post_market_synthesis);

                // Render Terminals
                renderTerminals(data.live_action_logs_crypto, data.live_action_logs_bist, data.live_action_logs_nasdaq, data.recent_trades);

            } catch (err) {
                console.error("fetchSummary error:", err);
            }
        }

        // 2. FETCH ACTIVE POSITIONS & WALLET
        async function fetchPositions() {
            try {
                const res = await fetch('/api/positions/active');
                const data = await res.json();
                
                const balEl = document.getElementById('walletBalance');
                const freeCashEl = document.getElementById('freeCash');
                if (balEl && data.account_balance !== undefined) {
                    lastAlpacaBalance = parseFloat(data.account_balance);
                    balEl.innerText = `$${parseFloat(data.account_balance).toFixed(2)}`;
                    const ce = document.getElementById('chartLatestEquity');
                    if (ce) ce.innerText = `$${lastAlpacaBalance.toFixed(2)}`;
                }
                if (freeCashEl && data.available_cash !== undefined) {
                    freeCashEl.innerText = `(Serbest Nakit: $${parseFloat(data.available_cash).toFixed(2)})`;
                }
                const commEl = document.getElementById('alpacaCommission');
                if (commEl && data.total_commissions_paid !== undefined) {
                    commEl.innerText = `(Alpaca Komisyon Gideri: -$${parseFloat(data.total_commissions_paid).toFixed(2)})`;
                }

                const tbody = document.getElementById('positionsTableBody');
                if (!tbody) return;

                const positions = data.active_positions || [];
                window.activeSymbols = new Set(positions.map(p => p.symbol));

                if (positions.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; color:var(--text-secondary); padding: 18px;">Açık pozisyon bulunmuyor. Sistem yeni fırsatları tarıyor.</td></tr>`;
                    return;
                }

                tbody.innerHTML = '';
                positions.forEach(p => {
                    const pnl = parseFloat(p.unrealized_pnl || 0);
                    const pnlPct = parseFloat(p.unrealized_pnl_pct || 0);
                    const isUp = pnl >= 0;
                    const pnlClass = isUp ? 'up' : 'down';
                    const sign = isUp ? '+' : '';

                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>
                            <b style="color:#fff;">${p.symbol}</b> 
                            <div style="font-size:10px; color:var(--text-muted);">${p.id}</div>
                            <div style="font-size:9.5px; color:#94a3b8; margin-top:3px;">
                                <span style="color:#cbd5e1;">Subm/Fill:</span> ${p.opened_at || '-'} &nbsp;|&nbsp; <span style="color:#cbd5e1;">Exp:</span> GTC
                            </div>
                        </td>
                        <td><span style="font-size:11px; padding:2px 6px; border-radius:4px; background:rgba(255,255,255,0.05);">${p.market}</span></td>
                        <td><span style="color:${p.side === 'BUY' ? 'var(--up-color)' : 'var(--down-color)'}; font-weight:700;">${p.side}</span></td>
                        <td>$${parseFloat(p.entry_price).toFixed(2)}</td>
                        <td>$${parseFloat(p.current_price).toFixed(2)}</td>
                        <td>${parseFloat(p.quantity).toFixed(4)} ($${parseFloat(p.nominal_value).toFixed(2)})</td>
                        <td style="color:var(--up-color);">$${parseFloat(p.target_profit_price).toFixed(2)}</td>
                        <td style="color:var(--down-color);">$${parseFloat(p.stop_loss_price).toFixed(2)}</td>
                        <td class="${pnlClass}" style="font-weight:700;">
                            ${sign}$${pnl.toFixed(2)} (${sign}%${pnlPct.toFixed(2)})<br>
                            <span style="font-size:9px; color:#64748b; font-weight:normal;">(Kom. Düşüldü)</span>
                        </td>
                        <td>
                            <button class="btn btn-close" style="padding:3px 8px; font-size:11px;" onclick="quickClosePosition('${p.id}')">Kapat</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch (err) {
                console.error("fetchPositions error:", err);
            }
        }

        // 3. FETCH LIVE MATRIX & 3-MARKET SEPARATED WINDOWS
        async function fetchLiveMatrix() {
            try {
                const res = await fetch('/api/market/live-matrix');
                const data = await res.json();
                if (!data || !data.grouped) return;

                // Market Overviews & Badges
                const ov = data.markets_overview || {};
                
                // CRYPTO STATUS
                const cryptoInfo = ov.CRYPTO || { is_open: true, status_badge: '🟢 7/24 PİYASA AÇIK' };
                const badgeCrypto = document.getElementById('badgeCryptoStatus');
                if (badgeCrypto) {
                    badgeCrypto.className = `window-status-badge ${cryptoInfo.is_open ? 'status-open' : 'status-closed'}`;
                    badgeCrypto.innerHTML = `<span class="live-dot"></span> ${cryptoInfo.status_badge}`;
                }

                // BIST STATUS
                const bistInfo = ov.BIST || { is_open: false, status_badge: '🔴 PİYASA KAPALI' };
                const badgeBist = document.getElementById('badgeBistStatus');
                const bannerBistNotice = document.getElementById('bannerBistNotice');
                const textBistNotice = document.getElementById('textBistNotice');
                if (badgeBist) {
                    badgeBist.className = `window-status-badge ${bistInfo.is_open ? 'status-open' : 'status-closed'}`;
                    badgeBist.innerHTML = bistInfo.is_open ? `<span class="live-dot"></span> ${bistInfo.status_badge}` : bistInfo.status_badge;
                }
                if (bannerBistNotice && textBistNotice) {
                    if (bistInfo.is_open) {
                        bannerBistNotice.className = 'market-notice-banner banner-open';
                        textBistNotice.innerHTML = `<b>🟢 BIST Seansı Açık:</b> Borsa İstanbul canlı emir akışı ve fiyat hareketleri anlık olarak işlenmektedir.`;
                    } else {
                        bannerBistNotice.className = 'market-notice-banner banner-closed';
                        textBistNotice.innerHTML = `<b>🔴 Seans Dışı (Kapalı):</b> Borsa İstanbul seans saatleri Hafta İçi 10:00 - 18:05 TSİ arasındadır. Varlıklar soluk renkte dünkü kapanış değerleriyle sergilenir.`;
                    }
                }

                // NASDAQ STATUS
                const nasdaqInfo = ov.NASDAQ || { is_open: false, status_badge: '🔴 PİYASA KAPALI' };
                const badgeNasdaq = document.getElementById('badgeNasdaqStatus');
                const bannerNasdaqNotice = document.getElementById('bannerNasdaqNotice');
                const textNasdaqNotice = document.getElementById('textNasdaqNotice');
                if (badgeNasdaq) {
                    badgeNasdaq.className = `window-status-badge ${nasdaqInfo.is_open ? 'status-open' : 'status-closed'}`;
                    badgeNasdaq.innerHTML = nasdaqInfo.is_open ? `<span class="live-dot"></span> ${nasdaqInfo.status_badge}` : nasdaqInfo.status_badge;
                }
                if (bannerNasdaqNotice && textNasdaqNotice) {
                    if (nasdaqInfo.is_open) {
                        bannerNasdaqNotice.className = 'market-notice-banner banner-open';
                        textNasdaqNotice.innerHTML = `<b>🟢 NASDAQ Seansı Açık:</b> Wall Street düzenli seansı aktiftir. Tüm mega-cap hisseler canlı dalgalanmaktadır.`;
                    } else {
                        bannerNasdaqNotice.className = 'market-notice-banner banner-closed';
                        textNasdaqNotice.innerHTML = `<b>🔴 Seans Dışı (Kapalı):</b> NASDAQ seans saatleri Hafta İçi 16:30 - 23:00 TSİ arasındadır. Varlıklar soluk renkte son kapanış değerleriyle sergilenir.`;
                    }
                }

                // RENDER EACH GRID SEPARATELY
                renderMarketGroup('gridCrypto', data.grouped.CRYPTO || [], cryptoInfo.is_open, 'cryptoStatsCount');
                renderMarketGroup('gridBist', data.grouped.BIST || [], bistInfo.is_open, 'bistStatsCount');
                renderMarketGroup('gridNasdaq', data.grouped.NASDAQ || [], nasdaqInfo.is_open, 'nasdaqStatsCount');

            } catch (err) {
                console.error("fetchLiveMatrix error:", err);
            }
        }

        // RENDER SPECIFIC MARKET GROUP
        function renderMarketGroup(gridId, items, isOpen, countBadgeId) {
            const grid = document.getElementById(gridId);
            if (!grid) return;

            const countBadge = document.getElementById(countBadgeId);
            if (countBadge) countBadge.innerText = `${items.length} Varlık`;

            // Sort to prioritize active positions (has_active_position = true at the top)
            items.sort((a, b) => {
                const aActive = !!a.has_active_position;
                const bActive = !!b.has_active_position;
                if (aActive && !bActive) return -1;
                if (!aActive && bActive) return 1;
                return 0; // retain original order otherwise
            });

            // Mevcut kart elementlerini koruyup sadece değerleri güncelle (titreme/re-render önleme)
            items.forEach(item => {
                const cardId = `card_${item.symbol}`;
                let card = document.getElementById(cardId);
                const prevPrice = prevPriceMap[item.symbol] !== undefined ? prevPriceMap[item.symbol] : item.price;
                const isPriceUp = item.price > prevPrice;
                const isPriceDown = item.price < prevPrice;
                prevPriceMap[item.symbol] = item.price;

                const chg = parseFloat(item.change_pct || 0);
                const isChgUp = chg >= 0;
                const chgClass = isChgUp ? 'up' : 'down';
                const sign = isChgUp ? '+' : '';

                // Piyasa kapalıysa kart soluk sınıfı eklenir
                const closedClass = !isOpen ? 'market-closed' : '';
                const activeClass = item.has_active_position ? 'active-position-card' : '';

                const formattedPrice = item.price < 1.0 ? parseFloat(item.price).toFixed(4) : parseFloat(item.price).toFixed(2);
                const formattedLow = item.low < 1.0 ? parseFloat(item.low).toFixed(4) : parseFloat(item.low).toFixed(2);
                const formattedHigh = item.high < 1.0 ? parseFloat(item.high).toFixed(4) : parseFloat(item.high).toFixed(2);

                if (!card) {
                    card = document.createElement('div');
                    card.id = cardId;
                    card.className = `ticker-card ${closedClass} ${activeClass}`;
                    card.onclick = () => {
                        document.getElementById('newPosSymbol').value = item.symbol;
                        openNewPositionModal();
                        showToast(`${item.symbol} seçildi. Hızlı emir penceresi açıldı.`, 'info');
                    };
                } else {
                    // Sınıfı güncelle (kapalıysa soluk, aktif işlemse özel arka plan)
                    card.className = `ticker-card ${closedClass} ${activeClass}`;
                }
                
                // Her halükarda DOM'a sıralı ekle (appendChild mevcut node'u sadece taşır)
                grid.appendChild(card);

                // Tick Pulse Animasyonu (Fiyat Değiştiğinde)
                let tickClass = '';
                if (isOpen) {
                    if (isPriceUp) tickClass = 'price-tick-up';
                    else if (isPriceDown) tickClass = 'price-tick-down';
                }

                const closedBadgeHtml = !isOpen ? `<span class="badge-closed-tag">KAPALI</span>` : '';

                card.innerHTML = `
                    <div class="ticker-top">
                        <span class="ticker-symbol">${item.symbol}</span>
                        <div style="display:flex; gap:4px; align-items:center;">
                            ${closedBadgeHtml}
                            <span class="ticker-change ${chgClass}">${sign}%${Math.abs(chg).toFixed(2)}</span>
                        </div>
                    </div>
                    <div class="ticker-price ${tickClass}" id="price_${item.symbol}">$${formattedPrice}</div>
                    <div class="ticker-bottom">
                        <span>D: ${formattedLow}</span>
                        <span>Y: ${formattedHigh}</span>
                    </div>
                `;
            });
        }

        // MARKET VIEW TAB FILTER
        function filterMarketView(market) {
            currentFilter = market;
            
            // Tab buton aktifliği
            document.getElementById('tabAll').className = 'tab-btn' + (market === 'ALL' ? ' active' : '');
            document.getElementById('tabCrypto').className = 'tab-btn' + (market === 'CRYPTO' ? ' active' : '');
            document.getElementById('tabBist').className = 'tab-btn' + (market === 'BIST' ? ' active' : '');
            document.getElementById('tabNasdaq').className = 'tab-btn' + (market === 'NASDAQ' ? ' active' : '');

            // Pencerelerin görünürlüğü
            const winCrypto = document.getElementById('windowCrypto');
            const winBist = document.getElementById('windowBist');
            const winNasdaq = document.getElementById('windowNasdaq');

            if (market === 'ALL') {
                if (winCrypto) winCrypto.style.display = 'block';
                if (winBist) winBist.style.display = 'block';
                if (winNasdaq) winNasdaq.style.display = 'block';
            } else if (market === 'CRYPTO') {
                if (winCrypto) winCrypto.style.display = 'block';
                if (winBist) winBist.style.display = 'none';
                if (winNasdaq) winNasdaq.style.display = 'none';
            } else if (market === 'BIST') {
                if (winCrypto) winCrypto.style.display = 'none';
                if (winBist) winBist.style.display = 'block';
                if (winNasdaq) winNasdaq.style.display = 'none';
            } else if (market === 'NASDAQ') {
                if (winCrypto) winCrypto.style.display = 'none';
                if (winBist) winBist.style.display = 'none';
                if (winNasdaq) winNasdaq.style.display = 'block';
            }
        }

        // ==========================================
        // RULES, SUMMARY & TERMINALS RENDERING
        // ==========================================
        function renderRules(rules) {
            const container = document.getElementById('rulesContainer');
            const badge = document.getElementById('rulesCountBadge');
            if (!container) return;

            if (!rules || rules.length === 0) {
                container.innerHTML = '<div style="color: var(--text-secondary); text-align:center; padding: 20px;">Henüz aktif kural bulunmuyor.</div>';
                if (badge) badge.innerText = '0 Kural';
                return;
            }

            if (badge) badge.innerText = `${rules.length} Kural Aktif`;
            container.innerHTML = '';

            rules.forEach(r => {
                const badgeClass = r.type === 'REWARD' ? 'badge-reward' : (r.type === 'CAUTION' ? 'badge-caution' : 'badge-block');
                const borderColor = r.type === 'REWARD' ? 'var(--up-color)' : (r.type === 'CAUTION' ? 'var(--accent-yellow)' : 'var(--down-color)');
                
                const div = document.createElement('div');
                div.className = 'inner-box';
                div.style.borderLeft = `3px solid ${borderColor}`;
                div.onclick = () => showToast(`${r.category}: ${r.action_taken}`, 'info');
                div.innerHTML = `
                    <div class="inner-box-title">
                        <span>
                            ${r.category || 'Algoritmik Kural'} 
                            <span style="font-size:10px; color:var(--text-secondary); font-family:'JetBrains Mono';">[${r.cluster_key}]</span>
                            <span style="font-size:10px; color:#94a3b8; font-family:'JetBrains Mono'; margin-left: 6px;">
                                🕒 ${r.timestamp || r.created_at || new Date().toLocaleString('tr-TR', {timeZone: 'Europe/Istanbul', hour12: false}).replace(',', '')}
                            </span>
                        </span>
                        <span class="inner-box-badge ${badgeClass}">${r.impact_status || r.type}</span>
                    </div>
                    <div class="inner-box-item">
                        <span>💡</span> 
                        <div><span style="color:#fff;">Çıkarım:</span> ${r.insight}</div>
                    </div>
                    <div class="inner-box-item">
                        <span>⚡</span> 
                        <div><span style="color:#fff;">Uygulanan Eylem:</span> ${r.action_taken}</div>
                    </div>
                `;
                container.appendChild(div);
            });
        }

        function renderSummary(synthesis) {
            const container = document.getElementById('summaryContainer');
            if (!container || !synthesis) return;

            const dateLbl = document.getElementById('summaryDateLabel');
            if (dateLbl && synthesis.session_date) dateLbl.innerText = synthesis.session_date;

            container.innerHTML = `
                <div class="inner-box" style="border-left: 3px solid var(--accent-blue);">
                    <div class="inner-box-title">🎯 Yarının Strateji Eğilimi: <span style="color:#93c5fd;">${synthesis.tomorrow_strategy_bias || 'NÖTR'}</span></div>
                    <p style="color:var(--text-secondary); font-size:12px; margin-top:4px;">${synthesis.executive_takeaway || 'Veri sentezleniyor.'}</p>
                </div>
                <div class="inner-box" style="border-left: 3px solid var(--accent-yellow);">
                    <div class="inner-box-title">🏆 Günün En İyi Kurulumu:</div>
                    <div style="font-size:12px; color:#fff; font-weight:600;">${synthesis.top_performing_setup || '-'}</div>
                    <div class="inner-box-item"><span>⚠️</span> <div><span style="color:#fff;">Kritik Hata/Risk:</span> ${synthesis.worst_mistake_detected || 'Tespit edilen hata yok.'}</div></div>
                </div>
            `;
        }

        function renderLogsToTerminal(containerId, logs) {
            const container = document.getElementById(containerId);
            if (!container) return;
            if (!logs || logs.length === 0) {
                container.innerHTML = '<div style="color:var(--text-secondary); text-align:center; padding:10px;">Bekleniyor...</div>';
                return;
            }
            
            container.innerHTML = logs.map(log => {
                let lvlColor = '#fff';
                if (log.level === 'ORDER') lvlColor = 'var(--up-color)';
                else if (log.level === 'WIN') lvlColor = '#22d3ee';
                else if (log.level === 'SCAN') lvlColor = '#c084fc';
                else if (log.level === 'STATUS' || log.level === 'WARN') lvlColor = 'var(--accent-yellow)';
                else if (log.level === 'UPDATE' || log.level === 'INFO') lvlColor = '#94a3b8';
                
                return `<div style="margin-bottom: 4px; line-height: 1.4;">
                    <span style="color: #64748b;">[${log.time}]</span> 
                    <span style="color: ${lvlColor}; font-weight: 700; min-width: 65px; display: inline-block;">[${log.level}]</span> 
                    <span style="color: #cbd5e1;">${log.message}</span>
                </div>`;
            }).join('');
            
            container.scrollTop = container.scrollHeight;
        }

        function renderTerminals(cryptoLogs, bistLogs, nasdaqLogs, recentTrades) {
            renderLogsToTerminal('cryptoTerminal', cryptoLogs);
            renderLogsToTerminal('bistTerminal', bistLogs);
            renderLogsToTerminal('nasdaqTerminal', nasdaqLogs);
            
            const tbody = document.getElementById('autotraderExecutionLog');
            if (tbody && recentTrades) {
                tbody.innerHTML = recentTrades.map(t => {
                    const isWin = t.is_win;
                    const sign = isWin ? '+' : '';
                    const color = isWin ? 'var(--up-color)' : 'var(--down-color)';
                    const badge = isWin ? '<span class="inner-box-badge badge-reward">BAŞARILI</span>' : '<span class="inner-box-badge badge-block">ZARAR</span>';
                    
                    return `<tr>
                        <td style="color:var(--text-secondary); font-family:'JetBrains Mono';">${t.timestamp.split(' ')[1]}</td>
                        <td style="font-weight:700; color:#fff;">${t.symbol}</td>
                        <td><span style="color:${t.action==='BUY'?'var(--up-color)':'var(--down-color)'}; font-weight:700;">${t.action}</span></td>
                        <td>${t.duration_minutes}m</td>
                        <td>${t.max_drawdown_percent}%</td>
                        <td>${t.exit_reason}</td>
                        <td style="color:${color}; font-weight:700;">
                            ${sign}${t.pnl_pct}%<br>
                            <span style="font-size:9px; color:#64748b; font-weight:normal;">(Alpaca Kom. Düşüldü)</span>
                        </td>
                        <td>${badge} <span style="color:var(--text-primary); font-size:11px;">${t.lesson_learned}</span></td>
                    </tr>`;
                }).join('');
            }
        }

        // ==========================================
        // USER INTERACTIVE BUTTON ACTIONS
        // ==========================================

        // KASAYI $1,000'A SIFIRLA
        window.resetAccountWallet = async function() {
            if (!confirm("Kasayı kesin olarak $1,000.00 taban sermayesine sıfırlamak ve tüm eski işlem kalıntılarını temizlemek istiyor musunuz?")) {
                return;
            }
            try {
                const res = await fetch('/api/account/reset', { method: 'POST' });
                const json = await res.json();
                if (res.ok && json.status === 'success') {
                    showToast('✅ Kasa bakiyesi kesin olarak $1,000.00 tabanına sıfırlandı!', 'success');
                    fetchPositions();
                    fetchSummary();
                } else {
                    showToast('Sıfırlama işlemi başarısız oldu.', 'error');
                }
            } catch (err) {
                showToast('Hata: Sunucuya bağlanılamadı.', 'error');
            }
        };

        // GÜNLÜK RAPOR MODAL
        window.openDailyReportModal = async function() {
            const content = document.getElementById('dailyReportContent');
            openModal('dailyReportModal');
            
            if (!latestSummaryData) {
                try {
                    const res = await fetch('/api/experience-memory/summary');
                    const json = await res.json();
                    if (json.data) latestSummaryData = json.data;
                } catch (e) {}
            }

            if (!latestSummaryData) {
                content.innerText = 'Rapor verisi yükleniyor, lütfen birkaç saniye sonra tekrar deneyin.';
                return;
            }

            const syn = latestSummaryData.daily_post_market_synthesis || {};
            const snapshots = latestSummaryData.hourly_experience_snapshots || [];
            
            let snapsHtml = snapshots.map(s => `
                <div style="display:flex; justify-content:space-between; align-items:center; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <span style="font-weight:600; color:#fff;">${s.hour_label}</span>
                    <span style="color:var(--up-color); font-family:'JetBrains Mono'; font-weight:700;">${s.hourly_pnl}</span>
                    <span style="color:var(--text-secondary); font-size:12px; max-width:60%;">${s.summary}</span>
                </div>
            `).join('');

            content.innerHTML = `
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="stat-label">Tarih</div>
                        <div class="stat-value" style="font-size:14px;">${syn.session_date || 'Bugün'}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Toplam Net Kâr</div>
                        <div class="stat-value up">+$${latestSummaryData.net_pnl_historical ? latestSummaryData.net_pnl_historical.toFixed(2) : '0.00'}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Başarı</div>
                        <div class="stat-value up">%${latestSummaryData.win_rate_historical ? latestSummaryData.win_rate_historical.toFixed(1) : '0.0'}</div>
                    </div>
                </div>
                <div style="margin-top: 14px; background: rgba(42,46,57,0.4); padding: 12px; border-radius: 6px; border: 1px solid var(--border-color); margin-bottom: 14px;">
                    <div style="font-weight: 700; color:#fff; margin-bottom: 4px;">🎯 Strateji Eğilimi:</div>
                    <p style="color:#d1d4dc;">${syn.tomorrow_strategy_bias || 'NÖTR'}</p>
                    <p style="color:var(--text-secondary); font-size: 12px; margin-top: 6px;">${syn.executive_takeaway || ''}</p>
                </div>
                <div style="font-weight:700; color:#fff; margin-bottom: 8px;">⏱️ Saatlik Deneyim Dökümü:</div>
                <div style="background:#0f121a; border-radius:6px; padding:10px; border:1px solid var(--border-color);">
                    ${snapsHtml || '<p style="color:#787b86;">Saatlik veri bulunmuyor.</p>'}
                </div>
            `;
        };

        // CSV EXPORT
        window.exportCsvData = function() {
            window.location.href = '/api/experience-memory/export/csv';
            showToast('📥 CSV tarihsel verisi indiriliyor...', 'info');
        };

        // JSON MODAL
        window.openJsonModal = async function() {
            const pre = document.getElementById('jsonCodeContent');
            pre.innerText = 'Rapor hazırlanıyor...';
            openModal('jsonModal');
            try {
                const res = await fetch('/api/experience-memory/summary');
                const json = await res.json();
                pre.innerText = JSON.stringify(json, null, 2);
            } catch (err) {
                pre.innerText = 'JSON raporu alınırken hata oluştu.';
            }
        };

        window.copyJsonToClipboard = function() {
            const pre = document.getElementById('jsonCodeContent');
            navigator.clipboard.writeText(pre.innerText).then(() => {
                showToast('📋 JSON raporu panoya kopyalandı!', 'success');
            });
        };

        window.downloadJsonFile = function() {
            const pre = document.getElementById('jsonCodeContent');
            const blob = new Blob([pre.innerText], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `experience_memory_${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
            showToast('📥 JSON dosyası indirildi.', 'info');
        };

        // PERFORMANCE MODAL
        window.openPerformanceModal = function() {
            if (!latestSummaryData) {
                showToast('Veriler yükleniyor, lütfen bekleyin...', 'info');
                return;
            }
            document.getElementById('modalStatTotalTrades').innerText = latestSummaryData.total_trades_analyzed || 0;
            document.getElementById('modalStatWinRate').innerText = `%${(latestSummaryData.win_rate_historical || 0).toFixed(1)}`;
            document.getElementById('modalStatPF').innerText = (latestSummaryData.profit_factor_historical || 0).toFixed(2);
            const pnl = latestSummaryData.net_pnl_historical || 0;
            document.getElementById('modalStatNetPnl').innerText = `${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}`;
            document.getElementById('modalStatNetPnl').className = `stat-value ${pnl >= 0 ? 'up' : 'down'}`;
            
            document.getElementById('modalStatAiInsight').innerText = 
                `Algoritmik hafıza motoru toplam ${latestSummaryData.total_trades_analyzed} işlemi analiz etmiş ve %${latestSummaryData.win_rate_historical} kazanma oranı ile ${latestSummaryData.profit_factor_historical} kâr faktörüne ulaşmıştır. Sistem dinamik çarpanı (${latestSummaryData.dynamic_experience_multiplier}x) ile pozisyonları optimize etmektedir.`;

            openModal('perfModal');
        };

        // MULTIPLIER MODAL
        window.openMultiplierModal = function() {
            if (!latestSummaryData) return;
            document.getElementById('modalMultValue').innerText = `${(latestSummaryData.dynamic_experience_multiplier || 1.2).toFixed(2)}x`;
            openModal('multiplierModal');
        };

        // SIMULATE TRADE MODAL
        window.openSimulateTradeModal = function() {
            openModal('simModal');
        };

        window.submitSimulateTrade = async function() {
            const symbol = document.getElementById('simSymbol').value.toUpperCase();
            const regime = document.getElementById('simRegime').value;
            const pnl = parseFloat(document.getElementById('simPnl').value);
            const exitReason = document.getElementById('simExitReason').value;

            try {
                const res = await fetch('/api/experience-memory/simulate-trade', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ symbol, regime, pnl, exit_reason: exitReason })
                });
                const json = await res.json();
                if (res.ok) {
                    showToast(`Simülasyon başarılı: Kasa ${pnl >= 0 ? '+' : ''}$${pnl} değişti.`, 'success');
                    closeModal('simModal');
                    fetchSummary();
                } else {
                    showToast('Simülasyon başarısız oldu.', 'error');
                }
            } catch (err) {
                showToast('Hata: Sunucuya bağlanılamadı.', 'error');
            }
        };

        // CALIBRATE ENGINE
        window.calibrateEngine = async function() {
            try {
                const res = await fetch('/api/experience-memory/calibrate', { method: 'POST' });
                const json = await res.json();
                if (res.ok) {
                    showToast('🎯 Motor başarıyla kalibre edildi!', 'success');
                    fetchSummary();
                } else {
                    showToast('Kalibrasyon başarısız.', 'error');
                }
            } catch (err) {
                showToast('Hata: Kalibre edilemedi.', 'error');
            }
        };

        // QUICK POSITION OPEN MODAL
        window.openNewPositionModal = function() {
            openModal('newPosModal');
        };

        window.submitOpenPosition = async function() {
            const symbol = document.getElementById('newPosSymbol').value.toUpperCase();
            const side = document.getElementById('newPosSide').value;
            const capital = parseFloat(document.getElementById('newPosCapital').value);
            const tp_pct = parseFloat(document.getElementById('newPosTp').value);
            const sl_pct = parseFloat(document.getElementById('newPosSl').value);

            try {
                const res = await fetch('/api/positions/open', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ symbol, side, capital, tp_pct, sl_pct })
                });
                const json = await res.json();
                if (res.ok) {
                    showToast(`🚀 ${symbol} için $${capital} tutarında ${side} pozisyonu açıldı!`, 'success');
                    closeModal('newPosModal');
                    fetchPositions();
                    fetchSummary();
                } else {
                    showToast(`Pozisyon açılamadı: ${json.detail || 'Limit yetersiz'}`, 'error');
                }
            } catch (err) {
                showToast('Hata: Pozisyon emri iletilemedi.', 'error');
            }
        };

        window.quickClosePosition = async function(posId) {
            if (!confirm(`${posId} nolu pozisyonu piyasa fiyatından kapatmak istiyor musunuz?`)) return;
            try {
                const res = await fetch(`/api/positions/close/${posId}`, { method: 'POST' });
                const json = await res.json();
                if (res.ok) {
                    showToast(`✅ ${posId} başarıyla kapatıldı!`, 'success');
                    fetchPositions();
                    fetchSummary();
                } else {
                    showToast('Pozisyon kapatılamadı.', 'error');
                }
            } catch (err) {
                showToast('Hata: Pozisyon kapatılamadı.', 'error');
            }
        };

        // REFRESH ALL
        window.refreshData = function(isManual = false) {
            fetchSummary();
            fetchPositions();
            fetchAlgorithmicStats();
            if (isManual) {
                showToast('Tüm canlı piyasa ve bakiye akışları yenilendi.', 'success');
            }
        };

        // RESET WALLET
        window.resetAccountWallet = async function() {
            if(!confirm("Kasa bakiyesi ve trade geçmişi 1000$ olarak sıfırlanacaktır. Onaylıyor musunuz?")) return;
            try {
                const res = await fetch('/api/account/reset', { method: 'POST' });
                if(res.ok) {
                    showToast('Kasa bakiyesi 1000$ olarak sıfırlandı.', 'success');
                    refreshData(true);
                } else {
                    showToast('Sıfırlama işlemi başarısız oldu.', 'error');
                }
            } catch (err) {
                showToast('Hata: Sıfırlama servisine ulaşılamadı.', 'error');
            }
        };

        // INITIALIZATION
        initChart();
        refreshData();

        // WEBSOCKET BAĞLANTISI (ANLIK VERİ AKIŞI)
        function connectWebSocket() {
            const wsUrl = `ws://${window.location.host}/ws/live`;
            const ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                console.log("WebSocket Bağlantısı Kuruldu");
                document.querySelector('.live-dot').style.backgroundColor = 'var(--up-color)';
                showToast('WebSocket ile Canlı Veri Akışına Geçildi', 'info');
            };

            ws.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg.type === 'LIVE_MARKET') {
                        const prices = msg.data.live_prices;
                        const summary = msg.data.summary;
                        
                        // Kasa ve Bakiye Güncellemesi
                        const balEl = document.getElementById('walletBalance');
                        const freeCashEl = document.getElementById('freeCash');
                        const commEl = document.getElementById('alpacaCommission');
                        
                        if (balEl && summary.account_balance !== undefined) {
                            balEl.innerText = `$${parseFloat(summary.account_balance).toFixed(2)}`;
                        }
                        if (freeCashEl && summary.available_cash !== undefined) {
                            freeCashEl.innerText = `(Serbest Nakit: $${parseFloat(summary.available_cash).toFixed(2)})`;
                        }
                        if (commEl && summary.total_commissions_paid !== undefined) {
                            commEl.innerText = `(Alpaca Komisyon Gideri: -$${parseFloat(summary.total_commissions_paid).toFixed(2)})`;
                        }

                        // Chart Güncellemesi
                        const chartEquity = document.getElementById('chartLatestEquity');
                        if (chartEquity && summary.account_balance !== undefined) {
                            chartEquity.innerText = `$${parseFloat(summary.account_balance).toFixed(2)}`;
                            updateChartData(summary.account_balance);
                        }

                        // Market Ticks (Piyasa Fiyatları)
                        if (prices && prices.market_ticks) {
                            const marketTicks = prices.market_ticks;
                            
                            const cryptoData = [];
                            const bistData = [];
                            const nasdaqData = [];
                            
                            Object.values(marketTicks).forEach(t => {
                                if (t.market === 'CRYPTO') cryptoData.push(t);
                                else if (t.market === 'BIST') bistData.push(t);
                                else if (t.market === 'NASDAQ') nasdaqData.push(t);
                            });
                            
                            renderMarketGroup('gridCrypto', cryptoData, true, 'cryptoStatsCount');
                            renderMarketGroup('gridBist', bistData, true, 'bistStatsCount');
                            renderMarketGroup('gridNasdaq', nasdaqData, true, 'nasdaqStatsCount');
                        }
                    }
                } catch (e) {
                    console.error("WebSocket Message Error:", e);
                }
            };

            ws.onclose = () => {
                console.log("WebSocket Bağlantısı Koptu, Yeniden Bağlanılıyor...");
                document.querySelector('.live-dot').style.backgroundColor = 'var(--down-color)';
                setTimeout(connectWebSocket, 3000);
            };
        }

        // Başlat
        connectWebSocket();
        fetchLiveMatrix(); // Varlık matrix verisini ilk girişte çek

        // 6 SANİYEDE BİR SADECE GENEL ÖZET & STATS GÜNCELLEMESİ (Hafif İşlemler)
        setInterval(() => {
            fetchSummary();
            fetchAlgorithmicStats();
            fetchPositions(); // Websocket üzerinden gelse de listeyi API'den senkronize edebiliriz
            fetchLiveMatrix(); // Canlı matris verisini periyodik olarak güncelle
        }, 6000);

        async function fetchAlgorithmicStats() {
            try {
                const res = await fetch('/api/experience-memory/algorithmic-stats');
                if (!res.ok) return;
                const data = await res.json();
                if (data.status === 'success' && data.data) {
                    const stats = data.data;
                    document.getElementById('uiGlobalErrorMargin').innerText = `%${stats.global_error_margin.toFixed(2)}`;
                    
                    // Error Margin Bars
                    const barsContainer = document.getElementById('uiErrorCurveBars');
                    if (barsContainer) {
                        barsContainer.innerHTML = '';
                        stats.history_points.forEach(pt => {
                            const h = Math.min(100, pt.error_margin);
                            const color = h > 50 ? 'var(--down-color)' : (h > 20 ? 'var(--accent-yellow)' : 'var(--up-color)');
                            barsContainer.innerHTML += `
                                <div style="width:12px; height:${h}%; background:${color}; border-radius:2px; flex-shrink:0;" title="${pt.symbol}: Hata %${pt.error_margin}"></div>
                            `;
                        });
                    }
                    
                    // Action Plans Table
                    const tbody = document.getElementById('uiActionPlansBody');
                    if (tbody) {
                        if (stats.action_plans.length === 0) {
                            tbody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding:10px; color:#64748b;">Henüz hata / eylem planı oluşmadı.</td></tr>';
                        } else {
                            tbody.innerHTML = stats.action_plans.map(p => `
                                <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                                    <td style="padding:6px 0; color:var(--text-secondary);">${p.date.split(' ')[1] || p.date}</td>
                                    <td style="padding:6px 0; color:#fff; font-weight:600;">${p.symbol}</td>
                                    <td style="padding:6px 0; color:#cbd5e1; font-family:'JetBrains Mono', monospace; font-size:11px;">${p.plan}</td>
                                </tr>
                            `).join('');
                        }
                    }
                }
            } catch (err) {
                console.log('Algorithmic stats fetch error:', err);
            }
        }

        // Call initially
        // checkLiveStatus();
        fetchPositions();
        
        async function setRiskMode(mode) {
            try {
                const response = await fetch('/api/engine/risk-mode', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode: mode })
                });
                const data = await response.json();
                
                if(data.status === 'success') {
                    // Butonları güncelle
                    document.querySelectorAll('.risk-btn').forEach(btn => btn.classList.remove('active'));
                    const activeBtn = document.getElementById('risk-btn-' + mode);
                    if(activeBtn) activeBtn.classList.add('active');
                    
                    showToast('success', 'Risk Modu Güncellendi', data.message);
                } else {
                    showToast('error', 'Hata', data.message);
                }
            } catch (error) {
                showToast('error', 'Bağlantı Hatası', 'Risk modu değiştirilemedi.');
            }
        }
        
        // Ensure the correct mode button is selected based on page load data if possible.
        // For now, it defaults to NORMAL visually until manually clicked, or we could fetch status.
    