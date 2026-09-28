/**
 * TradeX Cwallet Auto-Sync Bookmarklet Client (static/cwallet_sync.js)
 * High-precision bidirectional clock, phase, and strike price synchronization client for Cwallet Market Battle.
 *
 * Usage: Copy into browser console or bookmarklet on Cwallet Market Battle tab.
 */
(function() {
    if (window._cwSyncActive) {
        alert('🟢 CW Auto-Sync is already active and streaming!');
        return;
    }
    window._cwSyncActive = true;

    // Create live HUD floating badge
    var hud = document.getElementById('cw-bot-hud');
    if (!hud) {
        hud = document.createElement('div');
        hud.id = 'cw-bot-hud';
        hud.style.cssText = 'position:fixed;bottom:16px;right:16px;background:rgba(15,23,42,0.95);border:1px solid #00e676;border-radius:8px;padding:8px 14px;color:#38bdf8;font-family:sans-serif;font-size:12px;font-weight:700;z-index:999999;box-shadow:0 4px 20px rgba(0,0,0,0.5);display:flex;gap:10px;align-items:center;';
        hud.innerHTML = '<span style="color:#00e676;">🟢 CW SYNC ALIVE</span> <span id="cw-hud-phase" style="color:#f59e0b;padding:2px 6px;border-radius:4px;background:rgba(245,158,11,0.15);">BETTING</span> <span id="cw-hud-sec" style="font-weight:800;color:#ffffff;">--s</span> <span id="cw-hud-strike" style="color:#38bdf8;">Strike: $--</span>';
        document.body.appendChild(hud);
    }

    var lastSec = null;
    var currentPhase = 'BETTING';

    setInterval(function() {
        try {
            var text = document.body.innerText || '';

            // Detect phase via explicit text markers or sequential transition
            var isBattleText = /in\s*battle|battling|settling|battle\s*phase/i.test(text);

            var secMatch = text.match(/(\d{1,2})\s*s\b/i);
            var sec = secMatch ? parseInt(secMatch[1], 10) : null;

            var strikeMatch = text.match(/(?:Start|Strike|Open|Base|Price)[\s\:\$]*([\d,]+\.\d{2,4})/i);
            var p = strikeMatch ? parseFloat(strikeMatch[1].replace(/,/g, '')) : null;
            if (!p) {
                var allPrices = text.match(/[\$]?([1-9]\d{1,5}(?:\.\d{2,4})?)/g);
                if (allPrices && allPrices.length > 0) {
                    p = parseFloat(allPrices[0].replace(/[\$,]/g, ''));
                }
            }

            if (sec !== null) {
                // Sequential Phase Disambiguation
                if (isBattleText) {
                    currentPhase = 'BATTLE';
                } else if (sec > 5) {
                    currentPhase = 'BETTING';
                } else if (sec <= 5) {
                    // When previous countdown reached 0 or 1 in betting, a 5s countdown marks Battle phase
                    if (lastSec !== null && lastSec <= 1 && currentPhase === 'BETTING') {
                        currentPhase = 'BATTLE';
                    } else if (lastSec !== null && lastSec <= 1 && currentPhase === 'BATTLE') {
                        currentPhase = 'BETTING';
                    }
                }
                lastSec = sec;

                var phEl = document.getElementById('cw-hud-phase');
                if (phEl) {
                    phEl.textContent = currentPhase;
                    if (currentPhase === 'BATTLE') {
                        phEl.style.color = '#ef4444';
                        phEl.style.background = 'rgba(239,68,68,0.15)';
                    } else {
                        phEl.style.color = '#f59e0b';
                        phEl.style.background = 'rgba(245,158,11,0.15)';
                    }
                }

                var sEl = document.getElementById('cw-hud-sec');
                if (sEl) sEl.textContent = sec + 's';
            }

            if (p) {
                var pEl = document.getElementById('cw-hud-strike');
                if (pEl) pEl.textContent = 'Strike: $' + p.toFixed(2);
            }

            if (sec !== null && sec >= 0 && sec <= 60) {
                var payload = JSON.stringify({
                    seconds_left: sec,
                    open_price: p,
                    phase: currentPhase
                });

                fetch('http://127.0.0.1:5000/api/sync_cwallet', {
                    method: 'POST',
                    mode: 'cors',
                    headers: { 'Content-Type': 'application/json' },
                    body: payload
                }).catch(function() {
                    fetch('http://localhost:5000/api/sync_cwallet', {
                        method: 'POST',
                        mode: 'cors',
                        headers: { 'Content-Type': 'application/json' },
                        body: payload
                    }).catch(function() {});
                });
            }
        } catch (e) {
            console.warn('[CW Auto-Sync Error]', e);
        }
    }, 1000);

    alert('🟢 CWALLET AUTO-SYNC CONNECTED!\nLive Cwallet clock, phase, and strike are now streaming to TradeX.');
})();
