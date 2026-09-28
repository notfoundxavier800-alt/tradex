# Original User Request

## 2026-09-24T03:41:30Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Full multi-agent team

End-to-end overhaul and calibration of the Cwallet Market Battle Signal Bot (TradeX) to guarantee exact 5.0-second countdown sniper execution, seamless bidirectional clock and strike price synchronization with Cwallet, intelligent venue pricing alignment (Binance Futures vs. Spot), and true high-probability directional accuracy.

Working directory: `C:\Users\divya\Desktop\tradex` (and mirrored to `C:\Users\divya\.gemini\antigravity\scratch\cwallet-signal-bot`)
Integrity mode: development

## Requirements

### R1. Exact 5.0s Betting Timer Sniper Trigger
- Ensure the sniper prediction triggers authoritatively at exactly 5 seconds remaining on the 15-second betting timer ($T-5\text{s}$ mark), giving the user exactly 5.0 seconds to execute on Cwallet before the round closes at $0\text{s}$.
- Eradicate all latency delays, eliminating client polling pauses and ensuring sub-millisecond audio and haptic delivery.

### R2. Flawless Cwallet Clock & Phase Synchronization
- Fix round epoch mapping in `round_manager.py` so syncing to the Cwallet betting timer ($15\text{s} \rightarrow 0\text{s}$) correctly aligns the 20-second continuous round epoch without phase inversion or premature battle transitions.
- Support both 1-click manual sync buttons and real-time auto-sync bookmarklet streaming with automatic phase detection (`BETTING` vs `BATTLE`).

### R3. Intelligent Venue Price Alignment (Binance Futures vs Spot)
- Auto-detect whether Cwallet is quoting Binance Futures (USDT-M Perpetual) or Binance Spot based on proximity to the active round strike price $K$.
- Automatically align the bot's live reference price and strike delta to the matching exchange venue to eliminate any basis spread discrepancy.
- Provide a clean 1-click toggle on the UI (`AUTO`, `FUTURES`, `SPOT`) to ensure zero strike drift between Cwallet and TradeX.

### R4. Calibrated 24-Vector Confluence & Win Rate Optimization
- Remove unrealistic clearance hurdles (e.g. $16 on BTC) and single-point vetoes (such as false market freeze or Feller flags), replacing them with realistic volatility-scaled clearance ($\approx \$0.75 - \$1.50$ on BTC).
- Enforce true democratic 24-vector confluence ($\ge 13/24$ vectors aligned with $\ge 3$ directional lead) to guarantee forward 5-second battle win persistence while shielding capital during flat chop.
- Prevent contradictory cross-venue comparisons (such as raw Coinbase USD vs Binance USDT).

### R5. Real-Time HUD & Dual Workspace Mirroring
- Update dashboard countdown HUD, audio alerts, and mobile notifications to reflect the exact 15s betting and 5s battle lifecycle.
- Mirror all validated code changes between `C:\Users\divya\Desktop\tradex` and `C:\Users\divya\.gemini\antigravity\scratch\cwallet-signal-bot` and ensure all automated tests pass.

## Acceptance Criteria

### Timing & Synchronization
- [ ] Sniper prediction event fires at exactly `phase_seconds_left == 5.0s` on every active round.
- [ ] Manual and auto-sync correctly set the betting phase countdown ($15\text{s} \rightarrow 0\text{s}$) without jumping prematurely into the battle phase.
- [ ] Live price delta between Cwallet strike and TradeX is $< \$0.50$ when venue auto-detection is active.

### Signal Accuracy & Gating
- [ ] 114/114 automated tests pass with zero regressions (`python -m unittest discover -s tests -p "test_*.py"`).
- [ ] Confluence engine delivers clean `UP` or `DOWN` signals with $\ge 97.5\%$ confidence on qualified breakouts and safely issues `CAPITAL SHIELD PASS` during flat chop.
- [ ] No false "FELLER VOL EXPLOSION" or "MARKET FROZEN" vetoes when active trading is taking place.

### System Verification & Workspace Mirroring
- [ ] Automated end-to-end simulation validates that a simulated $+3.50$ breakout generates an `UP` prediction and a $-3.50$ breakdown generates a `DOWN` prediction.
- [ ] All code modifications are mirrored cleanly between `Desktop\tradex` and `scratch\cwallet-signal-bot` with zero compile errors.

## 2026-09-28T12:37:10Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Full multi-agent team

End-to-end bug eradication and quantitative institutional overhaul of the Cwallet Market Battle Signal Bot (TradeX), integrating deep Renaissance Technologies statistical arbitrage theories, advanced market microstructure engines, and a calibrated 26-vector confluence hierarchy to achieve >= 98% directional accuracy on qualified breakouts while safeguarding capital during noise.

Working directory: `C:\Users\divya\Desktop\tradex` (and mirrored to `C:\Users\divya\.gemini\antigravity\scratch\cwallet-signal-bot`)
Integrity mode: development

## Requirements

### R1. Comprehensive Bug Eradication & Zero-Defect State Management
- Eliminate all remaining runtime bugs, edge cases, and race conditions across round lifecycle transitions, clock synchronizers, venue price switches, and WebSocket reconnections.
- Guarantee that `RoundManager` strike price K, delta, and phase timers reset cleanly on every round transition without stale price leakage or latching.
- Ensure sub-50ms execution latency for both server-side sniper dispatch and client-side HUD/audio alerts at the exact T-5s mark of the betting window.

### R2. Deep Renaissance Technologies Quantitative Theories & Statistical Engines
- Expand the quantitative math core by integrating institutional-grade mathematical models inspired by Jim Simons and Renaissance Technologies:
  1. **Hidden Semi-Markov Micro-Regime Transitions (HSMM)**: High-order state transition probability matrix distinguishing between persistent trending momentum, mean-reverting chop, and jump-diffusion expansion.
  2. **Ornstein-Uhlenbeck (OU) Mean-Reversion SDE Solver**: Continuous-time parameter estimation (theta, mu, sigma) calculating instantaneous mean-reversion pull and identifying overextended blow-off exhaustion limits (|Z| > 1.8 sigma).
  3. **Hawkes Self-Exciting Point Process**: Real-time order arrival intensity estimation (lambda(t) = mu + sum alpha * exp(-beta * (t - t_i))) and branching ratio eta to detect predatory order cascades and liquidity vacuums.
  4. **Bouchaud Transient Price Impact Propagator**: Non-linear market impact model with power-law kernel decay G(tau) ~ tau^-gamma quantifying trade footprint absorption.
  5. **Cont-Stoikov L2 Queue Gradient & Avellaneda-Stoikov Reservation Skew**: Microstructure order book dynamics calculating bid/ask replenishment vs. depletion velocity and dealer inventory risk skew.
  6. **Merton Jump-Diffusion Compound Poisson PDE**: Explicit probability computation Phi(d) of forward price trajectories breaching strike K over the remaining battle duration tau.

### R3. Calibrated 26-Vector Confluence & >= 98% Directional Precision Gating
- Enforce a strict democratic conviction matrix: require >= 18/26 aligned vectors with a minimum +4 directional lead before generating actionable UP or DOWN signals.
- **AI Investor Council & Multi-Agent Priority (30% composite weight)**:
  - AI Hedge Fund Council (Buffett, Graham, Munger, Lynch, Druckenmiller) and TradingAgents Multi-Agent Debate & Risk Management Gate maintain primary veto authority.
  - No trade may execute contrary to an active AI Council mandate or Munger Inversion Risk Gate rejection.
- Dynamic volatility-scaled strike clearance hurdle (~$0.65 - $1.50 on BTC): strictly prohibit 50/50 coin-flip gambles near strike, issuing CAPITAL SHIELD PASS (0x Kelly unit) whenever edge is insufficient.

### R4. Intelligent Venue Alignment & Multi-Exchange Order Flow Triangulation
- Synchronize price references between Binance Futures (USDT-M Perpetual), Binance Spot, and Coinbase Pro with zero cross-venue basis distortion.
- Auto-detect Cwallet's active reference venue using real-time distance proximity to Cwallet strike K with < $0.50 basis spread tolerance.
- Maintain synchronized order book depth ladders, cumulative volume delta (CVD), and informed order flow toxicity (VPIN) metrics.

### R5. Dual-Workspace Mirroring & Automated Test Verification
- Ensure 100% of automated tests pass without errors across both repositories:
  - `C:\Users\divya\Desktop\tradex`
  - `C:\Users\divya\.gemini\antigravity\scratch\cwallet-signal-bot`
- Validate end-to-end signal emission, WebSocket contract integrity, and zero regressions across all existing test suites.

## Acceptance Criteria

### Mathematical Engine & Theory Depth
- [ ] All 6 Renaissance and microstructure quantitative models (HSMM, OU SDE, Hawkes Process, Bouchaud Propagator, Cont-Stoikov, Merton Jump-Diffusion) are fully implemented and verified with unit tests.
- [ ] Confluence engine incorporates all 26 vectors with AI Council holding 30% priority weight and strict risk veto authority.
- [ ] Volatility-calibrated clearance threshold prevents trade generation on flat chop (delta < clearanceThresh outputs WAIT / PASS).

### Signal Quality & Precision
- [ ] Confluence engine achieves >= 98% win probability confidence on all qualified UP and DOWN sniper signals.
- [ ] Absolute sanity guard enforced: no UP signal can ever fire when delta < -0.05$, and no DOWN signal can ever fire when delta > +0.05$ under any circumstances.
- [ ] Capital Shield activates reliably during flat chop, low volume, or contradictory order flow, preserving capital with 0x unit allocation.

### System Timing, Stability, & Synchronization
- [ ] Sniper prediction event fires with <= 50ms latency at the T-5s mark of the 15-second betting window.
- [ ] Clock and phase synchronization correctly aligns 20s round epochs (15s betting + 5s combat battle) with zero strike price freeze or stale data leakage.
- [ ] 100% automated test suite passes cleanly across both workspaces (Desktop\tradex and scratch\cwallet-signal-bot).

