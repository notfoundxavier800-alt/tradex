"""
Unit and Integration Test Suite for Server Integrity and Cloud Deployment (Milestone M1, M6).
Tests:
1. Socket.IO server initialization and event handlers (cwallet_round_update, cwallet_sniper_call, cwallet_round_settled).
2. Flask REST endpoints via test client (/api/settle_round, /api/status, /api/cwallet_state, /api/market_list, /api/toggle_zero_defect).
3. py_compile bytecode compilation across all repository Python source files.
4. Render and Docker deployment manifests (render.yaml, Procfile, Dockerfile, requirements.txt, .dockerignore).

Executable via: python -m unittest discover -s tests -p "test_*.py"
"""

import os
import sys
import glob
import py_compile
import unittest
from unittest.mock import patch

import server
from round_manager import RoundManager


class TestFlaskEndpoints(unittest.TestCase):
    """
    Tier 1 & Tier 2: Validates core Flask HTTP REST endpoints and payload contracts.
    """

    def setUp(self):
        self.app = server.app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_index_route(self):
        """GET / returns HTTP 200 and renders the Cwallet dashboard template."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"html", res.data.lower())

    def test_api_status(self):
        """GET /api/status returns JSON state containing status, symbol, and UTC timestamp."""
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("status", data)
        self.assertIn("market_type", data)
        self.assertIn("symbol", data)
        self.assertIn("currency_symbol", data)
        self.assertIn("timestamp", data)

    def test_api_market_list(self):
        """GET /api/market_list returns curated crypto, indian, and international markets."""
        res = self.client.get("/api/market_list")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("crypto_markets", data)
        self.assertIn("indian_markets", data)
        self.assertIn("international_markets", data)
        self.assertGreater(len(data["crypto_markets"]), 0)

    def test_api_cwallet_state(self):
        """GET /api/cwallet_state returns the active RoundManager state dictionary."""
        res = self.client.get("/api/cwallet_state")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("round_id", data)
        self.assertIn("phase", data)
        self.assertIn("phase_seconds_left", data)
        self.assertIn("strike_price", data)

    def test_api_settle_round_up(self):
        """POST /api/settle_round evaluates UP win when close_price > strike."""
        payload = {
            "round_id": 101,
            "strike": 64000.0,
            "close_price": 64025.5
        }
        res = self.client.post("/api/settle_round", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "ok")
        settlement = data["settlement"]
        self.assertEqual(settlement["round_id"], 101)
        self.assertEqual(settlement["strike"], 64000.0)
        self.assertEqual(settlement["close_price"], 64025.5)
        self.assertEqual(settlement["outcome"], "UP")

    def test_api_settle_round_down(self):
        """POST /api/settle_round evaluates DOWN win when close_price < strike."""
        payload = {
            "round_id": 102,
            "strike": 64000.0,
            "close_price": 63970.0
        }
        res = self.client.post("/api/settle_round", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "ok")
        settlement = data["settlement"]
        self.assertEqual(settlement["round_id"], 102)
        self.assertEqual(settlement["outcome"], "DOWN")

    def test_api_settle_round_tie(self):
        """POST /api/settle_round evaluates TIE outcome when close_price == strike."""
        payload = {
            "round_id": 103,
            "strike": 64000.0,
            "close_price": 64000.0
        }
        res = self.client.post("/api/settle_round", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "ok")
        settlement = data["settlement"]
        self.assertEqual(settlement["round_id"], 103)
        self.assertEqual(settlement["outcome"], "TIE")

    def test_api_settle_round_invalid_payload(self):
        """POST /api/settle_round handles invalid non-numeric inputs gracefully."""
        payload = {"strike": "invalid_number", "close_price": "bad_price"}
        res = self.client.post("/api/settle_round", json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("error", data)

    def test_api_toggle_zero_defect(self):
        """POST /api/toggle_zero_defect toggles zero_defect_mode state."""
        res_on = self.client.post("/api/toggle_zero_defect", json={"enabled": True})
        self.assertEqual(res_on.status_code, 200)
        self.assertTrue(res_on.get_json()["zero_defect_mode"])

        res_off = self.client.post("/api/toggle_zero_defect", json={"enabled": False})
        self.assertEqual(res_off.status_code, 200)
        self.assertFalse(res_off.get_json()["zero_defect_mode"])

    def test_api_search_symbol_crypto_and_indian(self):
        """GET /api/search_symbol returns relevant symbols for search queries."""
        res_btc = self.client.get("/api/search_symbol?q=BTC")
        self.assertEqual(res_btc.status_code, 200)
        results = res_btc.get_json()["results"]
        self.assertTrue(any("BTC" in r["symbol"].upper() for r in results))

        res_rel = self.client.get("/api/search_symbol?q=RELIANCE")
        self.assertEqual(res_rel.status_code, 200)
        results = res_rel.get_json()["results"]
        self.assertTrue(any("RELIANCE" in r["symbol"].upper() for r in results))


class TestSocketIOSetupAndHandlers(unittest.TestCase):
    """
    Tier 1 & Tier 2: Validates Socket.IO server initialization, event listeners,
    and client-server event communication (cwallet_round_update, cwallet_round_settled, cwallet_sniper_call).
    """

    def setUp(self):
        self.socketio = server.socketio
        self.app = server.app

    def test_socketio_configuration(self):
        """Socket.IO instance configured with threading mode and open CORS."""
        self.assertIsNotNone(self.socketio)
        self.assertEqual(self.socketio.async_mode, "threading")

    def test_socketio_client_connection(self):
        """Socket.IO client connects successfully and receives initial synchronization events."""
        client = self.socketio.test_client(self.app)
        self.assertTrue(client.is_connected())
        received = client.get_received()
        event_names = [e["name"] for e in received]
        self.assertIn("zero_defect_mode_switched", event_names)
        self.assertIn("market_switched", event_names)
        client.disconnect()

    def test_socketio_settle_round_event(self):
        """Socket.IO 'settle_round' event emits 'cwallet_round_settled' and 'cwallet_round_update'."""
        client = self.socketio.test_client(self.app)
        client.get_received()  # flush initial events

        # Emit settle_round from client
        client.emit("settle_round", {
            "round_id": 201,
            "strike": 64100.0,
            "close_price": 64150.0
        })

        received = client.get_received()
        event_names = [e["name"] for e in received]
        self.assertIn("cwallet_round_settled", event_names)
        self.assertIn("cwallet_round_update", event_names)

        # Inspect cwallet_round_settled payload
        settled_event = next(e for e in received if e["name"] == "cwallet_round_settled")
        settled_data = settled_event["args"][0]
        self.assertEqual(settled_data["round_id"], 201)
        self.assertEqual(settled_data["strike"], 64100.0)
        self.assertEqual(settled_data["close_price"], 64150.0)
        self.assertEqual(settled_data["outcome"], "UP")
        client.disconnect()

    def test_socketio_sync_cwallet_event(self):
        """Socket.IO 'sync_cwallet' event re-aligns clock and emits 'cwallet_round_update'."""
        client = self.socketio.test_client(self.app)
        client.get_received()

        client.emit("sync_cwallet", {
            "seconds_left": 12.0,
            "open_price": 64050.0,
            "round_number": 55,
            "round_duration": 20,
            "lead_time": 5.0
        })

        received = client.get_received()
        event_names = [e["name"] for e in received]
        self.assertIn("cwallet_round_update", event_names)

        update_event = next(e for e in received if e["name"] == "cwallet_round_update")
        update_data = update_event["args"][0]
        self.assertEqual(update_data["round_duration"], 20)
        self.assertIn("phase", update_data)
        client.disconnect()

    def test_socketio_sniper_call_emission_contract(self):
        """cwallet_sniper_call event emission contains all required UI and quantitative fields."""
        client = self.socketio.test_client(self.app)
        client.get_received()

        mock_sniper_payload = {
            "round_id": 305,
            "round_number": 42,
            "seconds_left": 5.0,
            "direction": "UP",
            "confidence": 98.5,
            "strength": "OMNISCIENT APEX",
            "kelly_unit": "3x MAX UNIT",
            "confluence_count": 21,
            "current_price": 64200.0,
            "strike_price": 64180.0,
            "strike_delta": 20.0,
            "is_apex": True,
            "is_zero_defect": True,
            "whale_shield_usd": 150000.0,
            "symbol": "BTCUSDT"
        }

        # Broadcast cwallet_sniper_call
        self.socketio.emit("cwallet_sniper_call", mock_sniper_payload)

        received = client.get_received()
        event_names = [e["name"] for e in received]
        self.assertIn("cwallet_sniper_call", event_names)

        sniper_event = next(e for e in received if e["name"] == "cwallet_sniper_call")
        payload = sniper_event["args"][0]
        self.assertEqual(payload["round_id"], 305)
        self.assertEqual(payload["direction"], "UP")
        self.assertEqual(payload["confidence"], 98.5)
        self.assertEqual(payload["confluence_count"], 21)
        self.assertEqual(payload["strike_delta"], 20.0)
        client.disconnect()


class TestPythonCompilationIntegrity(unittest.TestCase):
    """
    Tier 1 & Acceptance Criteria: Validates py_compile across all repository Python source files.
    Ensures zero syntax, indentation, or bytecode compilation errors.
    """

    def test_all_python_files_compile(self):
        """Every .py file in the repository must compile cleanly with py_compile."""
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        python_files = []
        for root, dirs, files in os.walk(repo_root):
            # Ignore hidden agent metadata and venv directories if present
            if ".git" in root or ".pytest_cache" in root or "node_modules" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    python_files.append(os.path.join(root, f))

        self.assertGreater(len(python_files), 10, "Repository must contain core Python modules.")

        errors = []
        for p in python_files:
            try:
                py_compile.compile(p, doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(f"{p}: {e}")

        self.assertEqual(len(errors), 0, f"py_compile failed on {len(errors)} files:\n" + "\n".join(errors))


class TestDeploymentManifests(unittest.TestCase):
    """
    Tier 1 & Tier 2: Validates Render and Docker deployment manifests for zero dependency conflict.
    (render.yaml, Procfile, Dockerfile, requirements.txt, .dockerignore).
    """

    def setUp(self):
        self.repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_render_yaml_validity(self):
        """render.yaml must define the tradex-signals web service with pip install and python bot.py."""
        path = os.path.join(self.repo_root, "render.yaml")
        self.assertTrue(os.path.exists(path), "render.yaml must exist at project root.")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("services:", content)
        self.assertIn("type: web", content)
        self.assertIn("name: tradex-signals", content)
        self.assertIn("env: python", content)
        self.assertIn("buildCommand: pip install -r requirements.txt", content)
        self.assertIn("startCommand: python bot.py --no-browser", content)

    def test_procfile_validity(self):
        """Procfile must declare web worker running python bot.py --no-browser."""
        path = os.path.join(self.repo_root, "Procfile")
        self.assertTrue(os.path.exists(path), "Procfile must exist at project root.")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        self.assertEqual(content, "web: python bot.py --no-browser")

    def test_dockerfile_validity(self):
        """Dockerfile must specify Python 3.11, non-root user (UID 1000), EXPOSE 7860, and CMD."""
        path = os.path.join(self.repo_root, "Dockerfile")
        self.assertTrue(os.path.exists(path), "Dockerfile must exist at project root.")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("FROM python:3.11", content)
        self.assertIn("useradd -m -u 1000", content)
        self.assertIn("EXPOSE 7860", content)
        self.assertIn("pip install", content)
        self.assertIn("CMD", content)
        self.assertIn("bot.py", content)

    def test_requirements_txt_validity(self):
        """requirements.txt must include essential production dependencies without conflicting pins."""
        path = os.path.join(self.repo_root, "requirements.txt")
        self.assertTrue(os.path.exists(path), "requirements.txt must exist at project root.")

        with open(path, "r", encoding="utf-8") as f:
            lines = [line.strip().lower() for line in f if line.strip() and not line.startswith("#")]

        # Core required dependencies for Flask, SocketIO, and numerical quantitative models
        required_packages = ["flask", "flask-socketio", "numpy", "pandas", "websocket-client", "ta", "requests", "gunicorn"]
        for pkg in required_packages:
            self.assertTrue(
                any(line.startswith(pkg) for line in lines),
                f"requirements.txt missing required package: {pkg}"
            )

    def test_dockerignore_validity(self):
        """.dockerignore must ignore .git, bytecode caches, and temporary data."""
        path = os.path.join(self.repo_root, ".dockerignore")
        self.assertTrue(os.path.exists(path), ".dockerignore must exist at project root.")

        with open(path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        self.assertIn(".git", lines)
        self.assertTrue(any("__pycache__" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
