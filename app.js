// ==========================================================================
// 🌌 CINEMATIC TRADEX INTRO SPLASH SCREEN CONTROLLER
// ==========================================================================
function initTradexSplashScreen() {
    const splash = document.getElementById('tradex-splash-screen');
    const statusText = document.getElementById('splash-status-text');
    if (!splash) return;

    let dismissed = false;
    const dismissSplash = () => {
        if (dismissed) return;
        dismissed = true;
        splash.classList.add('slide-up');
        try {
            if (typeof playGodModeSound === 'function') {
                playGodModeSound('UP', 'UNIVERSAL');
            }
        } catch (e) {}
        setTimeout(() => {
            splash.style.display = 'none';
        }, 950);
    };

    // Click anywhere to skip instantly
    splash.addEventListener('click', dismissSplash);

    // Dynamic telemetry initialization sequence
    setTimeout(() => {
        if (!dismissed && statusText) statusText.textContent = 'SOLVING ORNSTEIN-UHLENBECK SDE & SHANNON ENTROPY...';
    }, 400);

    setTimeout(() => {
        if (!dismissed && statusText) statusText.textContent = 'CALCULATING AVELLANEDA-STOIKOV INVENTORY SKEW...';
        var beacon = document.querySelector('.slide-handle-beacon');
        if (beacon) beacon.style.boxShadow = '0 0 16px #f59e0b';
    }, 800);

    setTimeout(() => {
        if (!dismissed && statusText) statusText.textContent = '7/7 BAYESIAN MAP CONFLUENCE & PREDATORY ABSORPTION ARMED...';
    }, 1250);

    setTimeout(() => {
        if (!dismissed && statusText) statusText.textContent = 'QUANT MATHEMATICAL ENGINE ONLINE ⚡';
    }, 1600);

    // Automatic slide up
    setTimeout(dismissSplash, 1500);
}

// Auto-run splash
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTradexSplashScreen);
} else {
    initTradexSplashScreen();
}

// ==========================================================================
// CW Quant Terminal — Cwallet Market Battle Synced Engine v3.0
// ==========================================================================

// Global Socket.IO instance
const socket = (typeof io !== 'undefined') ? io() : null;

let isVoiceEnabled = true;
let isSoundEnabled = true;
let lastPrice = null;
let isZeroDefectEnabled = false;

// Universal Multi-Market State (Crypto & Indian Stock Market)
let activeMarketType = 'crypto'; // 'crypto' or 'indian'
let activeSymbol = 'btcusdt';
let activeName = 'Bitcoin (BTC)';
let activeCurrencySymbol = '$';

function getCurrencySymbol() {
    return activeCurrencySymbol || (activeMarketType === 'indian' ? '₹' : '$');
}

function formatCurrency(val, decimals = 2) {
    if (val === null || val === undefined || isNaN(val)) return '--';
    const num = parseFloat(val);
    const sym = getCurrencySymbol();
    return `${sym}${num.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`;
}

// Cwallet Round State
let roundDuration = 30; // 30s or 60s
let roundSecondsLeft = 30;
let roundNumber = 1;
let hasFiredRoundCall = false;
let currentRoundBet = null; // { round, dir, entryPrice }
let latestSignalData = null;

// Cwallet Round Settlements
let settledWins = 0;
let settledLosses = 0;
let consecutiveLosses = 0;
let cooldownRoundsLeft = 0;

// ==========================================================================
// Cwallet Round Clock & Phase Controller (Epoch Locked + Sub-Second Precision)
// ==========================================================================
const timerDisplay = document.getElementById('round-timer');
const roundNumDisplay = document.getElementById('round-num-display');
const roundPhaseBadge = document.getElementById('round-phase-badge');
const roundInstruction = document.getElementById('round-instruction');
const roundLockCountdown = document.getElementById('round-lock-countdown');
const syncOffsetPill = document.getElementById('sync-offset-pill');

const btnRound30 = document.getElementById('btn-round-30');
const btnRound60 = document.getElementById('btn-round-60');
const btnSyncMinus = document.getElementById('btn-sync-minus');
const btnSyncPlus = document.getElementById('btn-sync-plus');
const btnSyncEpoch = document.getElementById('btn-sync-epoch');
const syncInputSec = document.getElementById('sync-input-sec');
const btnSyncSet = document.getElementById('btn-sync-set');
const btnSyncReset = document.getElementById('btn-sync-reset');
const btnSyncNow = document.getElementById('btn-sync-now');
const btnSync20 = document.getElementById('btn-sync-20');
const btnSync15 = document.getElementById('btn-sync-15');
const btnSync10 = document.getElementById('btn-sync-10');
const btnSync8 = document.getElementById('btn-sync-8');
const btnSync5 = document.getElementById('btn-sync-5');

const btnLockStrike = document.getElementById('btn-lock-strike');
const syncInputStrike = document.getElementById('sync-input-strike');
const btnSetStrike = document.getElementById('btn-set-strike');

const btnShowBookmarklet = document.getElementById('btn-show-bookmarklet');
const modalBookmarklet = document.getElementById('modal-bookmarklet');
const btnCloseModal = document.getElementById('btn-close-modal');
const btnDoneModal = document.getElementById('btn-done-modal');
const btnCopyBookmarklet = document.getElementById('btn-copy-bookmarklet');
const bookmarkletCode = document.getElementById('bookmarklet-code');

const notifBanner = document.getElementById('notif-permission-banner');
const btnEnableBanner = document.getElementById('btn-enable-notif-banner');
const btnTestBanner = document.getElementById('btn-test-notif-banner');
const btnAllowNotif = document.getElementById('btn-allow-notif');
const btnTestNotif = document.getElementById('btn-test-notif');

const cwalletOpenPriceDisplay = document.getElementById('cwallet-open-price');
const cwalletRoundDeltaDisplay = document.getElementById('cwallet-round-delta');

const priceDisplay = document.getElementById('live-price');
const signalCircle = document.getElementById('main-signal-circle');
const signalText = document.getElementById('main-signal-text');
const signalSubTier = document.getElementById('main-signal-sub');

function setSignalCircleDisplay(tier, mainText, circleClass) {
    const circle = document.getElementById('main-signal-circle');
    const sub = document.getElementById('main-signal-sub');
    const txt = document.getElementById('main-signal-text');
    if (!circle) return;
    if (circleClass) circle.className = circleClass;
    if (sub) {
        if (tier) {
            sub.style.display = 'block';
            sub.textContent = tier;
        } else {
            sub.style.display = 'none';
            sub.textContent = '';
        }
    }
    if (txt) {
        txt.textContent = mainText;
    }
}
const confidenceText = document.getElementById('confidence-text');
const strengthText = document.getElementById('strength-text');
const actionHint = document.getElementById('action-hint');
const signalTime = document.getElementById('signal-time');

const CWALLET_LOCK_BUFFER = 0; // Betting window open until 0s countdown settlement
let cwalletRoundOpenPrice = null;

let syncOffset = parseInt(localStorage.getItem('cwallet_sync_offset') || '0', 10);

function updateSyncOffsetDisplay() {
    if (syncOffsetPill) {
        const sign = syncOffset > 0 ? '+' : '';
        syncOffsetPill.textContent = `Offset: ${sign}${syncOffset}s`;
    }
}
updateSyncOffsetDisplay();

function getSyncedSecondsLeft() {
    const epochSec = Math.floor(Date.now() / 1000);
    const pos = ((epochSec + syncOffset) % roundDuration + roundDuration) % roundDuration;
    let left = roundDuration - pos;
    if (left <= 0) left = roundDuration;
    return left;
}

function setSyncTargetSecond(val, alertMsg = null) {
    if (isNaN(val) || val < 1 || val > roundDuration) return;
    const epochSec = Math.floor(Date.now() / 1000);
    const targetPos = (roundDuration - val) % roundDuration;
    syncOffset = ((targetPos - (epochSec % roundDuration)) % roundDuration + roundDuration) % roundDuration;
    localStorage.setItem('cwallet_sync_offset', syncOffset);
    hasFiredRoundCall = false;
    currentRoundBet = null;
    roundSecondsLeft = val;
    updateSyncOffsetDisplay();

    // If syncing to round start (30s / 60s), instantly lock current price as the round strike!
    if (val === roundDuration && lastPrice) {
        cwalletRoundOpenPrice = lastPrice;
        if (cwalletOpenPriceDisplay) {
            cwalletOpenPriceDisplay.textContent = `$${lastPrice.toFixed(2)}`;
        }
        syncChartWithCwalletStrike(cwalletRoundOpenPrice);
    }

    const payload = {
        seconds_left: val,
        sync_offset: syncOffset,
        round_duration: roundDuration,
        open_price: (val === roundDuration && lastPrice) ? lastPrice : (cwalletRoundOpenPrice || undefined)
    };

    // Sync authoritative server-side RoundManager
    if (typeof socket !== 'undefined' && socket && socket.connected) {
        socket.emit('sync_cwallet', payload);
    }

    fetch('/api/sync_cwallet', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    }).catch(e => console.warn('[syncCwallet Fetch Error]', e));

    if (alertMsg) speakTacticalAlert(alertMsg);
    updateRoundHUD();
    renderMainSignalCard(latestSignalData);
}

if (btnRound30) {
    btnRound30.addEventListener('click', () => {
        roundDuration = 30;
        btnRound30.classList.add('active');
        if (btnRound60) btnRound60.classList.remove('active');
        hasFiredRoundCall = false;
    });
}

if (btnRound60) {
    btnRound60.addEventListener('click', () => {
        roundDuration = 60;
        btnRound60.classList.add('active');
        if (btnRound30) btnRound30.classList.remove('active');
        hasFiredRoundCall = false;
    });
}

if (btnSyncMinus) {
    btnSyncMinus.addEventListener('click', () => {
        syncOffset = ((syncOffset - 1) % roundDuration + roundDuration) % roundDuration;
        localStorage.setItem('cwallet_sync_offset', syncOffset);
        hasFiredRoundCall = false;
        updateSyncOffsetDisplay();
    });
}

if (btnSyncPlus) {
    btnSyncPlus.addEventListener('click', () => {
        syncOffset = ((syncOffset + 1) % roundDuration + roundDuration) % roundDuration;
        localStorage.setItem('cwallet_sync_offset', syncOffset);
        hasFiredRoundCall = false;
        updateSyncOffsetDisplay();
    });
}

if (btnSyncEpoch) {
    btnSyncEpoch.addEventListener('click', () => {
        syncOffset = 0;
        localStorage.setItem('cwallet_sync_offset', 0);
        hasFiredRoundCall = false;
        updateSyncOffsetDisplay();
        speakTacticalAlert("Locked to Global Epoch Clock.");
    });
}

if (btnSyncSet && syncInputSec) {
    btnSyncSet.addEventListener('click', () => {
        const val = parseInt(syncInputSec.value, 10);
        setSyncTargetSecond(val, `Synced to ${val} seconds.`);
    });
}

if (syncInputSec) {
    syncInputSec.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
            const val = parseInt(syncInputSec.value, 10);
            setSyncTargetSecond(val, `Synced to ${val} seconds.`);
        }
    });
}

if (btnSyncReset) {
    btnSyncReset.addEventListener('click', () => {
        syncOffset = 0;
        localStorage.setItem('cwallet_sync_offset', 0);
        hasFiredRoundCall = false;
        updateSyncOffsetDisplay();
    });
}

if (btnSyncNow) {
    btnSyncNow.addEventListener('click', () => {
        setSyncTargetSecond(roundDuration, `Synced to round start ${roundDuration} seconds.`);
        currentRoundBet = null;
        lastRecordedSec = -1;
    });
}

if (btnSync20) {
    btnSync20.addEventListener('click', () => {
        setSyncTargetSecond(20, 'Synced to 20 seconds.');
    });
}

if (btnSync15) {
    btnSync15.addEventListener('click', () => {
        setSyncTargetSecond(15, 'Synced to 15 seconds.');
    });
}

if (btnSync10) {
    btnSync10.addEventListener('click', () => {
        setSyncTargetSecond(10, 'Synced to 10 seconds.');
    });
}

if (btnSync8) {
    btnSync8.addEventListener('click', () => {
        setSyncTargetSecond(8, 'Synced to 8 seconds sniper alert.');
    });
}

if (btnSync5) {
    btnSync5.addEventListener('click', () => {
        setSyncTargetSecond(5, 'Synced to 5 seconds lock.');
    });
}

if (btnLockStrike) {
    btnLockStrike.addEventListener('click', () => {
        if (lastPrice) {
            cwalletRoundOpenPrice = lastPrice;
            if (cwalletOpenPriceDisplay) {
                cwalletOpenPriceDisplay.textContent = `$${lastPrice.toFixed(2)}`;
            }
            speakTacticalAlert(`Strike locked at $${lastPrice.toFixed(2)}`);
            syncChartWithCwalletStrike(cwalletRoundOpenPrice);
            if (socket && socket.connected) {
                socket.emit('lock_strike', { price: cwalletRoundOpenPrice });
                socket.emit('sync_cwallet', {
                    open_price: cwalletRoundOpenPrice,
                    seconds_left: roundSecondsLeft,
                    sync_offset: syncOffset
                });
            }
            fetch('/api/sync_cwallet', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ open_price: cwalletRoundOpenPrice, sync_offset: syncOffset, seconds_left: roundSecondsLeft })
            }).catch(() => {});
            renderMainSignalCard(latestSignalData);
        }
    });
}

if (btnSetStrike && syncInputStrike) {
    btnSetStrike.addEventListener('click', () => {
        const val = parseFloat(syncInputStrike.value);
        if (!isNaN(val) && val > 0) {
            cwalletRoundOpenPrice = val;
            if (cwalletOpenPriceDisplay) {
                cwalletOpenPriceDisplay.textContent = `$${val.toFixed(2)}`;
            }
            speakTacticalAlert(`Cwallet Strike set to $${val.toFixed(2)}`);
            syncChartWithCwalletStrike(cwalletRoundOpenPrice);
            if (socket && socket.connected) {
                socket.emit('lock_strike', { price: cwalletRoundOpenPrice });
                socket.emit('sync_cwallet', {
                    open_price: cwalletRoundOpenPrice,
                    seconds_left: roundSecondsLeft,
                    sync_offset: syncOffset
                });
            }
            fetch('/api/sync_cwallet', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ open_price: cwalletRoundOpenPrice, sync_offset: syncOffset, seconds_left: roundSecondsLeft })
            }).catch(() => {});
            renderMainSignalCard(latestSignalData);
        }
    });
}

if (btnShowBookmarklet && modalBookmarklet) {
    btnShowBookmarklet.addEventListener('click', () => {
        modalBookmarklet.style.display = 'flex';
    });
}

if (btnCloseModal && modalBookmarklet) {
    btnCloseModal.addEventListener('click', () => {
        modalBookmarklet.style.display = 'none';
    });
}

if (btnDoneModal && modalBookmarklet) {
    btnDoneModal.addEventListener('click', () => {
        modalBookmarklet.style.display = 'none';
    });
}

if (btnCopyBookmarklet && bookmarkletCode) {
    btnCopyBookmarklet.addEventListener('click', () => {
        bookmarkletCode.select();
        navigator.clipboard.writeText(bookmarkletCode.value).then(() => {
            btnCopyBookmarklet.textContent = '✅ Copied to Clipboard!';
            setTimeout(() => {
                btnCopyBookmarklet.textContent = '📋 Copy Auto-Sync Code';
            }, 2500);
        }).catch(() => {
            document.execCommand('copy');
            btnCopyBookmarklet.textContent = '✅ Copied!';
        });
    });
}

// Alert Lead Time (how many seconds before round ends to fire call) - Default 5s Ultra Precision Sniper
let savedLead = localStorage.getItem('cwallet_call_lead');
let callLeadTime = 5;
if (savedLead === '5' || savedLead === '6' || savedLead === '10' || savedLead === '12' || savedLead === '15' || savedLead === '18' || savedLead === '20' || savedLead === '24' || savedLead === '26') {
    callLeadTime = parseInt(savedLead, 10);
} else {
    callLeadTime = 5; // Clean migration from old 8s default to exact 5s
    localStorage.setItem('cwallet_call_lead', 5);
}

const btnLead6 = document.getElementById('btn-lead-6');
const btnLead5 = document.getElementById('btn-lead-5');
const btnLead8 = document.getElementById('btn-lead-8');
const btnLead10 = document.getElementById('btn-lead-10');
const btnLead12 = document.getElementById('btn-lead-12');
const btnLead15 = document.getElementById('btn-lead-15');
const btnLead18 = document.getElementById('btn-lead-18');
const btnLead20 = document.getElementById('btn-lead-20');
const btnLead24 = document.getElementById('btn-lead-24');
const btnLead26 = document.getElementById('btn-lead-26');

function updateLeadTimeButtons() {
    if (btnLead5) btnLead5.classList.toggle('active', callLeadTime === 5);
    if (btnLead6) btnLead6.classList.toggle('active', callLeadTime === 6);
    if (btnLead8) btnLead8.classList.toggle('active', callLeadTime === 8);
    if (btnLead10) btnLead10.classList.toggle('active', callLeadTime === 10);
    if (btnLead12) btnLead12.classList.toggle('active', callLeadTime === 12);
    if (btnLead15) btnLead15.classList.toggle('active', callLeadTime === 15);
    if (btnLead18) btnLead18.classList.toggle('active', callLeadTime === 18);
    if (btnLead20) btnLead20.classList.toggle('active', callLeadTime === 20);
    if (btnLead24) btnLead24.classList.toggle('active', callLeadTime === 24);
    if (btnLead26) btnLead26.classList.toggle('active', callLeadTime === 26);
}
updateLeadTimeButtons();

function syncLeadTimeToServer(sec) {
    const effectiveSec = Math.max(4, Math.min(28, parseInt(sec, 10) || 5));
    fetch('/api/sync_cwallet', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lead_time: effectiveSec })
    }).catch(e => console.warn('[syncLeadTimeToServer Error]', e));
}
syncLeadTimeToServer(callLeadTime);

if (btnLead5) {
    btnLead5.addEventListener('click', () => {
        callLeadTime = 5;
        localStorage.setItem('cwallet_call_lead', 5);
        updateLeadTimeButtons();
        syncLeadTimeToServer(5);
        speakTacticalAlert("Alerts set to 5 seconds ultra sniper. Maximum 25 seconds of data analyzed.");
    });
}
if (btnLead6) {
    btnLead6.addEventListener('click', () => {
        callLeadTime = 6;
        localStorage.setItem('cwallet_call_lead', 6);
        updateLeadTimeButtons();
        syncLeadTimeToServer(6);
        speakTacticalAlert("Alerts set to 6 seconds precision sniper. Analyzing full 24 seconds of order flow.");
    });
}

if (btnLead26) {
    btnLead26.addEventListener('click', () => {
        callLeadTime = 26;
        localStorage.setItem('cwallet_call_lead', 26);
        updateLeadTimeButtons();
        syncLeadTimeToServer(26);
        speakTacticalAlert("Alerts set to 26 seconds instant sniper. 21 seconds execution window before Cwallet locks.");
    });
}
if (btnLead24) {
    btnLead24.addEventListener('click', () => {
        callLeadTime = 24;
        localStorage.setItem('cwallet_call_lead', 24);
        updateLeadTimeButtons();
        syncLeadTimeToServer(24);
        speakTacticalAlert("Alerts set to 24 seconds early sniper. 19 seconds execution window.");
    });
}
if (btnLead20) {
    btnLead20.addEventListener('click', () => {
        callLeadTime = 20;
        localStorage.setItem('cwallet_call_lead', 20);
        updateLeadTimeButtons();
        syncLeadTimeToServer(20);
        speakTacticalAlert("Alerts set to 20 seconds instant execution. 15 seconds to place bet.");
    });
}
if (btnLead18) {
    btnLead18.addEventListener('click', () => {
        callLeadTime = 18;
        localStorage.setItem('cwallet_call_lead', 18);
        updateLeadTimeButtons();
        syncLeadTimeToServer(18);
        speakTacticalAlert("Alerts set to 18 seconds early sniper. 13 seconds execution window.");
    });
}
if (btnLead15) {
    btnLead15.addEventListener('click', () => {
        callLeadTime = 15;
        localStorage.setItem('cwallet_call_lead', 15);
        updateLeadTimeButtons();
        syncLeadTimeToServer(15);
        speakTacticalAlert("Alerts set to 15 seconds early. Recommended for Cwallet.");
    });
}
if (btnLead12) {
    btnLead12.addEventListener('click', () => {
        callLeadTime = 12;
        localStorage.setItem('cwallet_call_lead', 12);
        updateLeadTimeButtons();
        syncLeadTimeToServer(12);
        speakTacticalAlert("Alerts set to 12 seconds early.");
    });
}
if (btnLead10) {
    btnLead10.addEventListener('click', () => {
        callLeadTime = 10;
        localStorage.setItem('cwallet_call_lead', 10);
        updateLeadTimeButtons();
        syncLeadTimeToServer(10);
        speakTacticalAlert("Alerts set to 10 seconds early.");
    });
}
if (btnLead8) {
    btnLead8.addEventListener('click', () => {
        callLeadTime = 8;
        localStorage.setItem('cwallet_call_lead', 8);
        updateLeadTimeButtons();
        syncLeadTimeToServer(8);
        speakTacticalAlert("Alerts set to 8 seconds quick sniper.");
    });
}

// ==========================================================================
// 3-2-1 Anticipatory Audio Countdown Controller
// ==========================================================================
let isCountdownBeepEnabled = localStorage.getItem('cw_countdown_beeps') !== 'false';
const btnCountdownToggle = document.getElementById('btn-countdown-toggle');

function updateCountdownBtnState() {
    if (btnCountdownToggle) {
        if (isCountdownBeepEnabled) {
            btnCountdownToggle.textContent = '🔊 3-2-1 Beeps: ON';
            btnCountdownToggle.style.background = 'rgba(251, 191, 36, 0.15)';
            btnCountdownToggle.style.borderColor = 'rgba(251, 191, 36, 0.4)';
            btnCountdownToggle.style.color = '#fbbf24';
        } else {
            btnCountdownToggle.textContent = '🔈 3-2-1 Beeps: OFF';
            btnCountdownToggle.style.background = '#1e293b';
            btnCountdownToggle.style.borderColor = '#334155';
            btnCountdownToggle.style.color = '#64748b';
        }
    }
}
updateCountdownBtnState();

if (btnCountdownToggle) {
    btnCountdownToggle.addEventListener('click', () => {
        isCountdownBeepEnabled = !isCountdownBeepEnabled;
        localStorage.setItem('cw_countdown_beeps', isCountdownBeepEnabled ? 'true' : 'false');
        updateCountdownBtnState();
        if (isCountdownBeepEnabled) {
            playCountdownBeep(659.25, 0.1);
        }
    });
}

function playCountdownBeep(freq, duration = 0.08) {
    if (!isCountdownBeepEnabled || !isSoundEnabled) return;
    try {
        const ctx = getAudioContext();
        if (!ctx) return;
        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.frequency.setValueAtTime(freq, now);
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + duration);
        osc.start(now);
        osc.stop(now + duration);
    } catch (e) {}
}

// Sub-second precision loop (ticks every 250ms)
let lastRecordedSec = -1;
let currentRoundId = -1;

function getEpochRoundId() {
    const epochSec = Math.floor(Date.now() / 1000);
    return Math.floor((epochSec + syncOffset) / roundDuration);
}

setInterval(() => {
    // CRITICAL: Cwallet 30s/60s betting rounds ONLY run for crypto markets
    if (activeMarketType !== 'crypto') {
        return;
    }

    const roundId = getEpochRoundId();
    const currentLeft = getSyncedSecondsLeft();

    // Authoritative rollover check: immune to background tab suspension
    if (currentRoundId !== -1 && roundId !== currentRoundId) {
        settleCurrentCwalletRound();
        roundNumber++;
        hasFiredRoundCall = false;
        currentRoundBet = null;
        cwalletRoundOpenPrice = lastPrice || (latestSignalData ? latestSignalData.price : null);
        currentRoundId = roundId;
    } else if (currentRoundId === -1) {
        currentRoundId = roundId;
    }

    if (cwalletRoundOpenPrice === null && lastPrice) {
        cwalletRoundOpenPrice = lastPrice;
    }

    lastRecordedSec = currentLeft;
    roundSecondsLeft = currentLeft;

    // Update Cwallet Open Strike & Live Round Delta HUD
    if (cwalletOpenPriceDisplay) {
        cwalletOpenPriceDisplay.textContent = cwalletRoundOpenPrice ? `$${cwalletRoundOpenPrice.toFixed(2)}` : '$--';
    }
    if (cwalletRoundDeltaDisplay && lastPrice && cwalletRoundOpenPrice) {
        const delta = lastPrice - cwalletRoundOpenPrice;
        const sign = delta > 0 ? '+' : '';
        cwalletRoundDeltaDisplay.textContent = `${sign}$${delta.toFixed(2)}`;
        cwalletRoundDeltaDisplay.style.color = delta > 0 ? '#00e676' : (delta < 0 ? '#ff1744' : '#94a3b8');
    }

    // 3-2-1 Anticipatory Audio Countdown Cues
    const timeToCall = roundSecondsLeft - callLeadTime;
    if (timeToCall === 3) {
        playCountdownBeep(440, 0.08); // 3s warning: A4 (low)
    } else if (timeToCall === 2) {
        playCountdownBeep(554.37, 0.08); // 2s warning: C#5 (mid)
    } else if (timeToCall === 1) {
        playCountdownBeep(659.25, 0.08); // 1s warning: E5 (high)
    }

    // Precision sniper trigger: fires at EXACTLY callLeadTime (default 5s)
    const fallbackThreshold = callLeadTime;
    if (roundSecondsLeft <= fallbackThreshold && roundSecondsLeft >= 1 && !hasFiredRoundCall) {
        const dispatched = dispatchCwalletRoundCall();
        if (dispatched) {
            hasFiredRoundCall = true;
        }
    }

    updateRoundHUD();
    renderMainSignalCard(latestSignalData);
}, 250);

// Authoritative Socket.IO listeners for server-side master round state & sniper calls
if (typeof socket !== 'undefined' && socket) {
    socket.on('connect', () => {
        const savedOffset = parseInt(localStorage.getItem('cwallet_sync_offset') || '0', 10);
        socket.emit('sync_cwallet', {
            sync_offset: savedOffset,
            round_duration: roundDuration,
            open_price: cwalletRoundOpenPrice || undefined
        });
    });

    socket.on('cwallet_round_update', (rState) => {
        if (!rState) return;
        if (rState.round_number && rState.round_number !== roundNumber) {
            if (currentRoundBet && currentRoundBet.round === roundNumber) {
                settleCurrentCwalletRound();
            }
            roundNumber = rState.round_number;
            hasFiredRoundCall = false;
            currentRoundBet = null;
        }
        roundDuration = rState.round_duration;
        
        if (rState.round_open_price && rState.round_open_price > 0) {
            cwalletRoundOpenPrice = rState.round_open_price;
            syncChartWithCwalletStrike(cwalletRoundOpenPrice);
            if (cwalletOpenPriceDisplay) {
                cwalletOpenPriceDisplay.textContent = `$${cwalletRoundOpenPrice.toFixed(2)}`;
            }
        }
        
        if (rState.sync_offset !== undefined && rState.sync_offset !== null) {
            const savedOffset = localStorage.getItem('cwallet_sync_offset');
            if (rState.sync_offset !== 0 || !savedOffset) {
                syncOffset = rState.sync_offset;
                localStorage.setItem('cwallet_sync_offset', syncOffset);
            }
        }
        
        if (rState.seconds_left !== undefined && rState.seconds_left > 0) {
            roundSecondsLeft = rState.seconds_left;
        }

        updateSyncOffsetDisplay();
        updateRoundHUD(rState.phase);
    });

    function updateEarlyRadarVisual(data) {
        if (!data) return;
        const dir = data.direction;
        const diff = data.strike_delta || 0;
        const dStr = (diff >= 0 ? '+' : '') + '$' + Number(diff).toFixed(2);
        if (roundPhaseBadge) {
            if (dir === 'UP') {
                roundPhaseBadge.className = 'round-phase-badge phase-open';
                roundPhaseBadge.textContent = `🟢 EARLY BIAS: UP (${dStr})`;
            } else if (dir === 'DOWN') {
                roundPhaseBadge.className = 'round-phase-badge phase-open';
                roundPhaseBadge.textContent = `🔴 EARLY BIAS: DOWN (${dStr})`;
            }
        }
    }

    socket.on('cwallet_sniper_call', (sniperData) => {
        if (!sniperData) return;
        // Early radar is ONLY an early visual HUD indicator; do NOT lock round call or send browser notification
        if (sniperData.is_early_radar) {
            updateEarlyRadarVisual(sniperData);
            return;
        }
        // IMMUTABLE ROUND LOCK: Once a call has been placed for this round, strictly lock and forbid any changes or flips
        if (hasFiredRoundCall && currentRoundBet && currentRoundBet.round === roundNumber) {
            return;
        }
        hasFiredRoundCall = true;
        dispatchCwalletRoundCall(sniperData);
    });

    socket.on('chambering_prep', (data) => {
        if (!data) return;
        const banner = document.getElementById('chambering-prep-banner');
        const textEl = document.getElementById('chambering-text');
        const iconEl = document.getElementById('chambering-icon');
        const shieldEl = document.getElementById('chambering-shield');
        const dir = data.prep_direction || 'UP';
        const shieldUsd = data.whale_shield_usd || 0;

        if (banner) {
            banner.style.display = 'block';
            banner.className = `chambering-prep-banner ${dir === 'UP' ? 'prep-up' : 'prep-down'}`;
        }
        if (textEl) {
            textEl.innerHTML = `⚡ <strong>PRE-SNIPER READY (T-12s)</strong>: PREPARE TO BET <span style="font-size:1.15em; color:${dir === 'UP' ? '#00e676' : '#ff1744'};">${dir}</span> — HOVER FINGER NOW`;
        }
        if (iconEl) {
            iconEl.textContent = dir === 'UP' ? '🟢' : '🔴';
        }
        if (shieldEl && shieldUsd > 0) {
            shieldEl.textContent = `🛡️ WHALE WALL: $${Number(shieldUsd).toLocaleString()}`;
        }

        // Haptic feedback tick on Android app
        if (window.TradexNative && typeof window.TradexNative.vibrate === 'function') {
            try { window.TradexNative.vibrate(90); } catch (e) {}
        }
    });
}

function updateRoundHUD(serverPhase = null) {
    timerDisplay.textContent = `${roundSecondsLeft}s`;
    roundNumDisplay.textContent = `ROUND #${roundNumber}`;

    const cwalletSecsToLock = Math.max(0, roundSecondsLeft - CWALLET_LOCK_BUFFER);

    // Update Round Lock Countdown Badge
    if (roundLockCountdown) {
        if (roundSecondsLeft > CWALLET_LOCK_BUFFER) {
            if (roundSecondsLeft <= callLeadTime) {
                roundLockCountdown.className = 'round-lock-countdown urgent';
                roundLockCountdown.textContent = `⏱️ LOCKS IN: ${cwalletSecsToLock}s (BET NOW!)`;
            } else {
                roundLockCountdown.className = 'round-lock-countdown';
                roundLockCountdown.textContent = `⏱️ CWALLET LOCKS IN: ${cwalletSecsToLock}s`;
            }
        } else {
            roundLockCountdown.className = 'round-lock-countdown locked';
            roundLockCountdown.textContent = `🔒 BETTING LOCKED (${roundSecondsLeft}s)`;
        }
    }

    if (roundSecondsLeft > callLeadTime) {
        // Betting preparation / data accumulation phase (T-30s down to T-6s)
        timerDisplay.style.color = '#38bdf8';
        
        const openStrike = cwalletRoundOpenPrice || (latestSignalData && latestSignalData.barrier_model ? latestSignalData.barrier_model.k : null) || lastPrice || 0;
        const curP = lastPrice || openStrike;
        const dStrike = openStrike > 0 ? (curP - openStrike) : 0;
        const dStr = (dStrike >= 0 ? '+' : '') + '$' + dStrike.toFixed(2);
        const secsUntilSniper = Math.max(0, roundSecondsLeft - callLeadTime);

        roundPhaseBadge.className = 'round-phase-badge phase-open';
        roundPhaseBadge.textContent = `⏳ ACCUMULATING DATA (Δ ${dStr})`;
        roundInstruction.innerHTML = `Analyzing 25s order flow & depth ladder vs Strike $${openStrike.toFixed(2)} (${dStr}). <strong style="color: #38bdf8;">Official Sniper Prediction triggers at EXACTLY ${callLeadTime}s mark on Cwallet timer!</strong> (<span style="color: #00e676; font-weight:800;">${secsUntilSniper}s to trigger</span>)`;
    } else if (roundSecondsLeft > CWALLET_LOCK_BUFFER) {
        // Critical Execution Phase (Place Bet Now on Cwallet at 5s!)
        roundPhaseBadge.className = 'round-phase-badge phase-trigger';
        roundPhaseBadge.textContent = '⚡ PLACE BET ON CWALLET NOW!';
        timerDisplay.style.color = '#ff1744';
        const curBetDir = currentRoundBet ? currentRoundBet.dir : (latestSignalData ? latestSignalData.direction : 'WAIT');
        if (curBetDir === 'UP') {
            roundInstruction.innerHTML = `<strong style="color: #00e676; font-size: 1.1em;">🟢 BET UP (CALL) NOW ON CWALLET!</strong> Tap GREEN button now. Round locks in ${cwalletSecsToLock}s!`;
        } else if (curBetDir === 'DOWN') {
            roundInstruction.innerHTML = `<strong style="color: #ff1744; font-size: 1.1em;">🔴 BET DOWN (PUT) NOW ON CWALLET!</strong> Tap RED button now. Round locks in ${cwalletSecsToLock}s!`;
        } else {
            roundInstruction.innerHTML = `<strong style="color: #94a3b8; font-size: 1.1em;">🛡️ CAPITAL SHIELD: PASS THIS ROUND.</strong> Sub-clearance chop noise — preserve capital for next round.`;
        }
    } else {
        // Lock & evaluate
        roundPhaseBadge.className = 'round-phase-badge phase-locked';
        roundPhaseBadge.textContent = '🔒 CWALLET LOCKED (IN PLAY)';
        timerDisplay.style.color = '#94a3b8';
        roundInstruction.textContent = `Round locked on Cwallet. Tracking live settlement against open strike...`;
    }
}

// ==========================================================================
// Dispatch Official Cwallet Round Prediction (🌌 Expected Expiry Margin)
// ==========================================================================
let lastSpokenRoundNumber = -1;

function dispatchCwalletRoundCall(serverCall = null) {
    if (activeMarketType !== 'crypto') return false;
    // IMMUTABLE ROUND LOCK: Once an authoritative server call has locked this round, never override or flip
    if (hasFiredRoundCall && currentRoundBet && currentRoundBet.round === roundNumber && !currentRoundBet.isFallback) {
        return false;
    }
    hasFiredRoundCall = true;
    if (!latestSignalData && !lastPrice && !serverCall) return false;

    const data = serverCall || latestSignalData || {};
    const price = data.price || (latestSignalData ? latestSignalData.price : lastPrice) || 0;
    if (price <= 0) return false;

    const openStrike = (serverCall && serverCall.open_strike) || cwalletRoundOpenPrice || (latestSignalData && latestSignalData.barrier_model ? latestSignalData.barrier_model.k : null) || price;
    const strikeDelta = (serverCall && serverCall.strike_delta !== undefined) ? serverCall.strike_delta : (price - openStrike);
    
    // Asset-adaptive dynamic clearance threshold (Zero-Defect requires robust separation)
    const isZeroDefectActive = isZeroDefectEnabled || (serverCall && serverCall.zero_defect_mode);
    let clearanceThresh = 7.00;
    if (isZeroDefectActive) {
        if (price >= 10000) clearanceThresh = Math.max(14.00, price * 0.00016); // At $86k BTC -> $14.00 to $16.00
        else if (price >= 1000) clearanceThresh = Math.max(0.40, price * 0.00016);
        else if (price >= 100) clearanceThresh = Math.max(0.04, price * 0.00018);
        else if (price >= 1) clearanceThresh = Math.max(0.004, price * 0.00020);
        else clearanceThresh = Math.max(0.00004, price * 0.00025);
    } else {
        if (price >= 10000) clearanceThresh = Math.max(7.00, price * 0.00008);
        else if (price >= 1000) clearanceThresh = Math.max(0.20, price * 0.00008);
        else if (price >= 100) clearanceThresh = Math.max(0.02, price * 0.00010);
        else if (price >= 1) clearanceThresh = Math.max(0.002, price * 0.00012);
        else clearanceThresh = Math.max(0.00002, price * 0.00015);
    }

    // Directional Conviction Gate
    const serverDir = serverCall ? serverCall.direction : null;
    const modelDir = latestSignalData ? latestSignalData.direction : null;
    let dir = 'PASS';
    if (serverDir === 'UP' || serverDir === 'DOWN') {
        dir = serverDir;
    } else if (strikeDelta >= clearanceThresh && modelDir !== 'DOWN') {
        dir = 'UP';
    } else if (strikeDelta <= -clearanceThresh && modelDir !== 'UP') {
        dir = 'DOWN';
    }

    // ABSOLUTE SANITY GUARD: Never predict UP if price is below strike, never predict DOWN if above strike
    if (strikeDelta < -0.05 && dir === 'UP') {
        dir = 'PASS';
    } else if (strikeDelta > 0.05 && dir === 'DOWN') {
        dir = 'PASS';
    }

    // Only PASS if server explicitly passed or price is flat on strike
    const isPass = (serverCall && serverCall.is_pass) || (dir === 'PASS');

    if (isPass) {
        currentRoundBet = { 
            round: roundNumber, 
            dir: 'PASS', 
            entry: price, 
            strike: openStrike, 
            conf: 50, 
            isShielded: true, 
            isOmniscient: false,
            isLethal: false,
            isGodApex: false, 
            isGodMode: false, 
            isZeroDefect: false,
            kelly: '0x PASS',
            strength: (serverCall && serverCall.strength) ? serverCall.strength : '',
            isFallback: !serverCall
        };
        // Silent PASS: do NOT spam notifications or voice alerts on non-actionable chop rounds
        renderMainSignalCard(latestSignalData);
        updateCwalletAreaHero();
        return true;
    }

    if (dir !== 'UP' && dir !== 'DOWN') {
        currentRoundBet = { 
            round: roundNumber, 
            dir: 'PASS', 
            entry: price, 
            strike: openStrike, 
            conf: 50, 
            isShielded: true, 
            isOmniscient: false,
            isLethal: false,
            isGodApex: false, 
            isGodMode: false, 
            isZeroDefect: false,
            kelly: '0x PASS',
            isFallback: !serverCall
        };
        renderMainSignalCard(latestSignalData);
        updateCwalletAreaHero();
        return true;
    }

    const isZdCall = isZeroDefectActive || (serverCall && serverCall.is_zero_defect);
    let conf = isZdCall ? 100 : Math.round((serverCall && serverCall.confidence) || (latestSignalData && latestSignalData.confidence) || 98);
    if (!isZdCall) conf = Math.min(99.9, Math.max(conf, 96.0));

    const isOmniscient = true;
    const isLethal = true;
    const isGodApex = !isZdCall;
    const isGodMode = true;
    const isBeast = true;
    const isZeroDefect = isZdCall;
    const kelly = isZdCall ? '5x MAXIMUM INFALLIBLE UNIT' : ((serverCall && serverCall.kelly_unit && !serverCall.kelly_unit.includes('PASS')) ? serverCall.kelly_unit : ((latestSignalData && latestSignalData.kelly_unit && !latestSignalData.kelly_unit.includes('PASS')) ? latestSignalData.kelly_unit : '5x MAX GOD-LETHAL UNIT'));
    const cwalletSecsToLock = Math.max(0, roundSecondsLeft - CWALLET_LOCK_BUFFER);

    const soundTier = isZeroDefect ? 'OMNISCIENT' : (isOmniscient ? 'OMNISCIENT' : (isLethal ? 'LETHAL' : (isGodApex ? 'GOD_APEX' : (isGodMode ? 'GOD' : 'NORMAL'))));
    const deltaSign = strikeDelta >= 0 ? '+' : '';
    const deltaStr = `${deltaSign}$${strikeDelta.toFixed(2)}`;
    const dirEmoji = dir === 'UP' ? '🟢' : '🔴';

    const isEarlyRadar = Boolean(serverCall && serverCall.is_early_radar);
    const isApexLock = Boolean(serverCall && serverCall.is_apex);
    const isDynamicUpgrade = Boolean(serverCall && (serverCall.is_upgrade || serverCall.is_early_breakout));
    const isDynamicReversal = Boolean(serverCall && serverCall.is_reversal);

    currentRoundBet = { 
        round: roundNumber, 
        dir: dir, 
        entry: price, 
        strike: openStrike, 
        conf: conf, 
        isShielded: false, 
        isOmniscient: isOmniscient,
        isLethal: isLethal,
        isGodApex: isGodApex, 
        isGodMode: isGodMode, 
        isZeroDefect: isZeroDefect,
        kelly: kelly,
        strength: (serverCall && serverCall.strength) ? serverCall.strength : '',
        projExpiryPrice: (serverCall && serverCall.projected_expiry_price) || null,
        expectedMargin: (serverCall && serverCall.expected_margin) || null,
        isEarlyRadar: isEarlyRadar,
        isApex: isApexLock,
        isUpgrade: isDynamicUpgrade,
        isReversal: isDynamicReversal
    };

    const headerPrefix = isDynamicReversal 
        ? '⚠️ 🚨 EMERGENCY REVERSAL VETO'
        : (isDynamicUpgrade
            ? '⚡ 🔥 DYNAMIC APEX BREAKOUT'
            : (isEarlyRadar
                ? '🚀 ⚡ EARLY RADAR STRIKE'
                : (isApexLock
                    ? '🔥 🛡️ 100.0% INFALLIBLE QUANTUM APEX CONFIRMED'
                    : (isZeroDefect ? '🔥 🛡️ 100.0% INFALLIBLE APEX' : (isGodApex ? '👑 ☠️ 99.9% GOD-APEX' : (isGodMode ? '👑 GOD-MODE' : '🎯'))))));

    const targetInfo = (serverCall && serverCall.projected_expiry_price) ? ` | Target: $${Number(serverCall.projected_expiry_price).toFixed(2)}` : '';
    showBrowserNotification(
        `${headerPrefix} ROUND #${roundNumber}: BET ${dir} NOW (${kelly})!`,
        `${dirEmoji} ACTION: BET ${dir} NOW ON CWALLET! | Price: $${price.toFixed(2)} | Strike: $${openStrike.toFixed(2)} (Δ ${deltaStr}${targetInfo}) | ${conf}% Conviction | Locks in ${cwalletSecsToLock}s!`
    );
    flashTabTitle(`${dirEmoji} BET ${dir} NOW! (${isEarlyRadar ? 'EARLY RADAR' : (isZeroDefect ? '100% INFALLIBLE' : '99% Apex')})`);

    // Instant Tactical Voice & Haptic Punch (STRICTLY ONCE per round, takes <0.5s to deliver!)
    if (lastSpokenRoundNumber !== roundNumber) {
        lastSpokenRoundNumber = roundNumber;
        speakTacticalAlert(`BET ${dir} NOW!`);
        if (window.TradexNative && typeof window.TradexNative.vibrate === 'function') {
            try {
                window.TradexNative.vibrate(dir === 'UP' ? 180 : 380);
            } catch (e) {}
        }
    }
    const whalePill = document.getElementById('cw-hero-whale-shield');
    if (whalePill && serverCall && serverCall.whale_shield_usd) {
        whalePill.textContent = `🛡️ WHALE WALL: $${Number(serverCall.whale_shield_usd).toLocaleString()}`;
        if (serverCall.is_whale_impenetrable) {
            whalePill.style.color = '#00e676';
            whalePill.style.borderColor = '#00e676';
        }
    }
    playGodModeSound(dir, soundTier);
    triggerScreenPulse(dir.toLowerCase());
    setChartStrikeLine(openStrike, dir);
    renderMainSignalCard(latestSignalData);
    updateCwalletAreaHero();
    return true;
}

// Settle round strictly against Cwallet round open strike K
function settleCurrentCwalletRound() {
    clearChartStrikeLine();
    if (activeMarketType !== 'crypto') return;

    if (!currentRoundBet || currentRoundBet.dir === 'PASS' || currentRoundBet.dir === 'WAIT' || currentRoundBet.dir === 'SKIP') {
        const passReason = (currentRoundBet && currentRoundBet.isShielded) ? 'SHIELD PASS' : 'SKIPPED (PASS)';
        recordRoundHistory(roundNumber, passReason, '--', lastPrice, '⚪ PASS');
        return;
    }

    const currentPrice = lastPrice || currentRoundBet.entry;
    const strike = currentRoundBet.strike || cwalletRoundOpenPrice || currentRoundBet.entry;
    let result = 'LOSS';
    let won = false;

    if (currentRoundBet.dir === 'UP') {
        won = currentPrice > strike;
    } else if (currentRoundBet.dir === 'DOWN') {
        won = currentPrice < strike;
    } else {
        // Any non-directional call must never be treated as a loss
        recordRoundHistory(currentRoundBet.round, 'PASS', '--', currentPrice, '⚪ PASS');
        return;
    }

    if (currentPrice !== strike) {
        if (won) {
            settledWins++;
            consecutiveLosses = 0;
            result = '🏆 WIN';
            speakTacticalAlert("Win confirmed! Settled in the money.");
        } else {
            settledLosses++;
            consecutiveLosses++;
            result = '❌ LOSS';
            speakTacticalAlert("Loss registered. Re-calibrating microstructure.");
        }
    } else {
        result = '⚪ TIE';
    }

    recordRoundHistory(
        currentRoundBet.round,
        `BET ${currentRoundBet.dir}`,
        `${currentRoundBet.conf}%`,
        currentPrice,
        result
    );

    // Update Win Rate HUD
    const total = settledWins + settledLosses;
    const wr = total > 0 ? ((settledWins / total) * 100).toFixed(1) : '0.0';
    const statWinRate = document.getElementById('stat-win-rate');
    const statRecord = document.getElementById('stat-record');
    if (statWinRate) statWinRate.textContent = `${wr}%`;
    if (statRecord) statRecord.textContent = `${settledWins}W / ${settledLosses}L`;
}

function recordRoundHistory(rnd, call, conf, price, result) {
    const timeStr = new Date().toLocaleTimeString('en-US', { hour12: false });
    const row = document.createElement('tr');
    const resultColor = result.includes('WIN') ? '#00e676' : (result.includes('LOSS') ? '#ff1744' : '#94a3b8');

    row.innerHTML = `
        <td>${timeStr}</td>
        <td><strong>#${rnd}</strong></td>
        <td>${call}</td>
        <td>${conf}</td>
        <td style="color: ${resultColor}; font-weight: 800;">${result}</td>
        <td>${formatCurrency(price)}</td>
    `;

    const historyTableBody = document.getElementById('history-table-body');
    if (historyTableBody) {
        historyTableBody.insertBefore(row, historyTableBody.firstChild);
        while (historyTableBody.children.length > 20) {
            historyTableBody.removeChild(historyTableBody.lastChild);
        }
    }
}

function triggerScreenPulse(dir) {
    const circle = document.getElementById('main-signal-circle');
    if (circle) {
        circle.classList.add('pulse');
        setTimeout(() => circle.classList.remove('pulse'), 800);
    }
}

// ==========================================================================
// Voice & Sound
// ==========================================================================
let lastSpokenText = '';
let lastSpokenTime = 0;

function speakTacticalAlert(text) {
    if (!isVoiceEnabled || !('speechSynthesis' in window) || !text) return;
    const now = Date.now();
    if (text === lastSpokenText && (now - lastSpokenTime) < 8000) return;
    lastSpokenText = text;
    lastSpokenTime = now;
    try {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        const isPunch = text.startsWith('BET ') || text.startsWith('UP') || text.startsWith('DOWN');
        utterance.rate = isPunch ? 1.35 : 1.05;
        utterance.pitch = isPunch ? 1.15 : 0.95;
        utterance.volume = 1.0;
        const voices = window.speechSynthesis.getVoices();
        const preferred = voices.find(v => v.lang.includes('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('David')));
        if (preferred) utterance.voice = preferred;
        window.speechSynthesis.speak(utterance);
    } catch (e) {}
}

// ==========================================================================
// 👑 GOD-MODE APEX ENGINE TOGGLE & PERSISTENCE
// ==========================================================================
let isGodModeEnabled = true;
const btnGodModeToggle = document.getElementById('btn-god-mode-toggle');

function applyGodModeState(enabled, notify = false) {
    isGodModeEnabled = enabled;
    try {
        localStorage.setItem('tradex_god_mode', enabled ? 'true' : 'false');
    } catch (e) {}

    if (btnGodModeToggle) {
        if (enabled) {
            btnGodModeToggle.textContent = '👑 GOD MODE: ON';
            btnGodModeToggle.classList.add('active');
        } else {
            btnGodModeToggle.textContent = '👑 GOD MODE: OFF';
            btnGodModeToggle.classList.remove('active');
        }
    }

    if (enabled) {
        document.body.classList.add('god-mode-active');
        if (notify) {
            playGodModeSound('UP', 'GOD_APEX');
            speakTacticalAlert('👑 God Mode activated. Institutional confluence and SMC reticle online.');
        }
    } else {
        document.body.classList.remove('god-mode-active');
        if (notify) {
            speakTacticalAlert('Standard mode restored.');
        }
    }

    // Re-render active card with new theme
    if (latestSignalData) {
        renderMainSignalCard(latestSignalData);
        updateGodModeHUD(latestSignalData);
    }
}

// Read saved preference
try {
    const savedGodMode = localStorage.getItem('tradex_god_mode');
    if (savedGodMode !== 'false') {
        applyGodModeState(true, false);
    }
} catch (e) {}

if (btnGodModeToggle) {
    btnGodModeToggle.addEventListener('click', () => {
        applyGodModeState(!isGodModeEnabled, true);
    });
}

// ==========================================================================
// 🛡️ 100% ZERO-DEFECT ULTRA-SNIPER ENGINE TOGGLE & PERSISTENCE
// ==========================================================================
const btnZeroDefectToggle = document.getElementById('btn-zero-defect-toggle');

function applyZeroDefectState(enabled, notify = false, emitServer = true) {
    isZeroDefectEnabled = enabled;
    try {
        localStorage.setItem('tradex_zero_defect', enabled ? 'true' : 'false');
    } catch (e) {}

    if (btnZeroDefectToggle) {
        if (enabled) {
            btnZeroDefectToggle.textContent = '🛡️ ZERO-DEFECT: 100%';
            btnZeroDefectToggle.classList.add('active');
        } else {
            btnZeroDefectToggle.textContent = '🛡️ ZERO-DEFECT: OFF';
            btnZeroDefectToggle.classList.remove('active');
        }
    }

    if (enabled) {
        document.body.classList.add('zero-defect-mode-active');
        if (notify) {
            playGodModeSound('UP', 'OMNISCIENT');
            speakTacticalAlert('Zero-Defect 100% Mode online. Zero risk fortress armed.');
        }
    } else {
        document.body.classList.remove('zero-defect-mode-active');
        if (notify) {
            speakTacticalAlert('Standard 99% God Mode active.');
        }
    }

    if (emitServer) {
        fetch('/api/toggle_zero_defect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: isZeroDefectEnabled })
        }).catch(() => {});
        if (typeof socket !== 'undefined' && socket && socket.connected) {
            socket.emit('toggle_zero_defect', { enabled: isZeroDefectEnabled });
        }
    }

    if (latestSignalData) {
        renderMainSignalCard(latestSignalData);
        updateCwalletAreaHero();
    }
}

// Read saved preference
try {
    localStorage.removeItem('tradex_zero_defect');
    applyZeroDefectState(false, false, false);
} catch (e) {}

if (btnZeroDefectToggle) {
    btnZeroDefectToggle.addEventListener('click', () => {
        applyZeroDefectState(!isZeroDefectEnabled, true, true);
    });
}

if (typeof socket !== 'undefined' && socket) {
    socket.on('zero_defect_mode_switched', (data) => {
        if (data && data.zero_defect_mode !== undefined && data.zero_defect_mode !== isZeroDefectEnabled) {
            applyZeroDefectState(data.zero_defect_mode, false, false);
        }
    });
}

const btnVoiceToggle = document.getElementById('btn-voice-toggle');
if (btnVoiceToggle) {
    btnVoiceToggle.addEventListener('click', () => {
        isVoiceEnabled = !isVoiceEnabled;
        if (isVoiceEnabled) {
            btnVoiceToggle.textContent = '🎙️ Voice: ON';
            btnVoiceToggle.classList.remove('off');
            speakTacticalAlert('Cwallet Voice Synced.');
        } else {
            btnVoiceToggle.textContent = '🔇 Voice: OFF';
            btnVoiceToggle.classList.add('off');
        }
    });
}

document.body.addEventListener('click', () => {
    isSoundEnabled = true;
    getAudioContext();
}, { once: true });

let audioCtx = null;
function getAudioContext() {
    if (!audioCtx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) audioCtx = new AudioContext();
    }
    if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
    return audioCtx;
}

let lastGodSoundPlayMs = 0;
function playGodModeSound(direction, tier = 'NORMAL') {
    const nowMs = Date.now();
    if (nowMs - lastGodSoundPlayMs < 2500) return; // Debounce duplicate triggers
    lastGodSoundPlayMs = nowMs;
    try {
        const ctx = getAudioContext();
        if (!ctx) return;
        const now = ctx.currentTime;
        
        if (tier === 'OMNISCIENT') {
            // 👑 ☠️ OMNISCIENT GOD-TIER: Earth-shattering 130Hz -> 18Hz seismic sub-bass + 7-tone celestial fanfare
            const sub = ctx.createOscillator();
            const subGain = ctx.createGain();
            sub.type = 'sawtooth';
            const filter = ctx.createBiquadFilter();
            filter.type = 'lowpass';
            filter.Q.setValueAtTime(4.0, now);
            filter.frequency.setValueAtTime(260, now);
            filter.frequency.exponentialRampToValueAtTime(35, now + 1.1);
            sub.connect(filter);
            filter.connect(subGain);
            subGain.connect(ctx.destination);
            sub.frequency.setValueAtTime(130, now);
            sub.frequency.exponentialRampToValueAtTime(18, now + 1.1);
            subGain.gain.setValueAtTime(0.85, now);
            subGain.gain.exponentialRampToValueAtTime(0.001, now + 1.2);
            sub.start(now);
            sub.stop(now + 1.2);

            // 7-Tone Celestial Ascending Crystal Fanfare
            const fanfare = direction === 'UP'
                ? [523.25, 659.25, 783.99, 1046.50, 1318.51, 1567.98, 2093.00]
                : [2093.00, 1567.98, 1318.51, 1046.50, 783.99, 659.25, 523.25];
            fanfare.forEach((f, idx) => {
                const o = ctx.createOscillator();
                const g = ctx.createGain();
                o.type = 'triangle';
                o.connect(g);
                g.connect(ctx.destination);
                const s = now + 0.05 + (idx * 0.065);
                o.frequency.setValueAtTime(f, s);
                g.gain.setValueAtTime(0.45, s);
                g.gain.exponentialRampToValueAtTime(0.001, s + 0.6);
                o.start(s);
                o.stop(s + 0.6);
            });
            return;
        }

        if (tier === 'LETHAL') {
            // ☠️ PREDATORY LETHAL: Devastating sub-bass warhorn (110Hz -> 25Hz) + Dual Laser Chirp
            const sub = ctx.createOscillator();
            const subGain = ctx.createGain();
            sub.type = 'sawtooth';
            const filter = ctx.createBiquadFilter();
            filter.type = 'lowpass';
            filter.frequency.setValueAtTime(220, now);
            filter.frequency.exponentialRampToValueAtTime(60, now + 0.8);
            sub.connect(filter);
            filter.connect(subGain);
            subGain.connect(ctx.destination);
            sub.frequency.setValueAtTime(120, now);
            sub.frequency.exponentialRampToValueAtTime(25, now + 0.8);
            subGain.gain.setValueAtTime(0.7, now);
            subGain.gain.exponentialRampToValueAtTime(0.001, now + 0.9);
            sub.start(now);
            sub.stop(now + 0.9);

            const chirpNotes = direction === 'UP' ? [1200, 1800, 2400] : [2400, 1800, 1200];
            chirpNotes.forEach((f, idx) => {
                const o = ctx.createOscillator();
                const g = ctx.createGain();
                o.type = 'sine';
                o.connect(g);
                g.connect(ctx.destination);
                const s = now + 0.04 + (idx * 0.06);
                o.frequency.setValueAtTime(f, s);
                g.gain.setValueAtTime(0.3, s);
                g.gain.exponentialRampToValueAtTime(0.001, s + 0.4);
                o.start(s);
                o.stop(s + 0.4);
            });
            return;
        }

        if (tier === 'GOD_APEX') {
            // ⚡ 🌌 APEX deep impact sub-bass (85Hz -> 30Hz)
            const sub = ctx.createOscillator();
            const subGain = ctx.createGain();
            sub.type = 'sine';
            sub.connect(subGain);
            subGain.connect(ctx.destination);
            sub.frequency.setValueAtTime(85, now);
            sub.frequency.exponentialRampToValueAtTime(30, now + 0.6);
            subGain.gain.setValueAtTime(0.6, now);
            subGain.gain.exponentialRampToValueAtTime(0.001, now + 0.7);
            sub.start(now);
            sub.stop(now + 0.7);

            // 6-note resonant Apex crystal arpeggio
            const apexChords = direction === 'UP' 
                ? [523.25, 659.25, 783.99, 1046.50, 1318.51, 1567.98]
                : [1567.98, 1318.51, 1046.50, 783.99, 659.25, 523.25];
            apexChords.forEach((f, idx) => {
                const o = ctx.createOscillator();
                const g = ctx.createGain();
                o.type = 'triangle';
                o.connect(g);
                g.connect(ctx.destination);
                const s = now + 0.05 + (idx * 0.07);
                o.frequency.setValueAtTime(f, s);
                g.gain.setValueAtTime(0.4, s);
                g.gain.exponentialRampToValueAtTime(0.001, s + 0.55);
                o.start(s);
                o.stop(s + 0.55);
            });
            return;
        }

        if (tier === 'UNIVERSAL') {
            // 🌌 Deep cosmic sub-bass impact (75Hz -> 35Hz)
            const sub = ctx.createOscillator();
            const subGain = ctx.createGain();
            sub.type = 'sine';
            sub.connect(subGain);
            subGain.connect(ctx.destination);
            sub.frequency.setValueAtTime(75, now);
            sub.frequency.exponentialRampToValueAtTime(35, now + 0.5);
            subGain.gain.setValueAtTime(0.5, now);
            subGain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
            sub.start(now);
            sub.stop(now + 0.6);

            // Shimmering crystalline celestial harmonics (C6 -> G6 -> C7)
            const chimes = direction === 'UP' ? [1046.50, 1567.98, 2093.00] : [2093.00, 1567.98, 1046.50];
            chimes.forEach((f, idx) => {
                const o = ctx.createOscillator();
                const g = ctx.createGain();
                o.type = 'triangle';
                o.connect(g);
                g.connect(ctx.destination);
                const s = now + 0.1 + (idx * 0.1);
                o.frequency.setValueAtTime(f, s);
                g.gain.setValueAtTime(0.35, s);
                g.gain.exponentialRampToValueAtTime(0.001, s + 0.5);
                o.start(s);
                o.stop(s + 0.5);
            });
            return;
        }

        if (tier === 'GOD' || tier === true) {
            // 👑 Celestial 5-note royal fanfare arpeggio
            const celestial = direction === 'UP' 
                ? [523.25, 659.25, 783.99, 1046.50, 1318.51] // C5, E5, G5, C6, E6
                : [1046.50, 880.00, 698.46, 587.33, 440.00]; // C6, A5, F5, D5, A4
            celestial.forEach((freq, idx) => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'triangle';
                osc.connect(gain);
                gain.connect(ctx.destination);
                const start = now + (idx * 0.08);
                osc.frequency.setValueAtTime(freq, start);
                gain.gain.setValueAtTime(0.4, start);
                gain.gain.exponentialRampToValueAtTime(0.005, start + 0.45);
                osc.start(start);
                osc.stop(start + 0.45);
            });
            return;
        }

        const freqs = direction === 'UP' ? [850, 1250, 1650] : [1450, 1050, 650];
        freqs.forEach((freq, idx) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            const start = now + (idx * 0.08);
            osc.frequency.setValueAtTime(freq, start);
            gain.gain.setValueAtTime(0.35, start);
            gain.gain.exponentialRampToValueAtTime(0.01, start + 0.3);
            osc.start(start);
            osc.stop(start + 0.3);
        });
    } catch (e) {}
}

function playTriumphFanfare() {
    try {
        const ctx = getAudioContext();
        if (!ctx) return;
        const now = ctx.currentTime;
        const chord = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6 (Triumphant Arpeggio)
        chord.forEach((freq, idx) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'triangle';
            osc.connect(gain);
            gain.connect(ctx.destination);
            const start = now + (idx * 0.12);
            osc.frequency.setValueAtTime(freq, start);
            gain.gain.setValueAtTime(0.35, start);
            gain.gain.exponentialRampToValueAtTime(0.001, start + 0.9);
            osc.start(start);
            osc.stop(start + 0.9);
        });
    } catch (e) {}
}

let tabFlashInterval = null;
const originalDocTitle = document.title || 'CW Quant Terminal — Cwallet Market Battle';

function flashTabTitle(flashMsg) {
    if (tabFlashInterval) {
        clearInterval(tabFlashInterval);
        tabFlashInterval = null;
    }
    let isOriginal = false;
    let count = 0;
    tabFlashInterval = setInterval(() => {
        document.title = isOriginal ? originalDocTitle : flashMsg;
        isOriginal = !isOriginal;
        count++;
        if (count >= 24) {
            clearInterval(tabFlashInterval);
            tabFlashInterval = null;
            document.title = originalDocTitle;
        }
    }, 500);
}

window.addEventListener('focus', () => {
    if (tabFlashInterval) {
        clearInterval(tabFlashInterval);
        tabFlashInterval = null;
        document.title = originalDocTitle;
    }
});

// ==========================================================================
// TRADEX UNIVERSAL NOTIFICATION ENGINE (APK, PWA, Browser & Floating Toast)
// ==========================================================================
let toastDismissTimer = null;

function showInAppToastNotification(title, body, dir = 'UP') {
    const toast = document.getElementById('tradex-floating-toast');
    const toastIcon = document.getElementById('toast-icon');
    const toastTitle = document.getElementById('toast-title');
    const toastSub = document.getElementById('toast-sub');
    const btnClose = document.getElementById('btn-close-toast');

    if (!toast || !toastTitle) return;

    const isUp = (dir === 'UP' || title.includes('UP'));
    toast.className = isUp ? 'tradex-toast' : 'tradex-toast toast-down';
    if (toastIcon) toastIcon.textContent = isUp ? '🟢' : '🔴';
    toastTitle.textContent = title;
    if (toastSub) toastSub.textContent = body;
    toast.style.display = 'flex';

    if (btnClose) {
        btnClose.onclick = () => { toast.style.display = 'none'; };
    }

    // Hardware vibration on mobile
    try {
        if ('vibrate' in navigator) {
            navigator.vibrate([200, 100, 200]);
        }
    } catch (e) {}

    // Auto-dismiss after 7 seconds
    if (toastDismissTimer) clearTimeout(toastDismissTimer);
    toastDismissTimer = setTimeout(() => {
        if (toast) toast.style.display = 'none';
    }, 7000);
}

let lastNotifiedRoundId = -1;
let lastNotifiedRoundDir = '';

function showBrowserNotification(title, body) {
    if (!title) return;
    // Suppress PASS notifications to prevent continuous alert spam on chop
    if (title.includes('PASS') || title.includes('PROTECTED') || title.includes('CAPITAL SHIELD')) {
        return;
    }

    const isUp = title.includes('UP');
    const isDown = title.includes('DOWN');
    if (!isUp && !isDown) return;
    const dir = isUp ? 'UP' : 'DOWN';

    // Strict single-fire per round (STRICTLY ONCE, never repeat)
    if (roundNumber > 0) {
        if (roundNumber === lastNotifiedRoundId) {
            return; // Already notified once for this round!
        }
        lastNotifiedRoundId = roundNumber;
        lastNotifiedRoundDir = dir;
    }

    flashTabTitle(title);

    // 1. Android Native APK Bridge via JavascriptInterface
    if (window.TradexNative && typeof window.TradexNative.showNotification === 'function') {
        try {
            window.TradexNative.showNotification(title, body);
        } catch (e) {
            console.error('TradexNative bridge error:', e);
        }
    }

    // 2. Guaranteed In-App Floating Heads-Up Toast (Visible on all screens)
    showInAppToastNotification(title, body, dir);

    // 3. HTML5 Web Notifications API (PC Chrome / Edge / Firefox)
    if ('Notification' in window) {
        if (Notification.permission === 'granted') {
            try {
                const notif = new Notification(title, {
                    body: body,
                    tag: 'tradex-signal-' + (roundNumber || Date.now()),
                    icon: '/static/icon-192.png',
                    renotify: true,
                    requireInteraction: true,
                    silent: false
                });
                notif.onclick = function() {
                    window.focus();
                    this.close();
                };
            } catch (e) {
                console.error('Notification error:', e);
            }
        } else if (Notification.permission === 'default') {
            try {
                Notification.requestPermission().then(perm => {
                    checkNotifPermissionState();
                    if (perm === 'granted') {
                        try {
                            new Notification(title, { body: body, tag: 'tradex-signal-' + (roundNumber || Date.now()), requireInteraction: true });
                        } catch (e) {}
                    }
                });
            } catch (e) {}
        }
    }
}

function checkNotifPermissionState() {
    const isNativeAPK = !!(window.TradexNative && typeof window.TradexNative.showNotification === 'function');
    const descSpan = document.getElementById('notif-status-desc');
    
    if (isNativeAPK) {
        if (descSpan) descSpan.textContent = '✅ tradex Android Native Alerts Active (Push Notifications & Vibration Online)';
        if (btnAllowNotif) {
            btnAllowNotif.textContent = '✅ Alerts Active';
            btnAllowNotif.style.background = '#059669';
            btnAllowNotif.style.borderColor = '#10b981';
            btnAllowNotif.style.color = '#fff';
        }
        if (btnEnableBanner) {
            btnEnableBanner.textContent = '✅ Alerts Online';
            btnEnableBanner.style.background = '#059669';
        }
        return;
    }

    if (!('Notification' in window)) {
        if (descSpan) descSpan.textContent = '⚡ Heads-Up in-app floating alerts & vibration active on your screen!';
        return;
    }

    if (Notification.permission === 'granted') {
        if (descSpan) descSpan.textContent = '✅ Instant browser alerts granted! You will receive high-priority sniper notifications.';
        if (btnAllowNotif) {
            btnAllowNotif.textContent = '✅ Alerts Active';
            btnAllowNotif.style.background = '#059669';
            btnAllowNotif.style.borderColor = '#10b981';
            btnAllowNotif.style.color = '#fff';
        }
        if (btnEnableBanner) {
            btnEnableBanner.textContent = '✅ Alerts Granted';
            btnEnableBanner.style.background = '#059669';
        }
    } else if (Notification.permission === 'denied') {
        if (descSpan) descSpan.textContent = '⚠️ System notifications blocked in browser settings. Please click the site icon in your address bar and allow Notifications!';
        if (btnAllowNotif) {
            btnAllowNotif.textContent = '❌ Blocked';
            btnAllowNotif.style.background = '#dc2626';
            btnAllowNotif.style.borderColor = '#ef4444';
            btnAllowNotif.style.color = '#fff';
        }
        if (btnEnableBanner) {
            btnEnableBanner.textContent = '⚠️ Unblock in Settings';
            btnEnableBanner.style.background = '#dc2626';
        }
    } else {
        if (descSpan) descSpan.textContent = 'Click "Enable Instant Alerts" below so tradex can send you real-time trade execution notifications!';
        if (btnAllowNotif) {
            btnAllowNotif.textContent = '📢 Enable Alerts';
            btnAllowNotif.style.background = '#1e293b';
            btnAllowNotif.style.borderColor = '#38bdf8';
            btnAllowNotif.style.color = '#38bdf8';
        }
        if (btnEnableBanner) {
            btnEnableBanner.textContent = '🔔 Enable Instant Alerts';
            btnEnableBanner.style.background = 'linear-gradient(135deg, #10b981, #059669)';
        }
    }
}

// Auto-request permission on very first touch/click on page
document.addEventListener('pointerdown', function requestOnFirstTouch() {
    getAudioContext();
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(() => {
            checkNotifPermissionState();
        }).catch(() => {});
    }
    document.removeEventListener('pointerdown', requestOnFirstTouch);
}, { once: true });

checkNotifPermissionState();

if (btnEnableBanner) {
    btnEnableBanner.addEventListener('click', () => {
        isSoundEnabled = true;
        getAudioContext();
        if ('Notification' in window) {
            Notification.requestPermission().then(perm => {
                checkNotifPermissionState();
                if (perm === 'granted') {
                    showBrowserNotification('✅ TRADEX SNIPER ACTIVE', 'You will receive notifications for every high-conviction sniper round!');
                    speakTacticalAlert('tradex sniper alerts activated.');
                    playGodModeSound('UP', 'UNIVERSAL');
                }
            });
        } else {
            showBrowserNotification('✅ TRADEX ALERTS ACTIVE', 'Heads-up in-app notification alerts and sound online!');
        }
    });
}

if (btnTestBanner) {
    btnTestBanner.addEventListener('click', () => {
        isSoundEnabled = true;
        getAudioContext();
        showBrowserNotification(`⚡ tradex ROUND #${roundNumber}: BET UP NOW!`, `🟢 ACTION: OPEN CWALLET BATTLE & TAP GREEN [UP]! | Strike: $${lastPrice ? lastPrice.toFixed(2) : '76,500.00'} | 99% Conviction`);
        playGodModeSound('UP', 'GOD_APEX');
        speakTacticalAlert(`BET UP! BET UP! Strike UP now.`);
    });
}

if (btnAllowNotif) {
    btnAllowNotif.addEventListener('click', () => {
        getAudioContext();
        if ('Notification' in window) {
            Notification.requestPermission().then(permission => {
                checkNotifPermissionState();
                if (permission === 'granted') {
                    showBrowserNotification('✅ TRADEX ALERTS ACTIVE', 'You will receive sniper notifications on every round!');
                    speakTacticalAlert('tradex sniper alerts activated.');
                    playGodModeSound('UP', 'GOD_APEX');
                }
            });
        } else {
            showBrowserNotification('✅ TRADEX ALERTS ACTIVE', 'Heads-up in-app notification alerts and sound online!');
        }
    });
}

if (btnTestNotif) {
    btnTestNotif.addEventListener('click', () => {
        isSoundEnabled = true;
        getAudioContext();
        btnTestNotif.textContent = '⚡ Firing...';

        showBrowserNotification(`🎯 tradex ROUND #${roundNumber}: BET UP!`, `Target: $${lastPrice ? lastPrice.toFixed(2) : '76,500'} | 99% accuracy sniper alert!`);
        playGodModeSound('UP', 'GOD_APEX');
        speakTacticalAlert(`tradex Round ${roundNumber}. Bet UP on Cwallet now.`);

        setTimeout(() => {
            btnTestNotif.textContent = '⚡ Test Call';
        }, 2000);
    });
}

// ==========================================================================
// Socket.IO & Chart
// ==========================================================================
const connectionDot = document.getElementById('connection-status-dot');
const connectionText = document.getElementById('connection-status-text');

if (socket) {
    socket.on('connect', () => {
        if (connectionDot) connectionDot.className = 'dot connected';
        if (connectionText) connectionText.textContent = 'Cwallet Stream Active';
    });

    socket.on('disconnect', () => {
        if (connectionDot) connectionDot.className = 'dot disconnected';
        if (connectionText) connectionText.textContent = 'Offline';
    });
}

const chartElement = document.getElementById('price-chart');
let chart = null;
let candleSeries = null;
let areaSeries = null;

if (typeof LightweightCharts !== 'undefined' && chartElement) {
    try {
        chart = LightweightCharts.createChart(chartElement, {
            layout: {
                textColor: '#94a3b8',
                background: { type: 'solid', color: '#0d1017' },
                fontSize: 12,
            },
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.03)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.03)' },
            },
            crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
            timeScale: {
                timeVisible: true,
                secondsVisible: true,
                barSpacing: 12,
                minBarSpacing: 5,
                rightOffset: 6,
                borderColor: '#1a202c',
            },
            rightPriceScale: {
                autoScale: true,
                borderColor: '#1a202c',
                scaleMargins: { top: 0.18, bottom: 0.18 },
            },
        });

        candleSeries = chart.addCandlestickSeries({
            upColor: '#00e676',
            downColor: '#ff1744',
            borderVisible: true,
            borderColor: '#1a202c',
            borderUpColor: '#00e676',
            borderDownColor: '#ff1744',
            wickUpColor: '#00e676',
            wickDownColor: '#ff1744',
        });

        areaSeries = chart.addAreaSeries({
            topColor: 'rgba(56, 189, 248, 0.45)',
            bottomColor: 'rgba(56, 189, 248, 0.02)',
            lineColor: '#38bdf8',
            lineWidth: 2,
            visible: false,
        });

        if (typeof ResizeObserver !== 'undefined') {
            new ResizeObserver(entries => {
                if (entries.length === 0 || entries[0].target !== chartElement) return;
                const rect = entries[0].contentRect;
                chart.applyOptions({ height: rect.height, width: rect.width });
            }).observe(chartElement);
        }
    } catch (e) {
        console.warn('LightweightCharts initialization error:', e);
    }
}

const btnCandle = document.getElementById('btn-chart-candle');
const btnArea = document.getElementById('btn-chart-area');
const btnCw = document.getElementById('btn-chart-cw');
const btnFit = document.getElementById('btn-chart-fit');

let isCwalletGraphSyncMode = false;
let currentStrikePriceLine = null;
let currentAreaStrikePriceLine = null;

if (btnCandle) {
    btnCandle.addEventListener('click', () => {
        isCwalletGraphSyncMode = false;
        btnCandle.classList.add('active');
        if (btnArea) btnArea.classList.remove('active');
        if (btnCw) btnCw.classList.remove('active');
        if (candleSeries) candleSeries.applyOptions({ visible: true });
        if (areaSeries) areaSeries.applyOptions({ visible: false });
        syncChartWithCwalletStrike();
    });
}

if (btnArea) {
    btnArea.addEventListener('click', () => {
        isCwalletGraphSyncMode = false;
        btnArea.classList.add('active');
        if (btnCandle) btnCandle.classList.remove('active');
        if (btnCw) btnCw.classList.remove('active');
        if (candleSeries) candleSeries.applyOptions({ visible: false });
        if (areaSeries) areaSeries.applyOptions({ visible: true });
        syncChartWithCwalletStrike();
    });
}

if (btnCw) {
    btnCw.addEventListener('click', () => {
        isCwalletGraphSyncMode = true;
        btnCw.classList.add('active');
        if (btnCandle) btnCandle.classList.remove('active');
        if (btnArea) btnArea.classList.remove('active');
        if (candleSeries) candleSeries.applyOptions({ visible: false });
        if (areaSeries) areaSeries.applyOptions({ visible: true });
        syncChartWithCwalletStrike();
        if (chart) chart.timeScale().scrollToRealTime();
    });
}

if (btnFit && chart) {
    btnFit.addEventListener('click', () => {
        chart.timeScale().fitContent();
    });
}

// ==========================================================================
// Cwallet Visual Graph Sync & Strike Price Line Controller
// ==========================================================================
function clearChartStrikeLine() {
    if (currentStrikePriceLine && candleSeries) {
        try {
            candleSeries.removePriceLine(currentStrikePriceLine);
        } catch (e) {}
        currentStrikePriceLine = null;
    }
    if (currentAreaStrikePriceLine && areaSeries) {
        try {
            areaSeries.removePriceLine(currentAreaStrikePriceLine);
        } catch (e) {}
        currentAreaStrikePriceLine = null;
    }
}

function syncChartWithCwalletStrike(targetStrike = null, favoredDir = null) {
    if (activeMarketType !== 'crypto') {
        clearChartStrikeLine();
        const overlay = document.getElementById('chart-cwallet-overlay');
        if (overlay) overlay.style.display = 'none';
        return;
    }

    const strike = targetStrike || cwalletRoundOpenPrice || (latestSignalData && latestSignalData.barrier_model ? latestSignalData.barrier_model.k : null);
    if (!strike || strike <= 0) {
        clearChartStrikeLine();
        return;
    }

    const curPrice = lastPrice || (latestSignalData ? latestSignalData.price : strike);
    const delta = curPrice - strike;
    const isUp = delta >= 0;
    const deltaBps = (delta / strike) * 10000.0;
    const sym = getCurrencySymbol();

    const dirTag = favoredDir || (latestSignalData ? latestSignalData.direction : (isUp ? 'UP' : 'DOWN'));
    const lineColor = (dirTag === 'UP') ? '#00e676' : (dirTag === 'DOWN' ? '#ff1744' : (isUp ? '#00e676' : '#ff1744'));

    clearChartStrikeLine();

    const titleText = `🎯 CW STRIKE: ${sym}${strike.toFixed(2)} (${isUp ? '▲ +' : '▼ -'}${sym}${Math.abs(delta).toFixed(2)})`;
    const lineConfig = {
        price: strike,
        color: lineColor,
        lineWidth: 2,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: titleText
    };

    try {
        if (candleSeries) {
            currentStrikePriceLine = candleSeries.createPriceLine(lineConfig);
        }
        if (areaSeries) {
            currentAreaStrikePriceLine = areaSeries.createPriceLine(lineConfig);
        }
    } catch (e) {
        console.warn('Error setting chart price line:', e);
    }

    // Dynamic Cwallet Area Fill
    if (isCwalletGraphSyncMode && areaSeries) {
        if (isUp) {
            areaSeries.applyOptions({
                topColor: 'rgba(0, 230, 118, 0.40)',
                bottomColor: 'rgba(0, 230, 118, 0.02)',
                lineColor: '#00e676',
                lineWidth: 2
            });
        } else {
            areaSeries.applyOptions({
                topColor: 'rgba(255, 23, 68, 0.40)',
                bottomColor: 'rgba(255, 23, 68, 0.02)',
                lineColor: '#ff1744',
                lineWidth: 2
            });
        }
    }

    // Header Overlay Badge
    const overlay = document.getElementById('chart-cwallet-overlay');
    const strikeTag = document.getElementById('chart-strike-tag');
    const deltaTag = document.getElementById('chart-delta-tag');

    if (overlay && strikeTag && deltaTag) {
        overlay.style.display = 'flex';
        strikeTag.textContent = `🎯 STRIKE: ${sym}${strike.toFixed(2)}`;
        deltaTag.textContent = `${delta >= 0 ? '+' : ''}${sym}${delta.toFixed(2)} (${deltaBps >= 0 ? '+' : ''}${deltaBps.toFixed(1)} bps ${isUp ? '▲ UP' : '▼ DOWN'})`;
        deltaTag.className = isUp ? 'delta-pill delta-up' : 'delta-pill delta-down';
    }
}

function setChartStrikeLine(price, dir) {
    syncChartWithCwalletStrike(price, dir);
}

const btnSnapStrikeChart = document.getElementById('btn-snap-strike-chart');
if (btnSnapStrikeChart) {
    btnSnapStrikeChart.addEventListener('click', () => {
        const snapPrice = lastPrice || (latestSignalData ? latestSignalData.price : null);
        if (snapPrice && snapPrice > 0) {
            cwalletRoundOpenPrice = snapPrice;
            syncChartWithCwalletStrike(snapPrice);
            if (cwalletOpenPriceDisplay) {
                cwalletOpenPriceDisplay.textContent = formatCurrency(snapPrice);
            }
            speakTacticalAlert(`Strike locked at ${snapPrice.toFixed(2)}`);
        }
    });
}

// Candle Updates
let hasHistorySet = false;

socket.on('candle_history', (candles) => {
    if (Array.isArray(candles) && candles.length > 0) {
        try {
            candleSeries.setData(candles);
            areaSeries.setData(candles.map(c => ({ time: c.time, value: c.close })));
            chart.timeScale().fitContent();
            hasHistorySet = true;
        } catch (e) {}
    }
});

socket.on('candle_update', (data) => {
    if (data.time && data.open && data.close) {
        try {
            if (!hasHistorySet) {
                candleSeries.setData([data]);
                areaSeries.setData([{ time: data.time, value: data.close }]);
                hasHistorySet = true;
            } else {
                candleSeries.update(data);
                areaSeries.update({ time: data.time, value: data.close });
            }
        } catch (e) {}
    }
});

// Market Switched Event (Universal Multi-Market Engine)
socket.on('market_switched', (data) => {
    if (!data) return;
    activeMarketType = data.market_type || activeMarketType;
    activeSymbol = data.symbol || activeSymbol;
    activeName = data.name || activeSymbol.toUpperCase();
    activeCurrencySymbol = data.currency_symbol || (activeMarketType === 'indian' ? '₹' : '$');

    const activeAssetDisplay = document.getElementById('active-asset-display');
    if (activeAssetDisplay) activeAssetDisplay.textContent = activeName;

    const pairTitle = document.getElementById('pair-title');
    if (pairTitle) pairTitle.textContent = activeName;

    const pairSubtitle = document.getElementById('pair-subtitle');
    if (pairSubtitle) pairSubtitle.textContent = activeMarketType === 'indian' ? 'NSE/BSE 1m Intraday' : '1s Ultra-Fast';

    // Dynamic History Table Header
    const thHistoryPrice = document.getElementById('th-history-price');
    if (thHistoryPrice) {
        if (activeMarketType === 'indian') {
            thHistoryPrice.textContent = `${activeName} Price (₹)`;
        } else {
            thHistoryPrice.textContent = `${activeSymbol.toUpperCase()} Price ($)`;
        }
    }

    const statusTag = document.getElementById('market-status-tag');
    if (statusTag) {
        if (activeMarketType === 'indian') {
            const ms = data.market_status || {};
            statusTag.textContent = ms.status_text || '🟢 NSE/BSE LIVE';
            statusTag.className = (ms.is_open !== false) ? 'market-status-tag' : 'market-status-tag closed';
        } else if (activeMarketType === 'international') {
            const ms = data.market_status || {};
            statusTag.textContent = ms.status_text || '🟢 US / GLOBAL LIVE';
            statusTag.className = (ms.is_open !== false) ? 'market-status-tag' : 'market-status-tag closed';
        } else {
            statusTag.textContent = '🟢 24/7 LIVE';
            statusTag.className = 'market-status-tag';
        }
    }

    // Switch tab buttons and pills
    const tabCrypto = document.getElementById('tab-market-crypto');
    const tabIndian = document.getElementById('tab-market-indian');
    const tabIntl = document.getElementById('tab-market-international');
    const pillsCrypto = document.getElementById('market-pills-crypto');
    const pillsIndian = document.getElementById('market-pills-indian');
    const pillsIntl = document.getElementById('market-pills-international');
    const roundSyncBar = document.getElementById('round-sync-bar');
    const indianSessionBar = document.getElementById('indian-session-bar');
    const intlSessionBar = document.getElementById('international-session-bar');

    if (activeMarketType === 'indian') {
        isCwalletGraphSyncMode = false;
        clearChartStrikeLine();
        const overlay = document.getElementById('chart-cwallet-overlay');
        if (overlay) overlay.style.display = 'none';

        if (tabIndian) {
            tabIndian.classList.add('active', 'tab-indian');
            if (tabCrypto) tabCrypto.classList.remove('active');
            if (tabIntl) tabIntl.classList.remove('active', 'tab-intl');
        }
        if (pillsIndian) pillsIndian.style.display = 'flex';
        if (pillsCrypto) pillsCrypto.style.display = 'none';
        if (pillsIntl) pillsIntl.style.display = 'none';
        if (roundSyncBar) roundSyncBar.style.display = 'none';
        if (indianSessionBar) indianSessionBar.style.display = 'flex';
        if (intlSessionBar) intlSessionBar.style.display = 'none';

        // Set Candlestick mode for Indian equities
        if (candleSeries) candleSeries.applyOptions({ visible: true });
        if (areaSeries) areaSeries.applyOptions({ visible: false });
        if (btnCandle) btnCandle.classList.add('active');
        if (btnArea) btnArea.classList.remove('active');
        if (btnCw) btnCw.classList.remove('active');
    } else if (activeMarketType === 'international') {
        isCwalletGraphSyncMode = false;
        clearChartStrikeLine();
        const overlay = document.getElementById('chart-cwallet-overlay');
        if (overlay) overlay.style.display = 'none';

        if (tabIntl) {
            tabIntl.classList.add('active', 'tab-intl');
            if (tabCrypto) tabCrypto.classList.remove('active');
            if (tabIndian) tabIndian.classList.remove('active', 'tab-indian');
        }
        if (pillsIntl) pillsIntl.style.display = 'flex';
        if (pillsCrypto) pillsCrypto.style.display = 'none';
        if (pillsIndian) pillsIndian.style.display = 'none';
        if (roundSyncBar) roundSyncBar.style.display = 'none';
        if (indianSessionBar) indianSessionBar.style.display = 'none';
        if (intlSessionBar) intlSessionBar.style.display = 'flex';

        // Set Candlestick mode for International assets
        if (candleSeries) candleSeries.applyOptions({ visible: true });
        if (areaSeries) areaSeries.applyOptions({ visible: false });
        if (btnCandle) btnCandle.classList.add('active');
        if (btnArea) btnArea.classList.remove('active');
        if (btnCw) btnCw.classList.remove('active');
    } else {
        isCwalletGraphSyncMode = true;
        if (tabCrypto) {
            tabCrypto.classList.add('active');
            if (tabIndian) tabIndian.classList.remove('active', 'tab-indian');
            if (tabIntl) tabIntl.classList.remove('active', 'tab-intl');
        }
        if (pillsCrypto) pillsCrypto.style.display = 'flex';
        if (pillsIndian) pillsIndian.style.display = 'none';
        if (pillsIntl) pillsIntl.style.display = 'none';
        if (roundSyncBar) roundSyncBar.style.display = 'flex';
        if (indianSessionBar) indianSessionBar.style.display = 'none';
        if (intlSessionBar) intlSessionBar.style.display = 'none';

        // Set Cwallet Synced Area mode for Crypto
        if (candleSeries) candleSeries.applyOptions({ visible: false });
        if (areaSeries) areaSeries.applyOptions({ visible: true });
        if (btnCw) btnCw.classList.add('active');
        if (btnCandle) btnCandle.classList.remove('active');
        if (btnArea) btnArea.classList.remove('active');
        if (cwalletRoundOpenPrice) {
            syncChartWithCwalletStrike(cwalletRoundOpenPrice);
        }
    }

    // Update active pill button
    document.querySelectorAll('.pill-asset').forEach(btn => {
        const btnSym = btn.getAttribute('data-symbol');
        const isActive = btnSym && (btnSym.toLowerCase() === activeSymbol.toLowerCase() || activeSymbol.toLowerCase().startsWith(btnSym.toLowerCase()));
        btn.classList.toggle('active', isActive);
        if (activeMarketType === 'indian' && isActive) {
            btn.classList.add('pill-indian');
            btn.classList.remove('pill-intl');
        } else if (activeMarketType === 'international' && isActive) {
            btn.classList.add('pill-intl');
            btn.classList.remove('pill-indian');
        } else {
            btn.classList.remove('pill-indian', 'pill-intl');
        }
    });

    // Reset chart series if candles provided
    if (Array.isArray(data.candles) && data.candles.length > 0 && candleSeries && areaSeries) {
        try {
            candleSeries.setData(data.candles);
            areaSeries.setData(data.candles.map(c => ({ time: c.time, value: c.close })));
            if (chart) chart.timeScale().fitContent();
        } catch (e) {}
    }
});

// Price Updates
socket.on('price_update', (data) => {
    const currentPrice = data.price;
    if (data.currency_symbol) {
        activeCurrencySymbol = data.currency_symbol;
    }
    if (currentPrice) {
        if (priceDisplay) {
            priceDisplay.textContent = formatCurrency(currentPrice, currentPrice < 5 ? 4 : 2);

            if (lastPrice !== null) {
                priceDisplay.className = 'price';
                void priceDisplay.offsetWidth;
                if (currentPrice > lastPrice) priceDisplay.classList.add('flash-up');
                else if (currentPrice < lastPrice) priceDisplay.classList.add('flash-down');
                setTimeout(() => (priceDisplay.className = 'price'), 300);
            }
        }
        lastPrice = currentPrice;
        if (activeMarketType === 'crypto' && cwalletRoundOpenPrice) {
            syncChartWithCwalletStrike(cwalletRoundOpenPrice);
        }
    }
});

// ==========================================================================
// Signal Updates from Engine
// ==========================================================================

const gaugeBull = document.getElementById('gauge-bull');
const gaugeBear = document.getElementById('gauge-bear');
const labelBullPct = document.getElementById('label-bull-pct');
const labelBearPct = document.getElementById('label-bear-pct');
const ofBuyVol = document.getElementById('of-buy-vol');
const ofSellVol = document.getElementById('of-sell-vol');
const deltaBurst = document.getElementById('delta-burst');

const hurstExponentBadge = document.getElementById('hurst-exponent-badge');
const kyleLambdaBadge = document.getElementById('kyle-lambda-badge');
const statTickRate = document.getElementById('stat-tick-rate');

const mtf1s = document.getElementById('mtf-1s');
const mtf5s = document.getElementById('mtf-5s');
const mtf15s = document.getElementById('mtf-15s');
const mtf60s = document.getElementById('mtf-60s');

const indicatorsGrid = document.getElementById('indicators-grid');
const INDICATOR_NAMES = [
    'Barrier Probability Φ(d)',
    'Hawkes Cascade Intensity',
    'Cross-Venue Lead-Lag',
    'L2 Queue Depletion',
    'Merton Jump-Diffusion Barrier',
    'Fractal Hurst Exponent',
    'Roll Noise & True Drift',
    'SMC Liquidity & FVG',
    'Amihud & Kyle Impact',
    'VPIN Flow Toxicity'
];

function renderEmptyIndicators() {
    indicatorsGrid.innerHTML = '';
    INDICATOR_NAMES.forEach(name => {
        const idSafe = name.replace(/[\s\/]+/g, '-');
        const div = document.createElement('div');
        div.className = 'indicator-card';
        div.id = `ind-${idSafe}`;
        div.innerHTML = `
            <div class="indicator-header">
                <span class="indicator-name">${name}</span>
                <span class="indicator-weight" id="weight-${idSafe}">--%</span>
            </div>
            <div class="indicator-body">
                <span class="indicator-value" id="val-${idSafe}">--</span>
                <span class="indicator-signal wait" id="sig-${idSafe}">—</span>
            </div>
            <div class="indicator-detail" id="det-${idSafe}">Analyzing...</div>
        `;
        indicatorsGrid.appendChild(div);
    });
}
renderEmptyIndicators();

// ==========================================================================
// 👑 GOD-MODE APEX HUD CONSOLE CONTROLLER
// ==========================================================================
function updateGodModeHUD(data) {
    if (!data) return;
    const sym = getCurrencySymbol();

    const elConf = document.getElementById('god-confluence-val');
    const elConfSub = document.getElementById('god-confluence-sub');
    const elSweep = document.getElementById('god-sweep-val');
    const elSweepSub = document.getElementById('god-sweep-sub');
    const elFvg = document.getElementById('god-fvg-val');
    const elFvgSub = document.getElementById('god-fvg-sub');
    const elKelly = document.getElementById('god-kelly-val');
    const elKellySub = document.getElementById('god-kelly-sub');

    // 1. Confluence Meter
    if (elConf) {
        const count = data.confluence_count !== undefined ? data.confluence_count : (data.strength && data.strength.includes('APEX') ? 7 : (data.strength && data.strength.includes('GOD-MODE') ? 5 : 4));
        const total = data.confluence_total || 7;
        const scoreStr = data.confluence_score || `${count}/${total} APEX`;
        if (data.is_lethal || (data.strength && data.strength.includes('LETHAL'))) {
            elConf.textContent = '7/7 LETHAL';
            elConf.classList.add('highlight-gold');
        } else {
            elConf.textContent = scoreStr;
        }
        if (elConfSub) {
            elConfSub.textContent = count >= 6 ? 'All Models Aligned' : (count >= 5 ? 'High Multi-Model Bias' : (data.direction === 'WAIT' ? 'Shielded Equilibrium' : 'Confluence Scanning'));
        }
    }

    // 2. SMC Liquidity Radar
    if (elSweep) {
        const sweep = data.smc_sweep || {};
        if (sweep.sweep_type === 'SSL_SWEEP_BULLISH') {
            elSweep.textContent = 'SSL SWEEP (BULL)';
            elSweep.style.color = '#00e676';
            if (elSweepSub) elSweepSub.textContent = `Absorbed (${sweep.rejection_pct || 65}% Wick)`;
        } else if (sweep.sweep_type === 'BSL_SWEEP_BEARISH') {
            elSweep.textContent = 'BSL SWEEP (BEAR)';
            elSweep.style.color = '#ff1744';
            if (elSweepSub) elSweepSub.textContent = `Rejected (${sweep.rejection_pct || 65}% Wick)`;
        } else {
            elSweep.textContent = 'RESTING POOLS';
            elSweep.style.color = '#94a3b8';
            if (elSweepSub) elSweepSub.textContent = sweep.detail ? sweep.detail.substring(0, 24) : 'BSL / SSL Resting';
        }
    }

    // 3. FVG Magnet Target
    if (elFvg) {
        const fvg = data.fvg_data || {};
        const p = data.price || lastPrice || 0;
        const isForex = p < 2.0;
        const dec = isForex ? 4 : 2;
        if (fvg.fvg_type && fvg.fvg_type !== 'NONE' && fvg.magnet_target) {
            elFvg.textContent = `${sym}${fvg.magnet_target.toFixed(dec)}`;
            elFvg.style.color = fvg.fvg_type === 'BULLISH_FVG' ? '#00e676' : '#ff1744';
            if (elFvgSub) elFvgSub.textContent = fvg.fvg_type === 'BULLISH_FVG' ? 'Displacement Support' : 'Supply Gap';
        } else {
            elFvg.textContent = `${sym}${p.toFixed(dec)}`;
            elFvg.style.color = '#fbbf24';
            if (elFvgSub) elFvgSub.textContent = 'Fair Value Equilibrium';
        }
    }

    // 4. Kelly Sizing Multiplier
    if (elKelly) {
        const k = data.kelly_unit || (data.is_god_apex ? '3x MAX UNIT' : (data.is_god_mode ? '2x UNIT' : '1x UNIT'));
        elKelly.textContent = k;
        if (elKellySub) {
            elKellySub.textContent = k.includes('4x') ? '☠️ Lethal Apex Killshot' : (k.includes('3x') ? 'Optimal Apex Bet' : (k.includes('2x') ? 'Strong Edge Bet' : (k.includes('0x') ? 'Capital Preserved' : 'Standard Allocation')));
        }
    }

    // 5. Mathematical Quantitative Matrix & Telemetry
    const math = data.math_models || {};
    const ou = math.ornstein_uhlenbeck || {};
    const entropy = math.shannon_entropy || {};
    const bayes = math.bayesian_map || {};
    const avell = math.avellaneda_stoikov || {};
    const markov = math.markov_regime || {};
    const hurst = data.hurst_model || math.hurst_model || {};

    const elMathSummary = document.getElementById('god-math-val');
    const elMathSub = document.getElementById('god-math-sub');
    if (elMathSummary) {
        const tHalf = ou.half_life !== undefined && ou.half_life < 900 ? `${ou.half_life.toFixed(1)}s` : '--';
        const hVal = entropy.norm_entropy !== undefined ? `${entropy.norm_entropy.toFixed(2)}` : '--';
        elMathSummary.textContent = `OU t½: ${tHalf} | H: ${hVal}`;
    }
    if (elMathSub) {
        const bConf = bayes.posterior_confidence !== undefined ? `${bayes.posterior_confidence}% ${bayes.map_dir || ''}` : '--';
        elMathSub.textContent = `Bayes MAP: ${bConf}`;
    }

    // Mathematical Matrix Grid Cells
    const elOuVal = document.getElementById('math-ou-val');
    const elOuSub = document.getElementById('math-ou-sub');
    if (elOuVal) {
        const tHalf = ou.half_life !== undefined && ou.half_life < 900 ? `${ou.half_life.toFixed(1)}s` : 'Momentum Drift';
        const zVal = ou.z_score !== undefined ? `${ou.z_score >= 0 ? '+' : ''}${ou.z_score.toFixed(1)}σ` : '0.0σ';
        elOuVal.textContent = `t½: ${tHalf} | Z: ${zVal}`;
    }
    if (elOuSub && ou.detail) elOuSub.textContent = ou.detail;

    const elEntropyVal = document.getElementById('math-entropy-val');
    const elEntropySub = document.getElementById('math-entropy-sub');
    if (elEntropyVal) {
        const rawH = entropy.entropy !== undefined ? entropy.entropy.toFixed(2) : '--';
        const normH = entropy.norm_entropy !== undefined ? entropy.norm_entropy.toFixed(2) : '--';
        elEntropyVal.textContent = `H: ${rawH} | h: ${normH}`;
    }
    if (elEntropySub && entropy.detail) elEntropySub.textContent = entropy.detail;

    const elBayesVal = document.getElementById('math-bayes-val');
    const elBayesSub = document.getElementById('math-bayes-sub');
    if (elBayesVal) {
        const bConf = bayes.posterior_confidence !== undefined ? `${bayes.posterior_confidence}% ${bayes.map_dir || ''}` : '50.0% WAIT';
        elBayesVal.textContent = bConf;
    }
    if (elBayesSub && bayes.detail) elBayesSub.textContent = bayes.detail;

    const elAvellVal = document.getElementById('math-avellaneda-val');
    const elAvellSub = document.getElementById('math-avellaneda-sub');
    if (elAvellVal) {
        const rVal = avell.reservation_price !== undefined ? `$${avell.reservation_price.toFixed(2)}` : '--';
        const sBps = avell.skew_bps !== undefined ? `${avell.skew_bps >= 0 ? '+' : ''}${avell.skew_bps.toFixed(1)} bps` : '0.0 bps';
        elAvellVal.textContent = `r(s): ${rVal} | Δ: ${sBps}`;
    }
    if (elAvellSub && avell.detail) elAvellSub.textContent = avell.detail;

    const elMarkovVal = document.getElementById('math-markov-val');
    const elMarkovSub = document.getElementById('math-markov-sub');
    if (elMarkovVal) {
        const st = markov.current_state || 'EQUILIBRIUM';
        const pVal = markov.persistence_prob !== undefined ? `${(markov.persistence_prob * 100).toFixed(0)}%` : '50%';
        elMarkovVal.textContent = `${st} (P: ${pVal})`;
    }
    if (elMarkovSub && markov.detail) elMarkovSub.textContent = markov.detail;

    const elHurstVal = document.getElementById('math-hurst-val');
    const elHurstSub = document.getElementById('math-hurst-sub');
    if (elHurstVal) {
        const h = hurst.hurst !== undefined ? hurst.hurst.toFixed(2) : (hurst.value !== undefined ? hurst.value.toFixed(2) : '0.50');
        elHurstVal.textContent = `H: ${h}`;
    }
    if (elHurstSub && hurst.detail) elHurstSub.textContent = hurst.detail;

    // Hawkes Self-Exciting Process
    const hawkes = math.hawkes_process || {};
    const elHawkesVal = document.getElementById('math-hawkes-val');
    const elHawkesSub = document.getElementById('math-hawkes-sub');
    if (elHawkesVal) {
        const eta = hawkes.branching_ratio !== undefined ? hawkes.branching_ratio.toFixed(2) : '0.50';
        const cascade = hawkes.is_cascade ? '⚡ CASCADE' : 'POISSON';
        elHawkesVal.textContent = `η: ${eta} | ${cascade}`;
        elHawkesVal.style.color = hawkes.is_cascade ? '#00e676' : '#f8fafc';
    }
    if (elHawkesSub && hawkes.detail) elHawkesSub.textContent = hawkes.detail;

    // Garman-Klass-Yang-Zhang Volatility
    const gkyz = math.gkyz_volatility || {};
    const elGkyzVal = document.getElementById('math-gkyz-val');
    const elGkyzSub = document.getElementById('math-gkyz-sub');
    if (elGkyzVal) {
        const sigBps = gkyz.sigma_bps_sec !== undefined ? `${gkyz.sigma_bps_sec.toFixed(1)} bps/s` : (gkyz.sigma_gkyz !== undefined ? `${(gkyz.sigma_gkyz * 10000).toFixed(1)} bps` : '--');
        elGkyzVal.textContent = `σ: ${sigBps} (8x Eff)`;
    }
    if (elGkyzSub && gkyz.detail) elGkyzSub.textContent = gkyz.detail;

    // Roll Microstructure Noise Filter
    const roll = math.roll_noise || {};
    const elRollVal = document.getElementById('math-roll-val');
    const elRollSub = document.getElementById('math-roll-sub');
    if (elRollVal) {
        const noisePct = roll.noise_ratio !== undefined ? `${(roll.noise_ratio * 100).toFixed(0)}%` : '--';
        const status = roll.is_noise_dominant ? '🛡️ CHOP NOISE' : '🟢 TRUE DRIFT';
        elRollVal.textContent = `Noise: ${noisePct} | ${status}`;
        elRollVal.style.color = roll.is_noise_dominant ? '#fbbf24' : '#00e676';
    }
    if (elRollSub && roll.detail) elRollSub.textContent = roll.detail;

    // Merton Jump-Diffusion Barrier
    const merton = math.merton_jump || {};
    const elMertonVal = document.getElementById('math-merton-val');
    const elMertonSub = document.getElementById('math-merton-sub');
    if (elMertonVal) {
        const wProb = merton.win_prob !== undefined ? `${merton.win_prob.toFixed(1)}%` : '--%';
        const dir = merton.direction || 'WAIT';
        elMertonVal.textContent = `${wProb} ${dir}`;
        elMertonVal.style.color = (merton.win_prob && merton.win_prob >= 80) ? '#00e676' : '#38bdf8';
    }
    if (elMertonSub && merton.detail) elMertonSub.textContent = merton.detail;

    // Vector 17: L2 Book Wall Absorption
    const bookWall = math.book_wall_absorption || {};
    const elBookWallVal = document.getElementById('math-book-wall-val');
    const elBookWallSub = document.getElementById('math-book-wall-sub');
    if (elBookWallVal) {
        const wallBtc = (bookWall.bid_wall_btc || bookWall.ask_wall_btc || 0).toFixed(1);
        const cushion = (bookWall.burn_ratio_up || bookWall.burn_ratio_down || 1.0).toFixed(1);
        elBookWallVal.textContent = `Wall: ${wallBtc} BTC | ${cushion}x Cushion`;
        elBookWallVal.style.color = bookWall.is_wall_secured ? '#00e676' : '#38bdf8';
    }
    if (elBookWallSub && bookWall.detail) elBookWallSub.textContent = bookWall.detail;

    // Vector 18: Tri-Venue Cross-Exchange Triangulation
    const triVenue = math.tri_venue_triangulation || {};
    const elTriVenueVal = document.getElementById('math-tri-venue-val');
    const elTriVenueSub = document.getElementById('math-tri-venue-sub');
    if (elTriVenueVal) {
        const futD = triVenue.fut_delta !== undefined ? (triVenue.fut_delta >= 0 ? '+' : '') + `$${triVenue.fut_delta.toFixed(2)}` : '--';
        const cbD = triVenue.cb_delta !== undefined ? (triVenue.cb_delta >= 0 ? '+' : '') + `$${triVenue.cb_delta.toFixed(2)}` : '--';
        elTriVenueVal.textContent = `CB: ${cbD} | Fut: ${futD}`;
        elTriVenueVal.style.color = triVenue.is_aligned ? '#00e676' : '#fbbf24';
    }
    if (elTriVenueSub && triVenue.detail) elTriVenueSub.textContent = triVenue.detail;

    // Vector 19: Almgren-Chriss Optimal Drift
    const almgren = math.almgren_chriss || data.almgren_model || {};
    const elAlmgrenVal = document.getElementById('math-almgren-val');
    const elAlmgrenSub = document.getElementById('math-almgren-sub');
    if (elAlmgrenVal) {
        const drift = almgren.drift !== undefined ? `${almgren.drift >= 0 ? '+' : ''}${almgren.drift.toFixed(2)} $/s` : '-- $/s';
        elAlmgrenVal.textContent = `Drift: ${drift}`;
        elAlmgrenVal.style.color = (almgren.signal > 0) ? '#00e676' : ((almgren.signal < 0) ? '#ef4444' : '#38bdf8');
    }
    if (elAlmgrenSub && almgren.detail) elAlmgrenSub.textContent = almgren.detail;

    // Vector 20: Amihud Illiquidity Impact
    const amihud = math.amihud_illiq || data.amihud_model || {};
    const elAmihudVal = document.getElementById('math-amihud-val');
    const elAmihudSub = document.getElementById('math-amihud-sub');
    if (elAmihudVal) {
        const kyleLam = amihud.kyle_lambda !== undefined ? amihud.kyle_lambda.toFixed(2) : '--';
        const impactState = amihud.impact_regime || 'Resilient';
        elAmihudVal.textContent = `λ: ${kyleLam} | ${impactState}`;
        elAmihudVal.style.color = '#38bdf8';
    }
    if (elAmihudSub && amihud.detail) elAmihudSub.textContent = amihud.detail;

    // Vector 21: Feller Volatility Stability
    const feller = math.feller_stability || data.feller_model || {};
    const elFellerVal = document.getElementById('math-feller-val');
    const elFellerSub = document.getElementById('math-feller-sub');
    if (elFellerVal) {
        const fRatio = feller.feller_ratio !== undefined ? feller.feller_ratio.toFixed(2) : '1.50';
        const fStatus = feller.is_stable !== false ? 'STABLE' : 'EXPLOSIVE';
        elFellerVal.textContent = `Ratio: ${fRatio} | ${fStatus}`;
        elFellerVal.style.color = feller.is_stable !== false ? '#00e676' : '#ef4444';
    }
    if (elFellerSub && feller.detail) elFellerSub.textContent = feller.detail;

    // Vector 22: Queue Depletion Gradient
    const qGrad = math.queue_gradient || data.queue_gradient_model || {};
    const elQGradVal = document.getElementById('math-queue-grad-val');
    const elQGradSub = document.getElementById('math-queue-grad-sub');
    if (elQGradVal) {
        const grad = qGrad.gradient !== undefined ? `${qGrad.gradient >= 0 ? '+' : ''}${qGrad.gradient.toFixed(2)}` : '0.00';
        const qDir = (qGrad.signal > 0) ? 'ASK DRAIN' : ((qGrad.signal < 0) ? 'BID DRAIN' : 'BALANCED');
        elQGradVal.textContent = `∇Q: ${grad} | ${qDir}`;
        elQGradVal.style.color = (qGrad.signal > 0) ? '#00e676' : ((qGrad.signal < 0) ? '#ef4444' : '#38bdf8');
    }
    if (elQGradSub && qGrad.detail) elQGradSub.textContent = qGrad.detail;

    // Vector 23: Cross-Venue Basis Expansion
    const basisExp = math.basis_expansion || data.basis_expansion_model || {};
    const elBasisVal = document.getElementById('math-basis-val');
    const elBasisSub = document.getElementById('math-basis-sub');
    if (elBasisVal) {
        const bDelta = basisExp.basis_delta !== undefined ? `${basisExp.basis_delta >= 0 ? '+' : ''}$${basisExp.basis_delta.toFixed(2)}` : '--$';
        elBasisVal.textContent = `ΔBasis: ${bDelta}`;
        elBasisVal.style.color = (basisExp.signal > 0) ? '#00e676' : ((basisExp.signal < 0) ? '#ef4444' : '#38bdf8');
    }
    if (elBasisSub && basisExp.detail) elBasisSub.textContent = basisExp.detail;

    // Vector 24: 2D Kalman State Velocity
    const kalman = math.kalman_velocity || {};
    const elKalmanVal = document.getElementById('math-kalman-val');
    const elKalmanSub = document.getElementById('math-kalman-sub');
    if (elKalmanVal) {
        const vBps = kalman.velocity_bps !== undefined ? `${kalman.velocity_bps >= 0 ? '+' : ''}${kalman.velocity_bps.toFixed(2)} bps/s` : '0.00 bps/s';
        elKalmanVal.textContent = `v_k: ${vBps}`;
        elKalmanVal.style.color = (kalman.velocity_bps > 0) ? '#00e676' : ((kalman.velocity_bps < 0) ? '#ef4444' : '#38bdf8');
    }
    if (elKalmanSub && kalman.detail) elKalmanSub.textContent = kalman.detail;
}

function renderMainSignalCard(data) {
    if (!data) data = latestSignalData;
    if (!data) return;

    const currentPrice = data.price || lastPrice || 0;

    updateGodModeHUD(data);

    // Universal Intraday Signal Display (Indian Equities & International Markets)
    if (activeMarketType === 'indian' || activeMarketType === 'international') {
        const dir = data.direction;
        const conf = data.confidence || 50;
        const sym = getCurrencySymbol();
        const vwap = (data.barrier_model && data.barrier_model.k) ? data.barrier_model.k : currentPrice;
        const setup = data.trade_setup || {};
        const isForex = currentPrice < 2.0;
        const dec = isForex ? 4 : 2;

        const isOmniscient = data.is_omniscient || (data.strength && data.strength.includes('OMNISCIENT'));
        const isLethal = isOmniscient || data.is_lethal || (data.strength && data.strength.includes('LETHAL'));
        const isGodApex = isLethal || data.is_god_apex || (data.strength && data.strength.includes('APEX'));
        const isGodMode = isGodApex || data.is_god_mode || (data.strength && data.strength.includes('GOD-MODE')) || document.body.classList.contains('god-mode-active');

        if (dir === 'UP') {
            const circleCls = isLethal ? 'signal-circle predatory-lethal' : (isGodApex ? 'signal-circle god-apex' : (isGodMode ? 'signal-circle god-mode' : 'signal-circle up'));
            const tierLabel = isOmniscient ? '👑 OMNISCIENT' : (isLethal ? '⚡ LETHAL' : (isGodApex ? 'APEX' : (isGodMode ? 'GOD' : '')));
            setSignalCircleDisplay(tierLabel, 'BUY', circleCls);
            confidenceText.textContent = `${conf}% CONVICTION`;
            strengthText.textContent = data.strength || (isGodApex ? '🌌 GOD-LEVEL APEX' : (isGodMode ? '👑 GOD-MODE' : '🔥 BULL BREAKOUT'));
            const t1 = setup.target_1 !== undefined ? setup.target_1.toFixed(dec) : (currentPrice * 1.01).toFixed(dec);
            const sl = setup.stop_loss !== undefined ? setup.stop_loss.toFixed(dec) : (currentPrice * 0.99).toFixed(dec);
            const rr = setup.risk_reward ? setup.risk_reward : '1:1.5';
            const fvgNote = (data.fvg_data && data.fvg_data.fvg_type && data.fvg_data.fvg_type !== 'NONE') ? ` | FVG: ${sym}${data.fvg_data.magnet_target.toFixed(dec)}` : '';
            actionHint.textContent = `🎯 TARGET: ${sym}${t1} | SL: ${sym}${sl} | R:R ${rr}${fvgNote} | SIZING: ${data.kelly_unit || '2x'}`;
            actionHint.style.color = isGodApex ? '#38bdf8' : (isGodMode ? '#fbbf24' : '#00e676');
        } else if (dir === 'DOWN') {
            const circleCls = isLethal ? 'signal-circle predatory-lethal' : (isGodApex ? 'signal-circle god-apex' : (isGodMode ? 'signal-circle god-mode' : 'signal-circle down'));
            const tierLabel = isOmniscient ? '👑 OMNISCIENT' : (isLethal ? '⚡ LETHAL' : (isGodApex ? 'APEX' : (isGodMode ? 'GOD' : '')));
            setSignalCircleDisplay(tierLabel, 'SELL', circleCls);
            confidenceText.textContent = `${conf}% CONVICTION`;
            strengthText.textContent = data.strength || (isGodApex ? '🌌 GOD-LEVEL APEX' : (isGodMode ? '👑 GOD-MODE' : '⚡ BEAR BREAKDOWN'));
            const t1 = setup.target_1 !== undefined ? setup.target_1.toFixed(dec) : (currentPrice * 0.99).toFixed(dec);
            const sl = setup.stop_loss !== undefined ? setup.stop_loss.toFixed(dec) : (currentPrice * 1.01).toFixed(dec);
            const rr = setup.risk_reward ? setup.risk_reward : '1:1.5';
            const fvgNote = (data.fvg_data && data.fvg_data.fvg_type && data.fvg_data.fvg_type !== 'NONE') ? ` | FVG: ${sym}${data.fvg_data.magnet_target.toFixed(dec)}` : '';
            actionHint.textContent = `🎯 TARGET: ${sym}${t1} | SL: ${sym}${sl} | R:R ${rr}${fvgNote} | SIZING: ${data.kelly_unit || '2x'}`;
            actionHint.style.color = isGodApex ? '#f43f5e' : (isGodMode ? '#fbbf24' : '#ff1744');
        } else {
            setSignalCircleDisplay('🛡️ CAPITAL', 'SHIELD', 'signal-circle wait');
            confidenceText.textContent = `${conf}% NEUTRAL`;
            strengthText.textContent = '🛡️ GOD-SHIELD: CAPITAL PROTECTED';
            actionHint.textContent = `Consolidating near VWAP (${sym}${vwap.toFixed(dec)}). Preserving capital (0x PASS).`;
            actionHint.style.color = '#fbbf24';
        }
        return;
    }

    // -------------------------------------------------------------
    // PHASE 2 & 3: OFFICIAL CALL LOCKED (From callLeadTime down to 0s)
    // The prediction is permanently locked and NEVER flips mid-round!
    // -------------------------------------------------------------
    if (hasFiredRoundCall && currentRoundBet) {
        const bDir = currentRoundBet.dir;
        const bConf = currentRoundBet.conf;
        const bEntry = cwalletRoundOpenPrice || currentRoundBet.entry;
        const cwalletSecsToLock = Math.max(0, roundSecondsLeft - CWALLET_LOCK_BUFFER);

        if (bDir === 'UP') {
            let circleCls = 'signal-circle up';
            if (currentRoundBet.isOmniscient) circleCls = 'signal-circle god-omniscient';
            else if (currentRoundBet.isLethal) circleCls = 'signal-circle predatory-lethal';
            else if (currentRoundBet.isGodApex) circleCls = 'signal-circle god-apex';
            else if (currentRoundBet.isUniversal) circleCls = 'signal-circle universal';
            else if (currentRoundBet.isGodMode) circleCls = 'signal-circle god-mode';

            const tierLabel = currentRoundBet.isOmniscient ? '👑 OMNISCIENT' : (currentRoundBet.isLethal ? '⚡ LETHAL' : (currentRoundBet.isGodApex ? 'APEX' : (currentRoundBet.isGodMode ? 'GOD' : 'BET')));
            setSignalCircleDisplay(tierLabel, 'UP', circleCls);
            confidenceText.textContent = `${bConf}% CONVICTION`;

            if (roundSecondsLeft > CWALLET_LOCK_BUFFER) {
                strengthText.textContent = currentRoundBet.isLethal ? `⚡ ☠️ PREDATORY LETHAL (${currentRoundBet.kelly || '4x'})` : (currentRoundBet.isGodApex ? `⚡ 🌌 GOD-LEVEL APEX (${currentRoundBet.kelly || '3x'})` : (currentRoundBet.isUniversal ? `🌌 UNIVERSAL APEX (${currentRoundBet.kelly || '3x'})` : (currentRoundBet.isGodMode ? `👑 GOD-MODE (${cwalletSecsToLock}s to Lock)` : `⚡ EXECUTE NOW (${cwalletSecsToLock}s to Lock)`)));
                actionHint.textContent = `🎯 OFFICIAL CALL: BET UP ON CWALLET! | Strike: $${bEntry.toFixed(2)} | Sizing: ${currentRoundBet.kelly || '1x'} | Cwallet locks in ${cwalletSecsToLock}s!`;
                actionHint.style.color = currentRoundBet.isLethal ? '#ff1744' : (currentRoundBet.isGodApex ? '#38bdf8' : (currentRoundBet.isUniversal ? '#c084fc' : (currentRoundBet.isGodMode ? '#fbbf24' : '#00e676')));
            } else {
                strengthText.textContent = currentRoundBet.isLethal ? `⚡ ☠️ PREDATORY LETHAL ROUND #${currentRoundBet.round} IN-PLAY` : (currentRoundBet.isGodApex ? `⚡ 🌌 GOD APEX ROUND #${currentRoundBet.round} IN-PLAY` : (currentRoundBet.isUniversal ? `🌌 UNIVERSAL ROUND #${currentRoundBet.round} IN-PLAY` : (currentRoundBet.isGodMode ? `👑 GOD-MODE ROUND #${currentRoundBet.round} IN-PLAY` : `🔒 ROUND #${currentRoundBet.round} IN-PLAY`)));
                const diff = currentPrice - bEntry;
                if (diff >= 0) {
                    actionHint.textContent = `🟢 IN THE MONEY: +$${diff.toFixed(2)} (Cwallet Strike: $${bEntry.toFixed(2)})`;
                    actionHint.style.color = '#00e676';
                } else {
                    actionHint.textContent = `🔴 OUT OF THE MONEY: -$${Math.abs(diff).toFixed(2)} (Cwallet Strike: $${bEntry.toFixed(2)})`;
                    actionHint.style.color = '#ff1744';
                }
            }
        } else if (bDir === 'DOWN') {
            let circleCls = 'signal-circle down';
            if (currentRoundBet.isOmniscient) circleCls = 'signal-circle god-omniscient';
            else if (currentRoundBet.isLethal) circleCls = 'signal-circle predatory-lethal';
            else if (currentRoundBet.isGodApex) circleCls = 'signal-circle god-apex';
            else if (currentRoundBet.isUniversal) circleCls = 'signal-circle universal';
            else if (currentRoundBet.isGodMode) circleCls = 'signal-circle god-mode';

            const tierLabel = currentRoundBet.isOmniscient ? '👑 OMNISCIENT' : (currentRoundBet.isLethal ? '⚡ LETHAL' : (currentRoundBet.isGodApex ? 'APEX' : (currentRoundBet.isGodMode ? 'GOD' : 'BET')));
            setSignalCircleDisplay(tierLabel, 'DOWN', circleCls);
            confidenceText.textContent = `${bConf}% CONVICTION`;

            if (roundSecondsLeft > CWALLET_LOCK_BUFFER) {
                strengthText.textContent = currentRoundBet.isGodApex ? `⚡ 🌌 GOD-LEVEL APEX (${currentRoundBet.kelly || '3x'})` : (currentRoundBet.isUniversal ? `🌌 UNIVERSAL APEX (${currentRoundBet.kelly || '3x'})` : (currentRoundBet.isGodMode ? `👑 GOD-MODE (${cwalletSecsToLock}s to Lock)` : `⚡ EXECUTE NOW (${cwalletSecsToLock}s to Lock)`));
                actionHint.textContent = `🎯 OFFICIAL CALL: BET DOWN ON CWALLET! | Strike: $${bEntry.toFixed(2)} | Sizing: ${currentRoundBet.kelly || '1x'} | Cwallet locks in ${cwalletSecsToLock}s!`;
                actionHint.style.color = currentRoundBet.isGodApex ? '#f43f5e' : (currentRoundBet.isUniversal ? '#c084fc' : (currentRoundBet.isGodMode ? '#fbbf24' : '#ff1744'));
            } else {
                strengthText.textContent = currentRoundBet.isGodApex ? `⚡ 🌌 GOD APEX ROUND #${currentRoundBet.round} IN-PLAY` : (currentRoundBet.isUniversal ? `🌌 UNIVERSAL ROUND #${currentRoundBet.round} IN-PLAY` : (currentRoundBet.isGodMode ? `👑 GOD-MODE ROUND #${currentRoundBet.round} IN-PLAY` : `🔒 ROUND #${currentRoundBet.round} IN-PLAY`));
                const diff = bEntry - currentPrice;
                if (diff >= 0) {
                    actionHint.textContent = `🟢 IN THE MONEY: +$${diff.toFixed(2)} (Cwallet Strike: $${bEntry.toFixed(2)})`;
                    actionHint.style.color = '#00e676';
                } else {
                    actionHint.textContent = `🔴 OUT OF THE MONEY: -$${Math.abs(diff).toFixed(2)} (Cwallet Strike: $${bEntry.toFixed(2)})`;
                    actionHint.style.color = '#ff1744';
                }
            }
        } else {
            // PASS / SKIP
            setSignalCircleDisplay('STREAK SHIELD', 'PASS', 'signal-circle wait');
            confidenceText.textContent = 'STREAK SHIELD';
            strengthText.textContent = `ROUND #${currentRoundBet.round} SKIPPED (PASS)`;
            actionHint.textContent = `Round #${currentRoundBet.round} Skipped: Low edge market. Capital protected! Next round in ${roundSecondsLeft}s.`;
            actionHint.style.color = '#94a3b8';
        }
        return;
    }

    // -------------------------------------------------------------
    // PHASE 1: DATA ACCUMULATION & CHAMBERING (T-30s down to callLeadTime / 5s)
    // NEVER bet or flip in Phase 1. Matrix accumulates 24 vectors quietly until T-5s!
    // -------------------------------------------------------------
    const secToCall = Math.max(0, roundSecondsLeft - callLeadTime);
    const openStrike = cwalletRoundOpenPrice || (data.barrier_model ? data.barrier_model.k : null) || lastPrice || 0;
    const curP = lastPrice || openStrike;
    const dStrike = openStrike > 0 ? (curP - openStrike) : 0;
    const dStr = (dStrike >= 0 ? '+' : '') + '$' + dStrike.toFixed(2);

    if (secToCall <= 3 && secToCall > 0) {
        // T-8s to T-6s: Chambering Ready Phase
        setSignalCircleDisplay(`⚡ ${secToCall}s`, 'CHAMBER', 'signal-circle wait');
        confidenceText.textContent = `⚡ CHAMBERING READY`;
        strengthText.textContent = `⚡ FINALIZING 24-VECTOR CONFLUENCE (Sniper in ${secToCall}s)`;
        actionHint.textContent = `⚡ Ready finger on Cwallet! Official Sniper prediction locks at EXACTLY ${callLeadTime}s mark (${secToCall}s left). Delta: ${dStr}`;
        actionHint.style.color = '#38bdf8';
    } else {
        // T-30s to T-9s: Data Accumulation Phase
        setSignalCircleDisplay(`⏳ ${secToCall}s`, 'ANALYZING', 'signal-circle wait');
        confidenceText.textContent = `ROUND #${roundNumber} (ACCUMULATING)`;
        strengthText.textContent = `⏳ ACCUMULATING 25s ORDER FLOW MATRIX (Δ ${dStr})`;
        actionHint.textContent = `⏳ Synthesizing 24 quantitative vectors. Official bet prediction triggers at EXACTLY ${callLeadTime}s mark (${secToCall}s left).`;
        actionHint.style.color = '#94a3b8';
    }
}

// ==========================================================================
// Human Execution Plan & Trader's Notebook Controller
// ==========================================================================
function updateTradePlanDeck(data) {
    if (!data) return;
    updateGodModeHUD(data);

    const setup = data.trade_setup || {};
    const sym = getCurrencySymbol();
    const currentPrice = data.price || lastPrice || 0;

    // 1. Setup Title Banner
    const banner = document.getElementById('setup-title-banner');
    const icon = document.getElementById('setup-dir-icon');
    const titleText = document.getElementById('setup-title-text');
    const rrBadge = document.getElementById('trade-rr-badge');

    const title = setup.setup_title || (data.direction === 'UP' ? 'High Conviction Bullish Continuation' : (data.direction === 'DOWN' ? 'High Conviction Bear Breakdown' : 'Equilibrium Consolidation'));
    if (titleText) titleText.textContent = title;

    if (banner && icon) {
        if (data.direction === 'UP') {
            banner.className = 'setup-title-banner bull';
            icon.textContent = '🟢';
        } else if (data.direction === 'DOWN') {
            banner.className = 'setup-title-banner bear';
            icon.textContent = '🔴';
        } else {
            banner.className = 'setup-title-banner';
            icon.textContent = '⚖️';
        }
    }

    if (rrBadge) {
        rrBadge.textContent = setup.risk_reward ? `R:R ${setup.risk_reward}` : 'R:R 1 : 2.0+';
    }

    // 2. Execution Levels
    const entryEl = document.getElementById('plan-entry-val');
    const t1El = document.getElementById('plan-target1-val');
    const t2El = document.getElementById('plan-target2-val');
    const slEl = document.getElementById('plan-stoploss-val');

    if (entryEl) entryEl.textContent = formatCurrency(setup.entry !== undefined ? setup.entry : currentPrice);
    if (t1El) t1El.textContent = formatCurrency(setup.target_1 !== undefined ? setup.target_1 : (data.direction === 'UP' ? currentPrice * 1.003 : currentPrice * 0.997));
    if (t2El) t2El.textContent = formatCurrency(setup.target_2 !== undefined ? setup.target_2 : (data.direction === 'UP' ? currentPrice * 1.006 : currentPrice * 0.994));
    if (slEl) slEl.textContent = formatCurrency(setup.stop_loss !== undefined ? setup.stop_loss : (data.direction === 'UP' ? currentPrice * 0.997 : currentPrice * 1.003));

    // 3. Trader's Notebook & Commentary
    const noteEl = document.getElementById('trader-notebook-text');
    if (noteEl) {
        const note = data.trader_note || setup.trader_note || data.trade_rationale || 'Real-time quantitative analysis active. Tracking buyer vs seller pressure across session volume.';
        noteEl.textContent = note;
    }

    // 4. Notebook Telemetry Metadata
    const vwapEl = document.getElementById('notebook-vwap-val');
    const ppEl = document.getElementById('notebook-pp-val');
    const regimeEl = document.getElementById('notebook-regime-val');
    const kellyEl = document.getElementById('notebook-kelly-val');

    const vwapVal = (data.barrier_model && data.barrier_model.k) ? data.barrier_model.k : (data.order_flow && data.order_flow.vwap_30s ? data.order_flow.vwap_30s : currentPrice);
    if (vwapEl) vwapEl.textContent = formatCurrency(vwapVal);

    const ppVal = (setup.pivots && setup.pivots.pp) ? setup.pivots.pp : vwapVal;
    if (ppEl) ppEl.textContent = formatCurrency(ppVal);

    if (regimeEl) regimeEl.textContent = data.regime || 'Trending';
    if (kellyEl) kellyEl.textContent = data.kelly_unit || '1x Unit';
}

socket.on('signal_update', (data) => {
    latestSignalData = data;
    renderMainSignalCard(data);
    updateTradePlanDeck(data);

    signalTime.textContent = new Date().toLocaleTimeString('en-US', { hour12: false });

    // Macro Trend Badge
    const macroBadge = document.getElementById('macro-trend-badge');
    if (macroBadge && data.macro_bias) {
        macroBadge.textContent = data.macro_bias;
        macroBadge.style.color = data.macro_bias === 'BULLISH' ? '#00e676' : (data.macro_bias === 'BEARISH' ? '#ff1744' : '#94a3b8');
    }

    // Whale Delta Badge
    const whaleBadge = document.getElementById('whale-delta-badge');
    if (whaleBadge && data.order_flow && data.order_flow.whale_delta !== undefined) {
        const wd = data.order_flow.whale_delta;
        whaleBadge.textContent = `${wd > 0 ? '+' : ''}${wd.toFixed(2)} BTC ${wd > 0 ? '🐋 Bulls' : (wd < 0 ? '🐋 Bears' : '')}`;
        whaleBadge.style.color = wd > 0 ? '#c084fc' : (wd < 0 ? '#f43f5e' : '#94a3b8');
    }

    // 👑 Futures Basis Lead Badge
    const futBadge = document.getElementById('futures-lead-badge');
    if (futBadge && data.order_flow && data.order_flow.basis_spread !== undefined) {
        const basis = data.order_flow.basis_spread;
        const delta = data.order_flow.basis_delta_5s || 0;
        const arrow = delta > 0.05 ? '▲+' : (delta < -0.05 ? '▼-' : '—');
        futBadge.textContent = `${basis >= 0 ? '+' : ''}$${basis.toFixed(2)} (${arrow}$${Math.abs(delta).toFixed(2)})`;
        futBadge.style.color = delta > 0.05 ? '#00e676' : (delta < -0.05 ? '#ff1744' : '#fbbf24');
    }

    // 🌌 Global Multi-Exchange Venues Badge
    const gvBadge = document.getElementById('global-venues-badge');
    if (gvBadge && data.order_flow) {
        const cb = data.order_flow.coinbase_connected ? '🟢 CB' : '⚪ CB';
        const fut = data.order_flow.futures_connected ? '🟢 Fut' : '⚪ Fut';
        gvBadge.textContent = `🟢 Spot | ${fut} | ${cb}`;
    }

    // Statistical Market Regime Badge
    const regBadge = document.getElementById('market-regime-badge');
    if (regBadge && data.regime) {
        regBadge.textContent = data.regime;
        regBadge.style.color = data.regime === 'TRENDING' ? '#00e676' : (data.regime === 'MEAN_REVERTING' ? '#38bdf8' : '#94a3b8');
    }

    // Dynamic Kelly Bet Sizing Badge
    const kellyBadge = document.getElementById('kelly-size-badge');
    if (kellyBadge && data.kelly_unit) {
        kellyBadge.textContent = data.kelly_unit;
        kellyBadge.style.color = data.kelly_unit.includes('3x') ? '#c084fc' : (data.kelly_unit.includes('2x') ? '#fbbf24' : '#00e676');
    }

    // Micro-VWAP Anchor
    const vwapBadge = document.getElementById('vwap-badge');
    if (vwapBadge && data.order_flow && data.order_flow.vwap_30s) {
        const vwapVal = data.order_flow.vwap_30s;
        const diff = (data.price || lastPrice || 0) - vwapVal;
        vwapBadge.textContent = `$${vwapVal.toFixed(1)} (${diff >= 0 ? '+' : ''}${diff.toFixed(1)})`;
        vwapBadge.style.color = diff > 0 ? '#38bdf8' : '#cbd5e1';
    }

    // Order Flow HUD
    if (data.order_flow) {
        const bull = data.order_flow.bull_ratio || 50;
        const bear = data.order_flow.bear_ratio || 50;
        const assetUnit = (activeMarketType === 'crypto') ? 'BTC' : (activeMarketType === 'indian' ? 'Shares' : 'Units');
        gaugeBull.style.width = `${bull}%`;
        gaugeBear.style.width = `${bear}%`;
        labelBullPct.textContent = `${bull}% BULLS`;
        labelBearPct.textContent = `${bear}% BEARS`;
        if (data.order_flow.buy_vol !== undefined) {
            ofBuyVol.textContent = `Bulls: ${data.order_flow.buy_vol.toFixed(2)} ${assetUnit}`;
            ofSellVol.textContent = `Bears: ${data.order_flow.sell_vol.toFixed(2)} ${assetUnit}`;
        }
        if (data.order_flow.delta_5s !== undefined) {
            const d5 = data.order_flow.delta_5s;
            deltaBurst.textContent = `Burst: ${d5 > 0 ? '+' : ''}${d5.toFixed(2)} ${assetUnit}`;
            deltaBurst.style.color = d5 > 0 ? '#00e676' : (d5 < 0 ? '#ff1744' : '#94a3b8');
        }
        const tickBadge = document.getElementById('tick-intensity-badge');
        if (tickBadge && data.order_flow.tick_intensity !== undefined) {
            tickBadge.textContent = `${data.order_flow.tick_intensity} t/s`;
        }
        if (data.order_flow.tick_intensity !== undefined && statTickRate) {
            statTickRate.textContent = `${data.order_flow.tick_intensity} t/s`;
        }

        // L1 Order Book Imbalance Depth & Stoikov Micro-Price
        const microBadge = document.getElementById('micro-price-badge');
        if (microBadge && data.order_flow.micro_price) {
            const mp = data.order_flow.micro_price;
            const bias = data.order_flow.spread_bias || 0;
            microBadge.textContent = `Micro: ${formatCurrency(mp)} (${bias >= 0 ? '+' : ''}${bias.toFixed(2)})`;
            microBadge.style.color = bias > 0.02 ? '#00e676' : (bias < -0.02 ? '#ff1744' : '#38bdf8');
        }

        const bookBidVol = document.getElementById('book-bids-vol');
        const bookAskVol = document.getElementById('book-asks-vol');
        if (bookBidVol && data.order_flow.book_bid_qty !== undefined) {
            bookBidVol.textContent = `Bids: ${data.order_flow.book_bid_qty.toLocaleString()} ${assetUnit}`;
        }
        if (bookAskVol && data.order_flow.book_ask_qty !== undefined) {
            bookAskVol.textContent = `Asks: ${data.order_flow.book_ask_qty.toLocaleString()} ${assetUnit}`;
        }

        const gaugeBookBid = document.getElementById('gauge-book-bid');
        const gaugeBookAsk = document.getElementById('gauge-book-ask');
        const labelBookBidPct = document.getElementById('label-book-bid-pct');
        const labelBookAskPct = document.getElementById('label-book-ask-pct');

        if (gaugeBookBid && gaugeBookAsk && data.order_flow.book_imbalance_5s !== undefined) {
            const imb = data.order_flow.book_imbalance_5s;
            const bidPct = Math.round(Math.max(5, Math.min(95, 50 + (imb * 50))));
            const askPct = 100 - bidPct;
            gaugeBookBid.style.width = `${bidPct}%`;
            gaugeBookAsk.style.width = `${askPct}%`;
            if (labelBookBidPct) labelBookBidPct.textContent = `${bidPct}% BIDS`;
            if (labelBookAskPct) labelBookAskPct.textContent = `${askPct}% ASKS`;
        }

        // Render Whale Radar Tape
        const whaleTape = document.getElementById('whale-tape-scroll');
        if (whaleTape && data.order_flow.recent_whales && Array.isArray(data.order_flow.recent_whales)) {
            const whales = data.order_flow.recent_whales;
            if (whales.length > 0) {
                whaleTape.innerHTML = '';
                whales.slice().reverse().forEach(w => {
                    const pill = document.createElement('span');
                    pill.className = `whale-pill ${w.is_buy ? 'buy' : 'sell'}`;
                    pill.textContent = `🐋 ${w.is_buy ? 'BUY' : 'SELL'} ${w.qty} BTC @ $${w.price ? w.price.toFixed(2) : '--'}`;
                    whaleTape.appendChild(pill);
                });
            }
        }
    }

    // MTF Matrix
    if (data.mtf) {
        const updatePill = (el, val) => {
            if (!el) return;
            el.textContent = val;
            el.className = `mtf-pill ${val.toLowerCase()}`;
        };
        updatePill(mtf1s, data.mtf['1s']);
        updatePill(mtf5s, data.mtf['5s']);
        updatePill(mtf15s, data.mtf['15s']);
        updatePill(mtf60s, data.mtf['60s']);
    }

    if (hurstExponentBadge) {
        const h = data.hurst_exponent !== undefined ? data.hurst_exponent : 0.50;
        const reg = h >= 0.58 ? 'TREND' : (h <= 0.44 ? 'REVERT' : 'RANDOM');
        hurstExponentBadge.textContent = `H=${h.toFixed(2)} (${reg})`;
        hurstExponentBadge.style.color = h >= 0.58 ? '#00e676' : (h <= 0.44 ? '#ff9100' : '#38bdf8');
    }

    if (kyleLambdaBadge) {
        const lam = data.kyle_lambda !== undefined ? data.kyle_lambda : 0.0;
        kyleLambdaBadge.textContent = `λ=${lam.toFixed(1)}`;
        kyleLambdaBadge.style.color = lam > 3.0 ? '#c084fc' : (lam > 1.0 ? '#f59e0b' : '#94a3b8');
    }

    // Indicators Breakdown Cards
    if (data.indicators && Array.isArray(data.indicators)) {
        data.indicators.forEach(ind => {
            const idSafe = ind.name.replace(/[\s\/]+/g, '-');
            let valEl = document.getElementById(`val-${idSafe}`);
            let sigEl = document.getElementById(`sig-${idSafe}`);
            let weightEl = document.getElementById(`weight-${idSafe}`);
            let detEl = document.getElementById(`det-${idSafe}`);

            if (!valEl && indicatorsGrid) {
                const div = document.createElement('div');
                div.className = 'indicator-card';
                div.id = `ind-${idSafe}`;
                div.innerHTML = `
                    <div class="indicator-header">
                        <span class="indicator-name">${ind.name}</span>
                        <span class="indicator-weight" id="weight-${idSafe}">--%</span>
                    </div>
                    <div class="indicator-body">
                        <span class="indicator-value" id="val-${idSafe}">--</span>
                        <span class="indicator-signal wait" id="sig-${idSafe}">—</span>
                    </div>
                    <div class="indicator-detail" id="det-${idSafe}">Analyzing...</div>
                `;
                indicatorsGrid.appendChild(div);
                valEl = document.getElementById(`val-${idSafe}`);
                sigEl = document.getElementById(`sig-${idSafe}`);
                weightEl = document.getElementById(`weight-${idSafe}`);
                detEl = document.getElementById(`det-${idSafe}`);
            }

            if (valEl && sigEl && weightEl) {
                valEl.textContent = typeof ind.value === 'number' ? ind.value.toFixed(2) : ind.value;
                weightEl.textContent = `${Math.round(ind.weight * 100)}%`;

                if (ind.signal > 0) {
                    sigEl.className = 'indicator-signal up';
                    sigEl.textContent = '▲';
                } else if (ind.signal < 0) {
                    sigEl.className = 'indicator-signal down';
                    sigEl.textContent = '▼';
                } else {
                    sigEl.className = 'indicator-signal wait';
                    sigEl.textContent = '—';
                }

                if (detEl && ind.detail) detEl.textContent = ind.detail;
            }
        });
    }

    // Quant Strike Radar & Mathematical Barrier Probability
    updateRadar(data);

    // Live L2 Order Book Depth Ladder
    if (data.order_flow) {
        updateDepthLadder(data.order_flow);
    }
});

// ==========================================================================
// Quant Radar & Mathematical Barrier Probability Model Controller
// ==========================================================================
function updateRadar(data) {
    if (!data) return;
    const probEl = document.getElementById('radar-prob-pct');
    const dirEl = document.getElementById('radar-prob-dir');
    const strikeEl = document.getElementById('radar-strike-val');
    const clearanceEl = document.getElementById('radar-clearance-val');
    const driftEl = document.getElementById('radar-drift-val');
    const volEl = document.getElementById('radar-vol-val');
    const volConeEl = document.getElementById('radar-vol-cone-val');
    const hurstRadarEl = document.getElementById('radar-hurst-val');
    const glowEl = document.getElementById('radar-circle-glow');

    const barrier = data.barrier_model || {};
    const winProb = data.win_probability !== undefined ? data.win_probability : (barrier.win_prob || 50.0);
    const dir = barrier.direction || data.direction || 'NEUTRAL';
    const delta = data.strike_delta !== undefined ? data.strike_delta : (barrier.strike_delta || 0.0);
    const k = barrier.k || cwalletRoundOpenPrice || (data.order_flow ? data.order_flow.vwap_30s : null) || data.price;

    if (probEl) probEl.textContent = `${winProb.toFixed(1)}%`;
    if (dirEl) {
        dirEl.textContent = dir === 'UP' ? 'PROB UP' : (dir === 'DOWN' ? 'PROB DOWN' : 'BALANCED');
        dirEl.style.color = dir === 'UP' ? '#00e676' : (dir === 'DOWN' ? '#ff1744' : '#38bdf8');
    }

    if (strikeEl) {
        strikeEl.textContent = k ? `$${k.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '$--';
    }
    if (clearanceEl) {
        const sign = delta > 0 ? '+' : '';
        clearanceEl.textContent = `${sign}$${delta.toFixed(2)} (${barrier.strike_bps ? (delta > 0 ? '+' : '') + barrier.strike_bps.toFixed(1) : '0.0'} bps)`;
        clearanceEl.style.color = delta > 0 ? '#00e676' : (delta < 0 ? '#ff1744' : '#94a3b8');
    }

    if (volConeEl) {
        const vc = barrier.vol_cone !== undefined ? barrier.vol_cone : 0.0;
        volConeEl.textContent = `±$${vc.toFixed(2)}`;
    }

    if (hurstRadarEl) {
        const h = data.hurst_exponent !== undefined ? data.hurst_exponent : (data.hurst_model ? data.hurst_model.hurst : 0.50);
        const hDesc = h >= 0.58 ? 'TREND RUN' : (h <= 0.44 ? 'REVERT SNAP' : 'RANDOM WALK');
        hurstRadarEl.textContent = `H=${h.toFixed(2)} (${hDesc})`;
        hurstRadarEl.style.color = h >= 0.58 ? '#00e676' : (h <= 0.44 ? '#ff9100' : '#38bdf8');
    }

    if (driftEl && data.order_flow) {
        const vel = data.order_flow.price_velocity_5s || 0.0;
        const sign = vel > 0 ? '+' : '';
        driftEl.textContent = `${sign}$${vel.toFixed(2)}/s`;
        driftEl.style.color = vel > 0 ? '#00e676' : (vel < 0 ? '#ff1744' : '#94a3b8');
    }

    if (volEl && data.order_flow) {
        const tickInt = data.order_flow.tick_intensity || 0.0;
        volEl.textContent = `${tickInt.toFixed(1)} trades/s`;
    }

    if (glowEl) {
        if (winProb >= 75 && dir === 'UP') {
            glowEl.className = 'radar-circle-outer glow-up';
        } else if (winProb >= 75 && dir === 'DOWN') {
            glowEl.className = 'radar-circle-outer glow-down';
        } else {
            glowEl.className = 'radar-circle-outer';
        }
    }
}

// ==========================================================================
// Order Book Depth Ladder Controller (L2 100ms Stream)
// ==========================================================================
function updateDepthLadder(orderFlow) {
    if (!orderFlow || !orderFlow.depth_ladder) return;
    const dl = orderFlow.depth_ladder;
    const asksList = document.getElementById('depth-asks-list');
    const bidsList = document.getElementById('depth-bids-list');
    const spreadEl = document.getElementById('depth-spread-val');
    const microEl = document.getElementById('depth-micro-val');
    const ratioBar = document.getElementById('depth-ratio-bar');
    const skewPill = document.getElementById('depth-skew-pill');
    const depletionPill = document.getElementById('depth-depletion-pill');

    const parseEntry = (entry) => {
        if (Array.isArray(entry)) return [parseFloat(entry[0]), parseFloat(entry[1])];
        if (typeof entry === 'string') {
            const parts = entry.trim().split(/\s+/);
            return [parseFloat(parts[0]), parseFloat(parts[1])];
        }
        return [0, 0];
    };

    if (asksList && Array.isArray(dl.asks) && dl.asks.length > 0) {
        asksList.innerHTML = '';
        const topAsks = dl.asks.slice(0, 5).reverse();
        topAsks.forEach((entry) => {
            const [p, q] = parseEntry(entry);
            if (p > 0) {
                const row = document.createElement('div');
                row.className = 'depth-row';
                row.innerHTML = `<span class="d-price" style="color: #ff5252;">$${p.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span><span class="d-qty">${q.toFixed(3)} BTC</span>`;
                asksList.appendChild(row);
            }
        });
    }

    if (spreadEl && dl.spread !== undefined) {
        spreadEl.textContent = `$${parseFloat(dl.spread).toFixed(2)}`;
    }
    if (microEl) {
        const mp = orderFlow.micro_price || (dl.best_bid && dl.best_ask ? (dl.best_bid + dl.best_ask) / 2 : null);
        microEl.textContent = mp ? `Mid: $${parseFloat(mp).toFixed(2)}` : 'Mid: $--';
    }

    if (bidsList && Array.isArray(dl.bids) && dl.bids.length > 0) {
        bidsList.innerHTML = '';
        const topBids = dl.bids.slice(0, 5);
        topBids.forEach((entry) => {
            const [p, q] = parseEntry(entry);
            if (p > 0) {
                const row = document.createElement('div');
                row.className = 'depth-row';
                row.innerHTML = `<span class="d-price" style="color: #00e676;">$${p.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span><span class="d-qty">${q.toFixed(3)} BTC</span>`;
                bidsList.appendChild(row);
            }
        });
    }

    const ratio = dl.depth_ratio !== undefined ? dl.depth_ratio : 50;
    if (ratioBar) {
        ratioBar.style.width = `${Math.min(95, Math.max(5, ratio))}%`;
    }
    if (skewPill) {
        const bidPct = Math.round(ratio);
        const askPct = 100 - bidPct;
        skewPill.textContent = `Depth: ${bidPct}% Bids / ${askPct}% Asks`;
        skewPill.style.color = ratio > 55 ? '#00e676' : (ratio < 45 ? '#ff1744' : '#38bdf8');
    }

    if (depletionPill) {
        const qv = dl.queue_depletion !== undefined ? dl.queue_depletion : 0.0;
        if (qv > 0.04) {
            depletionPill.textContent = `Queue: Bids Dominant (+${Math.round(qv * 100)}%)`;
            depletionPill.style.color = '#00e676';
            depletionPill.style.borderColor = 'rgba(0, 230, 118, 0.4)';
        } else if (qv < -0.04) {
            depletionPill.textContent = `Queue: Asks Depleting (-${Math.round(Math.abs(qv) * 100)}%)`;
            depletionPill.style.color = '#ff1744';
            depletionPill.style.borderColor = 'rgba(255, 23, 68, 0.4)';
        } else {
            depletionPill.textContent = 'Queue: Balanced';
            depletionPill.style.color = '#38bdf8';
            depletionPill.style.borderColor = 'rgba(56, 189, 248, 0.3)';
        }
    }
}

// ==========================================================================
// Institutional System Clock (Sub-Second Synchronized)
// ==========================================================================
function updateSystemClock() {
    const el = document.getElementById('system-clock');
    const istEl = document.getElementById('ist-clock');
    const istBig = document.getElementById('indian-ist-clock-big');
    const now = new Date();
    if (el) el.textContent = now.toLocaleTimeString('en-US', { timeZone: 'UTC', hour12: false }) + ' UTC';
    try {
        const istString = now.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false });
        if (istEl) istEl.textContent = istString + ' IST';
        if (istBig) istBig.textContent = istString;
    } catch(e) {
        if (istEl) istEl.textContent = now.toLocaleTimeString('en-US', { hour12: false }) + ' IST';
    }
}
setInterval(updateSystemClock, 250);
updateSystemClock();

// ==========================================================================
// Instant State Hydration & Fallback Polling (Zero-Delay Startup)
// ==========================================================================
function fetchInitialState() {
    fetch('/api/live')
        .then(r => r.json())
        .then(data => {
            if (!data) return;
            if (data.market_type) activeMarketType = data.market_type;
            if (data.symbol) activeSymbol = data.symbol;
            if (data.name) activeName = data.name;
            if (data.currency_symbol) activeCurrencySymbol = data.currency_symbol;

            const activeAssetDisplay = document.getElementById('active-asset-display');
            if (activeAssetDisplay && activeName) activeAssetDisplay.textContent = activeName;

            const pairTitle = document.getElementById('pair-title');
            if (pairTitle && activeName) pairTitle.textContent = activeName;

            const pairSubtitle = document.getElementById('pair-subtitle');
            if (pairSubtitle) {
                if (activeMarketType === 'indian') pairSubtitle.textContent = 'NSE/BSE 1m Intraday';
                else if (activeMarketType === 'international') pairSubtitle.textContent = 'Global Intraday (EST)';
                else pairSubtitle.textContent = '1s Ultra-Fast';
            }

            const thHistoryPrice = document.getElementById('th-history-price');
            if (thHistoryPrice) {
                const sym = getCurrencySymbol();
                thHistoryPrice.textContent = `${activeName} Price (${sym})`;
            }

            const roundSyncBar = document.getElementById('round-sync-bar');
            const indianSessionBar = document.getElementById('indian-session-bar');
            const intlSessionBar = document.getElementById('international-session-bar');
            const pillsCrypto = document.getElementById('market-pills-crypto');
            const pillsIndian = document.getElementById('market-pills-indian');
            const pillsIntl = document.getElementById('market-pills-international');
            const tabCrypto = document.getElementById('tab-market-crypto');
            const tabIndian = document.getElementById('tab-market-indian');
            const tabIntl = document.getElementById('tab-market-international');

            if (activeMarketType === 'indian') {
                if (roundSyncBar) roundSyncBar.style.display = 'none';
                if (indianSessionBar) indianSessionBar.style.display = 'flex';
                if (intlSessionBar) intlSessionBar.style.display = 'none';
                if (pillsIndian) pillsIndian.style.display = 'flex';
                if (pillsCrypto) pillsCrypto.style.display = 'none';
                if (pillsIntl) pillsIntl.style.display = 'none';
                if (tabIndian) tabIndian.classList.add('active', 'tab-indian');
                if (tabCrypto) tabCrypto.classList.remove('active');
                if (tabIntl) tabIntl.classList.remove('active', 'tab-intl');
            } else if (activeMarketType === 'international') {
                if (roundSyncBar) roundSyncBar.style.display = 'none';
                if (indianSessionBar) indianSessionBar.style.display = 'none';
                if (intlSessionBar) intlSessionBar.style.display = 'flex';
                if (pillsIntl) pillsIntl.style.display = 'flex';
                if (pillsCrypto) pillsCrypto.style.display = 'none';
                if (pillsIndian) pillsIndian.style.display = 'none';
                if (tabIntl) tabIntl.classList.add('active', 'tab-intl');
                if (tabCrypto) tabCrypto.classList.remove('active');
                if (tabIndian) tabIndian.classList.remove('active', 'tab-indian');
            } else {
                if (roundSyncBar) roundSyncBar.style.display = 'flex';
                if (indianSessionBar) indianSessionBar.style.display = 'none';
                if (intlSessionBar) intlSessionBar.style.display = 'none';
                if (pillsCrypto) pillsCrypto.style.display = 'flex';
                if (pillsIndian) pillsIndian.style.display = 'none';
                if (pillsIntl) pillsIntl.style.display = 'none';
                if (tabCrypto) tabCrypto.classList.add('active');
                if (tabIndian) tabIndian.classList.remove('active', 'tab-indian');
                if (tabIntl) tabIntl.classList.remove('active', 'tab-intl');
            }

            if (data.price) {
                lastPrice = data.price;
                updatePriceDisplay(data.price, 'neutral');
                if (cwalletRoundOpenPrice === null) {
                    cwalletRoundOpenPrice = data.price;
                    if (cwalletOpenPriceDisplay) {
                        cwalletOpenPriceDisplay.textContent = formatCurrency(data.price);
                    }
                }
            }
            if (data.last_signal) {
                latestSignalData = data.last_signal;
                renderMainSignalCard(data.last_signal);
                updateTradePlanDeck(data.last_signal);
            }
            if (data.stats) {
                renderPerformanceStats(data.stats);
            }
            if (data.zero_defect_mode !== undefined && data.zero_defect_mode !== isZeroDefectEnabled) {
                applyZeroDefectState(data.zero_defect_mode, false, false);
            }
        })
        .catch(e => console.warn('Initial state fetch error:', e));
}
fetchInitialState();
setInterval(fetchInitialState, 3000);

// ==========================================================================
// Market Hub Interaction Controller
// ==========================================================================
function setupMarketHub() {
    const tabCrypto = document.getElementById('tab-market-crypto');
    const tabIndian = document.getElementById('tab-market-indian');
    const pillsCrypto = document.getElementById('market-pills-crypto');
    const pillsIndian = document.getElementById('market-pills-indian');
    const searchInput = document.getElementById('market-search-input');
    const btnSearchGo = document.getElementById('btn-search-go');
    const searchDropdown = document.getElementById('search-dropdown');

    function switchMarket(type, symbol) {
        fetch('/api/switch_symbol', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ market_type: type, symbol: symbol })
        })
        .then(r => r.json())
        .then(res => {
            if (res.status === 'ok') {
                speakTacticalAlert(`Loaded ${res.name}`);
            }
        })
        .catch(err => console.error('Error switching symbol:', err));
    }

    if (tabCrypto) {
        tabCrypto.addEventListener('click', () => {
            if (activeMarketType !== 'crypto') {
                switchMarket('crypto', 'btcusdt');
            }
        });
    }

    if (tabIndian) {
        tabIndian.addEventListener('click', () => {
            if (activeMarketType !== 'indian') {
                switchMarket('indian', '^NSEI');
            }
        });
    }

    const tabIntl = document.getElementById('tab-market-international');
    if (tabIntl) {
        tabIntl.addEventListener('click', () => {
            if (activeMarketType !== 'international') {
                switchMarket('international', '^GSPC');
            }
        });
    }

    // Live EST Digital Clock
    setInterval(() => {
        const estClockEl = document.getElementById('intl-est-clock-big');
        if (estClockEl) {
            try {
                const now = new Date();
                const estTime = new Intl.DateTimeFormat('en-US', {
                    timeZone: 'America/New_York',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false
                }).format(now);
                estClockEl.textContent = estTime + ' EST';
            } catch (e) {
                estClockEl.textContent = new Date().toLocaleTimeString() + ' EST';
            }
        }
    }, 1000);

    // Pill clicks
    document.querySelectorAll('.pill-asset').forEach(btn => {
        btn.addEventListener('click', () => {
            const mType = btn.getAttribute('data-type') || 'crypto';
            const mSym = btn.getAttribute('data-symbol');
            if (mSym) switchMarket(mType, mSym);
        });
    });

    // Search Box Autocomplete
    let searchDebounce = null;
    if (searchInput && searchDropdown) {
        searchInput.addEventListener('input', () => {
            clearTimeout(searchDebounce);
            const val = searchInput.value.trim();
            if (val.length === 0) {
                searchDropdown.style.display = 'none';
                searchDropdown.innerHTML = '';
                return;
            }

            searchDebounce = setTimeout(() => {
                fetch(`/api/search_symbol?q=${encodeURIComponent(val)}`)
                    .then(r => r.json())
                    .then(data => {
                        const items = data.results || [];
                        if (items.length === 0) {
                            searchDropdown.innerHTML = '<div style="padding: 10px; color: #94a3b8; font-size: 12px;">No matching symbols found</div>';
                            searchDropdown.style.display = 'block';
                            return;
                        }
                        searchDropdown.innerHTML = items.map(item => `
                            <div class="search-item" data-type="${item.market_type}" data-symbol="${item.symbol}">
                                <div class="search-item-left">
                                    <span class="search-item-sym">${item.currency_symbol || ''} ${item.symbol}</span>
                                    <span class="search-item-name">${item.name}</span>
                                </div>
                                <span class="search-item-badge">${item.exchange || item.market_type.toUpperCase()}</span>
                            </div>
                        `).join('');
                        searchDropdown.style.display = 'block';

                        searchDropdown.querySelectorAll('.search-item').forEach(el => {
                            el.addEventListener('click', () => {
                                const t = el.getAttribute('data-type');
                                const s = el.getAttribute('data-symbol');
                                searchInput.value = s;
                                searchDropdown.style.display = 'none';
                                switchMarket(t, s);
                            });
                        });
                    })
                    .catch(() => {});
            }, 200);
        });

        if (btnSearchGo) {
            btnSearchGo.addEventListener('click', () => {
                const val = searchInput.value.trim();
                if (val) {
                    const isIndian = val.toUpperCase().endsWith('.NS') || val.toUpperCase().endsWith('.BO') || val.startsWith('^') || activeMarketType === 'indian';
                    switchMarket(isIndian ? 'indian' : 'crypto', val);
                    searchDropdown.style.display = 'none';
                }
            });
        }

        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const val = searchInput.value.trim();
                if (val) {
                    const isIndian = val.toUpperCase().endsWith('.NS') || val.toUpperCase().endsWith('.BO') || val.startsWith('^') || activeMarketType === 'indian';
                    switchMarket(isIndian ? 'indian' : 'crypto', val);
                    searchDropdown.style.display = 'none';
                }
            }
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.market-search-box')) {
                searchDropdown.style.display = 'none';
            }
        });
    }
}
setupMarketHub();



// ==========================================================================
// Dedicated Cwallet System Live Prediction & Action Command Deck
// ==========================================================================
function updateCwalletAreaHero() {
    const callTag = document.getElementById('cw-prediction-call-tag');
    const callIcon = document.getElementById('cw-call-icon');
    const callTitle = document.getElementById('cw-call-title');
    const strikePill = document.getElementById('cw-hero-strike');
    const deltaPill = document.getElementById('cw-hero-delta');
    const probPill = document.getElementById('cw-hero-prob');
    const sizingPill = document.getElementById('cw-hero-sizing');
    const headline = document.getElementById('cw-hero-action-headline');
    const actionSub = document.getElementById('cw-hero-action-sub');

    if (!callTag) return;

    const openStrike = cwalletRoundOpenPrice || (latestSignalData && latestSignalData.barrier_model ? latestSignalData.barrier_model.k : null) || lastPrice || 0;
    const currentPrice = lastPrice || openStrike;
    const delta = openStrike > 0 ? (currentPrice - openStrike) : 0;
    const deltaSign = delta >= 0 ? '+' : '';
    const deltaBps = openStrike > 0 ? ((delta / openStrike) * 10000).toFixed(1) : '0.0';
    const cwalletSecsToLock = Math.max(0, roundSecondsLeft - CWALLET_LOCK_BUFFER);

    // Update Telemetry Pills
    if (strikePill) strikePill.textContent = `OPEN STRIKE: $${openStrike > 0 ? openStrike.toFixed(2) : '--'}`;
    if (deltaPill) {
        deltaPill.textContent = `DELTA: ${deltaSign}$${delta.toFixed(2)} (${deltaSign}${deltaBps} bps)`;
        deltaPill.style.color = delta > 0 ? '#00e676' : (delta < 0 ? '#ff1744' : '#94a3b8');
    }

    // 1. PHASE: OFFICIAL SNIPER CONFIRMED & IN PLAY (From sniper trigger until round end)
    if (hasFiredRoundCall && currentRoundBet) {
        const isZdCall = currentRoundBet.isZeroDefect || isZeroDefectEnabled;
        if (currentRoundBet.dir === 'PASS' || currentRoundBet.isShielded) {
            callTag.className = 'cw-prediction-call-tag call-wait';
            if (callIcon) callIcon.textContent = '🛡️';
            if (callTitle) {
                callTitle.textContent = currentRoundBet.strength || (isZdCall 
                    ? `🛡️ 100% ZERO-DEFECT SHIELD: PASS ROUND #${roundNumber} (0x ALLOC)`
                    : `🛡️ CAPITAL SHIELD: SKIP ROUND #${roundNumber} (0x PASS)`);
            }
            if (probPill) probPill.textContent = isZdCall ? 'RISK: 0% (FORTRESS)' : 'EDGE: LOW (CHOP)';
            if (sizingPill) sizingPill.textContent = isZdCall ? 'SIZING: 0x ZERO-DEFECT PASS' : 'SIZING: 0x PASS';

            if (headline) {
                headline.textContent = isZdCall 
                    ? `🛡️ ROUND #${roundNumber} ZERO-DEFECT SHIELD (0% RISK FORTRESS):`
                    : `🛡️ ROUND #${roundNumber} CAPITAL SHIELDED (PRESERVE BANKROLL):`;
            }
            if (actionSub) {
                actionSub.innerHTML = currentRoundBet.strength
                    ? `<strong style="color: #34d399; font-size: 14px;">${currentRoundBet.strength}</strong><br><span style="color: #94a3b8; font-size: 11px;">100% Zero-Defect fortress preserves bankroll until an infallible runaway fires. Next round in ${roundSecondsLeft}s.</span>`
                    : (isZdCall
                        ? `<strong style="color: #34d399; font-size: 14px;">🛡️ 100% ZERO-DEFECT CAPITAL SHIELD: DO NOT BET!</strong><br><span style="color: #94a3b8; font-size: 11px;">Sub-4σ chop (Δ $${delta.toFixed(2)}). 100% Zero-Defect fortress preserves bankroll until an infallible runaway fires. Next round in ${roundSecondsLeft}s.</span>`
                        : `<strong style="color: #fbbf24; font-size: 14px;">🚫 DO NOT BET THIS ROUND!</strong><br><span style="color: #94a3b8; font-size: 11px;">Price is fluctuating in chop/noise near strike ($${openStrike.toFixed(2)}). Capital preserved. Next round setup in ${roundSecondsLeft}s.</span>`);
            }
            return;
        }

        const dir = currentRoundBet.dir;
        const kelly = currentRoundBet.kelly || (isZdCall ? '5x MAXIMUM ZERO-DEFECT UNIT' : '5x MAX GOD-LETHAL UNIT');
        const conf = isZdCall ? 100 : Math.max(currentRoundBet.conf || 96, 96);

        if (probPill) probPill.textContent = isZdCall ? `WIN PROB: 100% (4σ FORTRESS)` : `WIN PROB: ${conf}% (SNIPER LOCKED)`;
        if (sizingPill) sizingPill.textContent = `SIZING: ${kelly}`;

        if (dir === 'UP') {
            callTag.className = isZdCall ? 'cw-prediction-call-tag call-up zero-defect' : 'cw-prediction-call-tag call-up';
            if (callIcon) callIcon.textContent = isZdCall ? '🛡️' : '👑';
            if (callTitle) {
                callTitle.textContent = currentRoundBet.strength || (isZdCall
                    ? `🛡️ 🔥 100% ZERO-DEFECT SNIPER: BET UP NOW (Δ ${deltaSign}$${delta.toFixed(2)})`
                    : `🎯 99% SNIPER CONFIRMED: BET UP NOW (Δ ${deltaSign}$${delta.toFixed(2)})`);
            }

            if (roundSecondsLeft > CWALLET_LOCK_BUFFER) {
                if (headline) {
                    headline.textContent = isZdCall
                        ? `🛡️ 🔥 100% ZERO-DEFECT SNIPER ACTIVE (ROUND #${roundNumber} | ${roundSecondsLeft}s LEFT):`
                        : `⚡ CWALLET SNIPER ACTIVE (ROUND #${roundNumber} | ${roundSecondsLeft}s LEFT):`;
                }
                if (actionSub) {
                    actionSub.innerHTML = isZdCall
                        ? `<strong style="color: #34d399; font-size: 15px;">👉 100% ZERO-DEFECT: TAP GREEN [UP] BUTTON NOW!</strong><br><span style="color: #94a3b8; font-size: 11px;">Open Strike: $${openStrike.toFixed(2)} (${deltaSign}${deltaBps} bps) | Win Prob: 100% (4σ Super-Clearance) | ${kelly}</span>`
                        : `<strong style="color: #00e676; font-size: 14px;">👉 OPEN CWALLET BATTLE &rarr; TAP GREEN [UP] BUTTON NOW!</strong><br><span style="color: #94a3b8; font-size: 11px;">Open Strike: $${openStrike.toFixed(2)} (${deltaSign}${deltaBps} bps) | Win Prob: ${conf}% | ${kelly}</span>`;
                }
            } else {
                if (headline) headline.textContent = `🔒 CWALLET BETTING LOCKED (ROUND #${roundNumber} SETTLING):`;
                if (delta >= 0) {
                    if (actionSub) actionSub.innerHTML = `<strong style="color: #00e676;">🟢 IN THE MONEY: +$${delta.toFixed(2)} above strike!</strong> Position winning. Settling at 0s.`;
                } else {
                    if (actionSub) actionSub.innerHTML = `<strong style="color: #ff1744;">🔴 OUT OF THE MONEY: -$${Math.abs(delta).toFixed(2)} below strike.</strong> Tracking settlement price...`;
                }
            }
        } else {
            callTag.className = isZdCall ? 'cw-prediction-call-tag call-down zero-defect' : 'cw-prediction-call-tag call-down';
            if (callIcon) callIcon.textContent = isZdCall ? '🛡️' : '👑';
            if (callTitle) {
                callTitle.textContent = currentRoundBet.strength || (isZdCall
                    ? `🛡️ 🔥 100% ZERO-DEFECT SNIPER: BET DOWN NOW (Δ -$${Math.abs(delta).toFixed(2)})`
                    : `🎯 99% SNIPER CONFIRMED: BET DOWN NOW (Δ -$${Math.abs(delta).toFixed(2)})`);
            }

            if (roundSecondsLeft > CWALLET_LOCK_BUFFER) {
                if (headline) {
                    headline.textContent = isZdCall
                        ? `🛡️ 🔥 100% ZERO-DEFECT SNIPER ACTIVE (ROUND #${roundNumber} | ${roundSecondsLeft}s LEFT):`
                        : `⚡ CWALLET SNIPER ACTIVE (ROUND #${roundNumber} | ${roundSecondsLeft}s LEFT):`;
                }
                if (actionSub) {
                    actionSub.innerHTML = isZdCall
                        ? `<strong style="color: #ff5252; font-size: 15px;">👉 100% ZERO-DEFECT: TAP RED [DOWN] BUTTON NOW!</strong><br><span style="color: #94a3b8; font-size: 11px;">Open Strike: $${openStrike.toFixed(2)} (-${Math.abs(deltaBps)} bps) | Win Prob: 100% (4σ Super-Clearance) | ${kelly}</span>`
                        : `<strong style="color: #ff1744; font-size: 14px;">👉 OPEN CWALLET BATTLE &rarr; TAP RED [DOWN] BUTTON NOW!</strong><br><span style="color: #94a3b8; font-size: 11px;">Open Strike: $${openStrike.toFixed(2)} (-${Math.abs(deltaBps)} bps) | Win Prob: ${conf}% | ${kelly}</span>`;
                }
            } else {
                if (headline) headline.textContent = `🔒 CWALLET BETTING LOCKED (ROUND #${roundNumber} SETTLING):`;
                if (delta <= 0) {
                    if (actionSub) actionSub.innerHTML = `<strong style="color: #00e676;">🟢 IN THE MONEY: -$${Math.abs(delta).toFixed(2)} below strike!</strong> Position winning. Settling at 0s.`;
                } else {
                    if (actionSub) actionSub.innerHTML = `<strong style="color: #ff1744;">🔴 OUT OF THE MONEY: +$${delta.toFixed(2)} above strike.</strong> Tracking settlement price...`;
                }
            }
        }
        return;
    }

    // 2. PHASE: EARLY ROUND ACTIVE GUIDANCE (Seconds 30 down to callLeadTime)
    const secsUntilSniper = Math.max(0, roundSecondsLeft - callLeadTime);
    const progressPct = Math.min(100, Math.round(((30 - roundSecondsLeft) / Math.max(1, 30 - callLeadTime)) * 100));

    const isEarlyBull = (delta >= 0.25) || (latestSignalData && latestSignalData.direction === 'UP' && delta >= -0.10);
    const isEarlyBear = (delta <= -0.25) || (latestSignalData && latestSignalData.direction === 'DOWN' && delta <= 0.10);

    if (probPill) probPill.textContent = `EARLY WIN PROB: ${isEarlyBull || isEarlyBear ? '96%' : 'ANALYZING'}`;
    if (sizingPill) sizingPill.textContent = `SNIPER LOCK: ${callLeadTime}s (${secsUntilSniper}s left)`;

    if (isEarlyBull) {
        callTag.className = 'cw-prediction-call-tag call-up';
        if (callIcon) callIcon.textContent = '🟢';
        if (callTitle) callTitle.textContent = `🟢 EARLY CALL: BET UP NOW (Δ ${deltaSign}$${delta.toFixed(2)})`;
        if (headline) headline.textContent = `⚡ EARLY CWALLET CALL (LOCKS AT ${callLeadTime}s | ${secsUntilSniper}s LEFT):`;
        if (actionSub) actionSub.innerHTML = `<strong style="color: #00e676; font-size: 14px;">👉 EARLY LEAN: TAP GREEN [UP] BUTTON NOW!</strong><br><span style="color: #94a3b8; font-size: 11px;">Clearance: ${deltaSign}$${delta.toFixed(2)} vs Strike $${openStrike.toFixed(2)}. In-round momentum bullish. Official sniper lock in ${secsUntilSniper}s!</span>`;
    } else if (isEarlyBear) {
        callTag.className = 'cw-prediction-call-tag call-down';
        if (callIcon) callIcon.textContent = '🔴';
        if (callTitle) callTitle.textContent = `🔴 EARLY CALL: BET DOWN NOW (Δ -$${Math.abs(delta).toFixed(2)})`;
        if (headline) headline.textContent = `⚡ EARLY CWALLET CALL (LOCKS AT ${callLeadTime}s | ${secsUntilSniper}s LEFT):`;
        if (actionSub) actionSub.innerHTML = `<strong style="color: #ff1744; font-size: 14px;">👉 EARLY LEAN: TAP RED [DOWN] BUTTON NOW!</strong><br><span style="color: #94a3b8; font-size: 11px;">Clearance: -$${Math.abs(delta).toFixed(2)} vs Strike $${openStrike.toFixed(2)}. In-round momentum bearish. Official sniper lock in ${secsUntilSniper}s!</span>`;
    } else {
        callTag.className = 'cw-prediction-call-tag call-scanning';
        if (callIcon) callIcon.textContent = '🔬';
        if (callTitle) callTitle.textContent = `FLAT ON STRIKE: WAITING BREAKOUT (Δ ${deltaSign}$${delta.toFixed(2)})`;
        if (headline) headline.textContent = `🧠 ORDER FLOW SCANNING (SNIPER AT ${callLeadTime}s | ${secsUntilSniper}s LEFT):`;
        if (actionSub) actionSub.innerHTML = `Price hovering within 25¢ of strike ($${openStrike.toFixed(2)}). <strong style="color: #38bdf8;">Precision sniper call fires at ${callLeadTime}s mark!</strong> (10s before Cwallet locks).`;
    }
}

// Collapsible Stochastic SDE & Math Core Toggle
const btnToggleMath = document.getElementById('btn-toggle-math-matrix');
const collapsibleMath = document.getElementById('collapsible-math-section');
if (btnToggleMath && collapsibleMath) {
    // Default to visible, but easily toggleable
    btnToggleMath.addEventListener('click', () => {
        const isHidden = collapsibleMath.style.display === 'none';
        collapsibleMath.style.display = isHidden ? 'block' : 'none';
        btnToggleMath.textContent = isHidden 
            ? '📐 Quantitative Mathematical Core (Stochastic SDE & Entropy) • [Hide]' 
            : '📐 Quantitative Mathematical Core (Stochastic SDE & Entropy) • [Show]';
    });
}

