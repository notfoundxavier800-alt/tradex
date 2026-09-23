"""
notifier.py — High-Priority Desktop Notification Engine for tradex
Fires native Windows Toast Notifications for all 99% accuracy sniper and signal calls.
"""
import subprocess
import threading
import sys
import os

def _send_windows_toast(title: str, message: str):
    if sys.platform != "win32":
        return
    try:
        safe_title = title.replace('"', "'")
        safe_msg = message.replace('"', "'")
        ps_script = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
        $textNodes = $template.GetElementsByTagName("text")
        $textNodes.Item(0).AppendChild($template.CreateTextNode("{safe_title}")) | Out-Null
        $textNodes.Item(1).AppendChild($template.CreateTextNode("{safe_msg}")) | Out-Null
        $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("tradex")
        $notification = [Windows.UI.Notifications.ToastNotification]::new($template)
        $notifier.Show($notification)
        '''
        flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            timeout=4,
            creationflags=flags
        )
    except Exception:
        pass

_last_notified_round = -1
_last_notified_dir = ""
_notif_lock = threading.Lock()

def send_signal_notification(direction: str, confidence: float = 99.0, price: float = 0.0, strike: float = 0.0, strength: str = "99% ACCURACY", round_id: int = -1):
    global _last_notified_round, _last_notified_dir

    dir_upper = direction.upper()
    # 1. Do NOT spam user with PASS or WAIT notifications
    if dir_upper not in ("UP", "DOWN"):
        return

    # 2. Strict single-fire deduplication per round (STRICTLY ONCE per round, never repeat)
    with _notif_lock:
        if round_id != -1:
            if round_id == _last_notified_round:
                return  # Already notified for this round!
            _last_notified_round = round_id
            _last_notified_dir = dir_upper

    def _worker():
        delta_str = ""
        if strike and strike > 0 and price > 0:
            diff = price - strike
            delta_str = f" | Δ {'+' if diff >= 0 else ''}${diff:.2f}"
        
        dir_emoji = "🟢" if dir_upper == "UP" else "🔴"
        title = f"{dir_emoji} tradex: BET {dir_upper} NOW ({confidence:.0f}%)"
        message = f"Action: Bet {dir_upper} on Cwallet! Strike: ${strike:.2f}{delta_str} | {strength}"
        _send_windows_toast(title, message)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
