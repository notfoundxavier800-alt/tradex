const fs = require('fs');
const path = require('path');

// 1. Read HTML and extract all IDs
const html = fs.readFileSync(path.join(__dirname, '..', 'templates', 'dashboard.html'), 'utf-8');
const idRegex = /id=["']([a-zA-Z0-9_-]+)["']/g;
const htmlIds = new Set();
let match;
while ((match = idRegex.exec(html)) !== null) {
    htmlIds.add(match[1]);
}
console.log(`[DOM Mock] Loaded ${htmlIds.size} unique IDs from templates/dashboard.html`);

// 2. Create mock Element factory
function createMockElement(id, tagName = 'div') {
    return {
        id: id || '',
        tagName: tagName.toUpperCase(),
        textContent: '',
        innerText: '',
        innerHTML: '',
        value: '',
        disabled: false,
        dataset: {},
        style: {},
        classList: {
            classes: new Set(),
            add: function(...cls) { cls.forEach(c => this.classes.add(c)); },
            remove: function(...cls) { cls.forEach(c => this.classes.delete(c)); },
            toggle: function(cls, force) {
                if (force === undefined) {
                    if (this.classes.has(cls)) { this.classes.delete(cls); return false; }
                    else { this.classes.add(cls); return true; }
                } else if (force) {
                    this.classes.add(cls); return true;
                } else {
                    this.classes.delete(cls); return false;
                }
            },
            contains: function(cls) { return this.classes.has(cls); }
        },
        listeners: {},
        addEventListener: function(event, handler) {
            if (!this.listeners[event]) this.listeners[event] = [];
            this.listeners[event].push(handler);
        },
        removeEventListener: function(event, handler) {
            if (this.listeners[event]) {
                this.listeners[event] = this.listeners[event].filter(h => h !== handler);
            }
        },
        dispatchEvent: function(event) {
            const handlers = this.listeners[event.type || event] || [];
            handlers.forEach(h => h(event));
        },
        click: function() {
            this.dispatchEvent({ type: 'click', target: this, preventDefault: function() {} });
        },
        appendChild: function(child) { return child; },
        insertBefore: function(child, ref) { return child; },
        prepend: function(child) { return child; },
        removeChild: function(child) { return child; },
        children: [],
        firstChild: null,
        lastChild: null,
        setAttribute: function(attr, val) { this[attr] = val; },
        getAttribute: function(attr) { return this[attr] || null; },
        removeAttribute: function(attr) { delete this[attr]; },
        select: function() {},
        focus: function() {},
        blur: function() {},
        scrollIntoView: function() {},
        getBoundingClientRect: function() {
            return { top: 0, left: 0, bottom: 100, right: 100, width: 100, height: 100 };
        }
    };
}

// Map of created elements for existing IDs
const domElements = new Map();
for (const id of htmlIds) {
    domElements.set(id, createMockElement(id));
}

// Mock socket
const socketHandlers = {};
const mockSocket = {
    connected: true,
    on: function(event, handler) {
        if (!socketHandlers[event]) socketHandlers[event] = [];
        socketHandlers[event].push(handler);
    },
    emit: function(event, data) {},
    connect: function() {}
};

// Mock chart
const mockSeries = {
    setData: function() {},
    update: function() {},
    setMarkers: function() {},
    applyOptions: function() {},
    createPriceLine: function() { return { applyOptions: function() {} }; },
    removePriceLine: function() {}
};
const mockChart = {
    applyOptions: function() {},
    addCandlestickSeries: function() { return mockSeries; },
    addAreaSeries: function() { return mockSeries; },
    addLineSeries: function() { return mockSeries; },
    addHistogramSeries: function() { return mockSeries; },
    timeScale: function() {
        return {
            fitContent: function() {},
            scrollToPosition: function() {},
            setVisibleRange: function() {}
        };
    },
    resize: function() {},
    remove: function() {}
};

// Global mocks
const mockStorage = {};
function MockNotification(title, options) {
    this.title = title;
    this.options = options;
}
MockNotification.permission = 'granted';
MockNotification.requestPermission = function() { return Promise.resolve('granted'); };

global.window = {
    innerWidth: 1200,
    innerHeight: 800,
    addEventListener: function(event, handler) {
        if (event === 'DOMContentLoaded' || event === 'load') {
            setImmediate(handler);
        }
    },
    removeEventListener: function() {},
    localStorage: {
        getItem: function(k) { return mockStorage[k] || null; },
        setItem: function(k, v) { mockStorage[k] = String(v); },
        removeItem: function(k) { delete mockStorage[k]; },
        clear: function() { Object.keys(mockStorage).forEach(k => delete mockStorage[k]); }
    },
    location: {
        protocol: 'https:',
        host: 'tradex-signals.onrender.com',
        origin: 'https://tradex-signals.onrender.com',
        href: 'https://tradex-signals.onrender.com/'
    },
    navigator: {
        userAgent: 'Node-Test-Browser',
        serviceWorker: { register: function() { return Promise.resolve(); } },
        clipboard: { writeText: function() { return Promise.resolve(); } }
    },
    Notification: MockNotification,
    AudioContext: function() {
        return {
            state: 'running',
            createOscillator: function() {
                return {
                    connect: function() {},
                    start: function() {},
                    stop: function() {},
                    frequency: { setValueAtTime: function() {}, exponentialRampToValueAtTime: function() {} },
                    type: 'sine'
                };
            },
            createGain: function() {
                return {
                    connect: function() {},
                    gain: { setValueAtTime: function() {}, linearRampToValueAtTime: function() {}, exponentialRampToValueAtTime: function() {} }
                };
            },
            destination: {}
        };
    },
    speechSynthesis: {
        speak: function() {},
        cancel: function() {},
        getVoices: function() { return []; }
    },
    SpeechSynthesisUtterance: function(text) { this.text = text; },
    io: function() { return mockSocket; },
    LightweightCharts: {
        createChart: function() { return mockChart; },
        CrosshairMode: { Normal: 0, Magnet: 1 }
    }
};

global.document = {
    getElementById: function(id) {
        if (domElements.has(id)) {
            return domElements.get(id);
        }
        return null;
    },
    querySelector: function(sel) {
        if (sel.startsWith('#')) {
            const id = sel.slice(1);
            return global.document.getElementById(id);
        }
        return createMockElement('', 'div');
    },
    querySelectorAll: function(sel) {
        return [];
    },
    createElement: function(tag) {
        return createMockElement('', tag);
    },
    createTextNode: function(text) {
        return { textContent: text };
    },
    body: createMockElement('body', 'body'),
    addEventListener: function(event, handler) {
        if (event === 'DOMContentLoaded') {
            setImmediate(handler);
        }
    },
    execCommand: function() { return true; }
};

global.navigator = global.window.navigator;
global.localStorage = global.window.localStorage;
global.Notification = MockNotification;
global.AudioContext = global.window.AudioContext;
global.webkitAudioContext = global.window.AudioContext;
global.speechSynthesis = global.window.speechSynthesis;
global.SpeechSynthesisUtterance = global.window.SpeechSynthesisUtterance;
global.io = global.window.io;
global.LightweightCharts = global.window.LightweightCharts;
global.fetch = function(url, opts) {
    return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: 'ok', price: 66500, symbol: 'BTCUSDT' })
    });
};

// 3. Load and execute static/app.js
console.log('[Test] Executing static/app.js...');
const jsCode = fs.readFileSync(path.join(__dirname, '..', 'static', 'app.js'), 'utf-8');

try {
    eval(jsCode);
    console.log('✅ [Test] static/app.js evaluated successfully with NO initial errors!');
} catch (err) {
    console.error('❌ [FATAL] Error evaluating static/app.js:');
    console.error(err);
    process.exit(1);
}

// 4. Test Socket events
console.log('\n[Test] Testing all registered socket events...');

const samplePriceUpdate = {
    price: 66500.50,
    timestamp: Date.now(),
    volume: 12.5,
    high: 66550,
    low: 66450,
    change: 1.25,
    order_flow: {
        tick_intensity: 15.2,
        imbalance_ratio: 2.1,
        cumulative_volume_delta: 45.2,
        vwap_30s: 66495.0,
        price_velocity_5s: 0.85
    }
};

const sampleSignalUpdate = {
    price: 66500.50,
    direction: 'UP',
    confidence: 99.4,
    tier: 'TIER_1_APEX',
    action: 'BUY_CALL',
    timestamp: Date.now(),
    lead_time: 10,
    confluence_score: 96,
    barrier_model: {
        k: 66480.0,
        direction: 'UP',
        win_prob: 99.4,
        strike_delta: 20.5,
        strike_bps: 3.1,
        vol_cone: 12.0
    },
    hurst_model: {
        hurst: 0.65,
        regime: 'PERSISTENT'
    },
    order_flow: {
        imbalance_ratio: 2.5,
        tick_intensity: 18.5,
        vwap_30s: 66490.0,
        buyer_exhaustion: false,
        seller_exhaustion: false,
        price_velocity_5s: 1.2
    },
    quantitative_models: {
        hsmm: { state: 1, name: 'BULL_TREND', win_prob: 99.1 },
        ou_process: { half_life_sec: 14.2, speed_gamma: 0.048, mean_mu: 66510 },
        hawkes_intensity: { lambda_t: 12.4, branching_ratio: 0.65, clustering: 'HIGH' },
        merton_jump: { jump_prob: 0.04, expected_intensity: 0.01 },
        avellaneda: { optimal_reservation_price: 66505, spread: 2.5 },
        bouchaud: { propagator_impact: 0.85, market_memory: 'PERSISTENT' },
        cont_stoikov: { queue_depletion: -0.15, absorption_time_ms: 120 }
    }
};

const sampleRoundUpdate = {
    round_id: 12345,
    status: 'ACTIVE',
    seconds_remaining: 8,
    open_price: 66480.0,
    current_price: 66500.5,
    strike_price: 66480.0,
    round_duration: 30,
    server_time: Date.now(),
    predicted_direction: 'UP',
    confidence: 99.4
};

const sampleRoundSettled = {
    round_id: 12345,
    open_price: 66480.0,
    close_price: 66510.0,
    outcome: 'WIN',
    profit_usdt: 18.5,
    consecutive_wins: 5
};

const sampleSniperCall = {
    round_id: 12346,
    direction: 'UP',
    confidence: 99.5,
    strike_price: 66500.0,
    lead_seconds: 8,
    tier: 'TIER_1_APEX'
};

const samplePrep = {
    round_id: 12347,
    direction: 'UP',
    seconds_until_lock: 12
};

const sampleCandleHistory = [
    { time: Math.floor(Date.now() / 1000) - 60, open: 66400, high: 66510, low: 66390, close: 66500, volume: 10 }
];

const sampleCandleUpdate = {
    time: Math.floor(Date.now() / 1000), open: 66500, high: 66520, low: 66490, close: 66510, volume: 2
};

const sampleAiAnalysis = {
    council_consensus: 'UP',
    consensus_confidence: 99.2,
    bull_rationale: 'Hawkes intensity cluster + OU drift confirms breakout',
    bear_rationale: 'Minimal barrier resistance above strike',
    risk_gate_approved: true,
    munger_veto: false
};

const testEvents = [
    { name: 'connect', data: {} },
    { name: 'price_update', data: samplePriceUpdate },
    { name: 'signal_update', data: sampleSignalUpdate },
    { name: 'cwallet_round_update', data: sampleRoundUpdate },
    { name: 'cwallet_sniper_call', data: sampleSniperCall },
    { name: 'chambering_prep', data: samplePrep },
    { name: 'cwallet_round_settled', data: sampleRoundSettled },
    { name: 'candle_history', data: sampleCandleHistory },
    { name: 'candle_update', data: sampleCandleUpdate },
    { name: 'ai_analysis_complete', data: sampleAiAnalysis },
    { name: 'zero_defect_mode_switched', data: { enabled: true } },
    { name: 'market_switched', data: { symbol: 'BTCUSDT', name: 'Bitcoin' } }
];

let failedEvents = 0;
for (const ev of testEvents) {
    const handlers = socketHandlers[ev.name] || [];
    console.log(`[Test] Firing event '${ev.name}' to ${handlers.length} handler(s)...`);
    for (const h of handlers) {
        try {
            h(ev.data);
            console.log(`  ✅ Handler for '${ev.name}' succeeded`);
        } catch (err) {
            console.error(`  ❌ [CRASH] Handler for '${ev.name}' failed!`);
            console.error(err);
            failedEvents++;
        }
    }
}

// 5. Test clicking every interactive element
console.log('\n[Test] Testing all registered element click handlers...');
let clickErrors = 0;
for (const [id, el] of domElements.entries()) {
    if (el.listeners['click'] && el.listeners['click'].length > 0) {
        for (const handler of el.listeners['click']) {
            try {
                handler({ target: el, preventDefault: function() {} });
            } catch (err) {
                console.error(`  ❌ [CRASH] Click handler for ID '${id}' failed!`);
                console.error(err);
                clickErrors++;
            }
        }
    }
}

console.log('\n=== RUNTIME TEST SUMMARY ===');
if (failedEvents === 0 && clickErrors === 0) {
    console.log('🎉 ALL WEB RUNTIME TESTS PASSED WITH 0 ERRORS!');
    process.exit(0);
} else {
    console.error(`❌ Total Failures: ${failedEvents} event errors, ${clickErrors} click errors`);
    process.exit(1);
}
