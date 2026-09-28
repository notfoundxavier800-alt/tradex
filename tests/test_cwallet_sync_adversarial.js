/**
 * Adversarial test harness for static/cwallet_sync.js extraction and parsing logic.
 */
const assert = require('assert');

function parseDOMText(text, state = { lastSec: null, currentPhase: 'BETTING' }) {
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

    var currentPhase = state.currentPhase;
    var lastSec = state.lastSec;

    if (sec !== null) {
        if (isBattleText) {
            currentPhase = 'BATTLE';
        } else if (sec > 5) {
            currentPhase = 'BETTING';
        } else if (sec <= 5) {
            if (lastSec !== null && lastSec <= 1 && currentPhase === 'BETTING') {
                currentPhase = 'BATTLE';
            } else if (lastSec !== null && lastSec <= 1 && currentPhase === 'BATTLE') {
                currentPhase = 'BETTING';
            }
        }
        lastSec = sec;
    }

    var willSendPayload = (sec !== null && sec >= 0 && sec <= 60);

    return {
        isBattleText,
        sec,
        p,
        currentPhase,
        lastSec,
        willSendPayload
    };
}

let totalTests = 0;
let passedTests = 0;
let failedTests = [];

function test(desc, fn) {
    totalTests++;
    try {
        fn();
        passedTests++;
        console.log(`  [PASS] ${desc}`);
    } catch (err) {
        failedTests.push({ desc, error: err.message });
        console.log(`  [FAIL] ${desc}: ${err.message}`);
    }
}

console.log("=== ADVERSARIAL STRESS TEST: cwallet_sync.js DOM EXTRACTION ===");

// Suite 1: Clean inputs
test("Clean Betting input", () => {
    const res = parseDOMText("Betting Phase 14s Strike: $65432.10");
    assert.strictEqual(res.sec, 14);
    assert.strictEqual(res.p, 65432.10);
    assert.strictEqual(res.currentPhase, 'BETTING');
    assert.strictEqual(res.willSendPayload, true);
});

test("Clean Battle input with explicit battle marker", () => {
    const res = parseDOMText("In Battle 04s Strike: $65432.10");
    assert.strictEqual(res.sec, 4);
    assert.strictEqual(res.p, 65432.10);
    assert.strictEqual(res.currentPhase, 'BATTLE');
    assert.strictEqual(res.willSendPayload, true);
});

// Suite 2: Malformed strings and special characters
test("Empty string", () => {
    const res = parseDOMText("");
    assert.strictEqual(res.sec, null);
    assert.strictEqual(res.p, null);
    assert.strictEqual(res.willSendPayload, false);
});

test("Corrupt noise and unicode emojis", () => {
    const res = parseDOMText("🚀🔥💣 @@##$$%% ^^&&** ((--))");
    assert.strictEqual(res.sec, null);
    assert.strictEqual(res.p, null);
    assert.strictEqual(res.willSendPayload, false);
});

test("HTML tags inside text", () => {
    const res = parseDOMText("<div class='countdown'>12s</div><span class='price'>Strike: $98765.43</span>");
    assert.strictEqual(res.sec, 12);
    assert.strictEqual(res.p, 98765.43);
    assert.strictEqual(res.currentPhase, 'BETTING');
    assert.strictEqual(res.willSendPayload, true);
});

// Suite 3: Missing seconds
test("Price only, missing seconds", () => {
    const res = parseDOMText("Current Price: $65000.00 BTC/USDT");
    assert.strictEqual(res.sec, null);
    assert.strictEqual(res.p, 65000.00);
    assert.strictEqual(res.willSendPayload, false);
});

// Suite 4: Non-numeric values
test("Non-numeric seconds '--s'", () => {
    const res = parseDOMText("Time left: --s Strike: $65000.00");
    assert.strictEqual(res.sec, null);
    assert.strictEqual(res.willSendPayload, false);
});

test("Non-numeric strike price 'Strike: pending'", () => {
    const res = parseDOMText("Time left: 10s Strike: pending");
    assert.strictEqual(res.sec, 10);
    assert.strictEqual(res.p, null);
    assert.strictEqual(res.willSendPayload, true);
});

// Suite 5: Fallback price extraction
test("Fallback price when no label keyword exists", () => {
    const res = parseDOMText("15s 67890.12");
    assert.strictEqual(res.sec, 15);
    assert.strictEqual(res.p, 67890.12);
});

// Suite 6: Sequential phase transitions
test("Sequential countdown through round cycle (15s down to 0s betting, then 5s battle, then 15s betting)", () => {
    let state = { lastSec: null, currentPhase: 'BETTING' };
    
    // Betting 15s -> 0s
    for (let s = 15; s >= 0; s--) {
        const res = parseDOMText(`Round 1234: ${s}s Strike: $65000.00`, state);
        state.lastSec = res.lastSec;
        state.currentPhase = res.currentPhase;
        assert.strictEqual(res.currentPhase, 'BETTING', `Failed at betting ${s}s`);
    }

    // Battle starts at 5s
    const battle5 = parseDOMText("Round 1234: 5s Strike: $65000.00", state);
    state.lastSec = battle5.lastSec;
    state.currentPhase = battle5.currentPhase;
    assert.strictEqual(battle5.currentPhase, 'BATTLE', "Failed transition to BATTLE at 5s after 0s");

    // Battle countdown 4s -> 0s
    for (let s = 4; s >= 0; s--) {
        const res = parseDOMText(`Round 1234: ${s}s Strike: $65000.00`, state);
        state.lastSec = res.lastSec;
        state.currentPhase = res.currentPhase;
        assert.strictEqual(res.currentPhase, 'BATTLE', `Failed at battle ${s}s`);
    }

    // New round starts at 15s (or 5s without label)
    const nextRound = parseDOMText("Round 1235: 15s Strike: $65000.00", state);
    assert.strictEqual(nextRound.currentPhase, 'BETTING', "Failed transition back to BETTING at 15s");
});

// Suite 7: Simultaneous 'Battle' and 'Betting' text
test("DOM contains 'Market Battle' game title and 'Betting Phase: 12s'", () => {
    const res = parseDOMText("Cwallet Market Battle - Betting Phase 12s Strike $65000.00");
    assert.strictEqual(res.sec, 12);
    assert.strictEqual(res.isBattleText, false);
    assert.strictEqual(res.currentPhase, 'BETTING');
});

test("DOM contains 'In Battle' label AND 'Betting Phase 12s' (e.g. status bar)", () => {
    const res = parseDOMText("Status: In Battle (0/10) | Betting Phase 12s Strike $65000.00");
    console.log("    [Detail] Simultaneous test result:", {
        isBattleText: res.isBattleText,
        currentPhase: res.currentPhase,
        sec: res.sec
    });
    // Let's see how current code handles it
});

console.log(`\nResults: ${passedTests}/${totalTests} passed, ${failedTests.length} failed.`);
if (failedTests.length > 0) {
    process.exit(1);
} else {
    process.exit(0);
}
