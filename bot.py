#!/usr/bin/env python3
"""
bot.py — Main Entry Point

Start the CW Signal Bot with a single command:
    python bot.py

Optional CLI arguments:
    --port PORT        Web dashboard port  (default: 5000)
    --interval SECS    Analysis interval   (default: 3)
    --host HOST        Bind address        (default: 127.0.0.1)
"""

import argparse
import sys
import webbrowser
import threading

# Ensure UTF-8 unbuffered output on Windows
sys.stdout.reconfigure(line_buffering=True, encoding='utf-8', errors='replace')
sys.stderr.reconfigure(line_buffering=True, encoding='utf-8', errors='replace')


def main():
    parser = argparse.ArgumentParser(
        description="CW Signal Bot — BTC/USDT Market Battle Predictor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bot.py                       # Start with defaults
  python bot.py --port 8080           # Use port 8080
  python bot.py --interval 2          # Analyse every 2 seconds
  python bot.py --no-browser          # Don't auto-open browser
        """,
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the web server to (default: 0.0.0.0)",
    )
    import os
    default_port = int(os.environ.get("PORT", 5000))
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help="Port for the web dashboard (default: 5000 or $PORT)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Seconds between each analysis cycle (default: 0.5)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't auto-open the dashboard in the browser",
    )

    args = parser.parse_args()

    # Print banner
    print()
    print("  +-----------------------------------------------+")
    print("  |        CW Signal Bot  v1.0                     |")
    print("  |   BTC/USDT Market Battle Signal Predictor      |")
    print("  +-----------------------------------------------+")
    print()
    print(f"  Analysis interval : {args.interval}s")
    print(f"  Dashboard         : http://{args.host}:{args.port}")
    print(f"  Data source       : Binance WebSocket (BTC/USDT)")
    print()
    print("  Press Ctrl+C to stop the bot.")
    print()

    # Auto-open browser after a short delay
    if not args.no_browser:
        def open_browser():
            import time
            time.sleep(2.5)
            browser_host = "127.0.0.1" if args.host == "0.0.0.0" else args.host
            url = f"http://{browser_host}:{args.port}"
            print(f"[Browser] Opening dashboard: {url}")
            webbrowser.open(url)

        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()

    # Import and start the server
    # (import here so argparse --help works without needing all dependencies)
    try:
        from server import start_bot
    except ImportError as e:
        print(f"\n❌ Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        sys.exit(1)

    start_bot(host=args.host, port=args.port, interval=args.interval)


if __name__ == "__main__":
    main()
