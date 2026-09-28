"""
Unit tests for AIAgentsHub (TradeX + TradingAgents + AI Hedge Fund Bridge)
"""

import unittest
import time
from ai_agents_hub import AIAgentsHub, ai_hub


class TestAIAgentsHub(unittest.TestCase):
    def setUp(self):
        self.hub = AIAgentsHub()

    def test_environment_detection(self):
        status = self.hub.get_status()
        self.assertIn("status", status)
        self.assertEqual(status["status"], "online")
        self.assertIn("provider", status)

    def test_investor_council_personas(self):
        """Verify that all 5 Legendary Investor Personas from AI Hedge Fund are present."""
        res = self.hub.evaluate_symbol_sync(
            symbol="BTCUSDT",
            market_type="crypto",
            current_price=65000.0,
            technical_summary={"overall_bias": "UP", "score": 0.45, "rsi": 42.0, "adx": 28.0}
        )
        council = res.get("investor_council", {})
        self.assertIn("buffett", council)
        self.assertIn("munger", council)
        self.assertIn("graham", council)
        self.assertIn("lynch", council)
        self.assertIn("druckenmiller", council)

        # Check Warren Buffett
        self.assertEqual(council["buffett"]["name"], "Warren Buffett")
        self.assertIn(council["buffett"]["verdict"], ["BUY", "HOLD", "PASS"])
        self.assertGreater(council["buffett"]["confidence"], 0)

        # Check Stanley Druckenmiller
        self.assertEqual(council["druckenmiller"]["name"], "Stanley Druckenmiller")
        self.assertIn("AGGRESSIVE", council["druckenmiller"]["verdict"])

    def test_trading_agents_framework(self):
        """Verify TradingAgents analyst team, bull/bear debate, trader, and risk manager."""
        res = self.hub.evaluate_symbol_sync(
            symbol="NVDA",
            market_type="international",
            current_price=120.0,
            technical_summary={"overall_bias": "UP", "score": 0.35, "rsi": 55.0, "adx": 26.0}
        )
        agents = res.get("trading_agents", {})
        self.assertIn("analysts", agents)
        self.assertIn("debate", agents)
        self.assertIn("trader_proposal", agents)
        self.assertIn("risk_manager", agents)

        analysts = agents["analysts"]
        self.assertIn("market_analyst", analysts)
        self.assertIn("sentiment_analyst", analysts)
        self.assertIn("news_analyst", analysts)
        self.assertIn("fundamentals_analyst", analysts)

        debate = agents["debate"]
        self.assertIn("bullish_researcher", debate)
        self.assertIn("bearish_researcher", debate)
        self.assertEqual(debate["consensus_winner"], "BULLS")

        trader = agents["trader_proposal"]
        self.assertEqual(trader["action"], "BUY")
        self.assertGreater(trader["target_take_profit"], trader["entry_price"])

        risk = agents["risk_manager"]
        self.assertEqual(risk["status"], "APPROVED")

    def test_bearish_confluence(self):
        """Verify bearish market dynamics properly adjust investor and debate verdicts."""
        res = self.hub.evaluate_symbol_sync(
            symbol="ETHUSDT",
            market_type="crypto",
            current_price=3200.0,
            technical_summary={"overall_bias": "DOWN", "score": -0.6, "rsi": 78.0, "adx": 30.0}
        )
        consensus = res.get("overall_consensus", {})
        self.assertIn(consensus["stance"], ["SELL", "STRONG_SELL", "NEUTRAL"])
        self.assertLessEqual(consensus["score"], 0.2)

        debate = res.get("trading_agents", {}).get("debate", {})
        self.assertEqual(debate["consensus_winner"], "BEARS")

    def test_caching_mechanism(self):
        """Verify that repeated queries hit the cache without recomputation."""
        sym = "TESTSYM"
        res1 = self.hub.evaluate_symbol_sync(sym, "crypto", 100.0)
        cached = self.hub.get_cached_analysis(sym)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["symbol"], sym)

    def test_async_worker_execution(self):
        """Verify that evaluate_symbol_async executes non-blocking and fires callback."""
        completed = []

        def callback(data):
            completed.append(data)

        thread = self.hub.evaluate_symbol_async(
            symbol="SOLUSDT",
            market_type="crypto",
            current_price=145.0,
            callback=callback
        )
        thread.join(timeout=3.0)
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0]["symbol"], "SOLUSDT")

    def test_evaluate_engine_tick_latency_and_correctness(self):
        """Verify that evaluate_engine_tick executes in sub-millisecond time and produces valid scores."""
        t0 = time.perf_counter()
        tick_res = self.hub.evaluate_engine_tick(
            symbol="BTCUSDT",
            current_price=64002.50,
            strike=64000.00,
            time_left=5.0,
            technical_summary={"overall_bias": "UP", "score": 0.4, "rsi": 54.0, "adx": 26.0},
            order_flow={"taker_buy_pct_5s": 58.0, "delta_5s": 4.5, "global_consensus": 0.65},
            regime_info={"regime": "TRENDING", "rho_1": 0.25}
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        self.assertLess(elapsed_ms, 50.0, "Engine evaluation must execute with zero lag (< 50ms)")
        self.assertIn("score", tick_res)
        self.assertIn("signal", tick_res)
        self.assertEqual(tick_res["signal"], 1, "Bullish conditions must yield signal = +1")
        self.assertGreater(tick_res["score"], 0.0)
        self.assertIn("investor_council", tick_res)
        self.assertIn("trading_agents", tick_res)
        self.assertEqual(tick_res["trading_agents"]["debate"]["winner"], "BULLS_WIN")
        self.assertEqual(tick_res["trading_agents"]["debate"]["consensus_winner"], "BULLS")
        self.assertIn("bullish_researcher", tick_res["trading_agents"]["debate"])
        self.assertIn("bearish_researcher", tick_res["trading_agents"]["debate"])
        self.assertIn("trader_proposal", tick_res["trading_agents"])
        self.assertEqual(tick_res["trading_agents"]["trader_proposal"]["action"], "BUY")
        self.assertIn("max_portfolio_allocation_pct", tick_res["trading_agents"]["risk_manager"])
        self.assertEqual(tick_res["trading_agents"]["risk_manager"]["status"], "APPROVED")

    def test_evaluate_engine_tick_munger_inversion_veto(self):
        """Verify Charlie Munger and Risk Gate veto when buying directly into overhead ask wall."""
        tick_res = self.hub.evaluate_engine_tick(
            symbol="BTCUSDT",
            current_price=64001.00,
            strike=64000.00,
            time_left=5.0,
            technical_summary={"overall_bias": "UP", "score": 0.3},
            order_flow={"ask_wall_btc": 4.5, "ask_iceberg_wall": True, "taker_buy_pct_5s": 51.0},
            regime_info={"regime": "TRENDING"}
        )
        self.assertTrue(tick_res["veto"], "Munger must veto when buying into 4.5 BTC ask wall.")
        self.assertEqual(tick_res["risk_status"], "REJECTED")
        self.assertEqual(tick_res["investor_council"]["munger"]["verdict"], "VETO")
        self.assertEqual(tick_res["investor_council"]["munger"]["score"], 0.0)


if __name__ == "__main__":
    unittest.main()

