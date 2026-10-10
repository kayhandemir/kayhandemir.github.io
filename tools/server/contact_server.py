#!/usr/bin/env python3
"""Contact form handler for ukgames.games.

nginx passes POST /api/contact here (127.0.0.1:8081). Each message is appended to MESSAGES_FILE and emailed to
CONTACT_TO through Gmail's SMTP server with an app password, with Reply-To set to the sender so a reply goes straight
back to them. Messages older than RETENTION_DAYS are dropped from the file (as the privacy policy says).

Spam guards: a hidden "website" field that people leave empty (bots fill it in), a per-IP limit, and size limits.
Settings come from the environment (systemd EnvironmentFile=/etc/ukgames-contact.env):
    SMTP_USER=ugka81@gmail.com
    SMTP_PASSWORD=<16-letter Gmail app password>
    CONTACT_TO=ugka81@gmail.com
Python standard library only.
"""

import json
import os
import re
import smtplib
import ssl
import sys
import threading
import time
from email.message import EmailMessage
from email.utils import formataddr
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

HOST = "127.0.0.1"
PORT = int(os.environ.get("CONTACT_PORT", "8081"))
MESSAGES_FILE = os.environ.get("MESSAGES_FILE", "/var/lib/ukgames-contact/messages.jsonl")
RETENTION_DAYS = 90
MAX_BODY_BYTES = 16 * 1024
MAX_NAME = 80
MAX_EMAIL = 120
MAX_MESSAGE = 4000
MIN_MESSAGE = 5
LIMIT_PER_HOUR = 5
EMAIL_PATTERN = re.compile(r"^[^@\s<>\"]+@[^@\s<>\"]+\.[^@\s<>\"]+$")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
CONTACT_TO = os.environ.get("CONTACT_TO", SMTP_USER)

_lock = threading.Lock()
_recent = {}  # ip -> [timestamps of accepted messages within the last hour]


def log(text):
    print(text, flush=True)


def is_rate_limited(ip):
    now = time.time()
    with _lock:
        times = [t for t in _recent.get(ip, []) if now - t < 3600]
        _recent[ip] = times
        if len(times) >= LIMIT_PER_HOUR:
            return True
        times.append(now)
        return False


def store(entry):
    """Appends the message and drops ones past RETENTION_DAYS."""
    cutoff = time.time() - RETENTION_DAYS * 86400
    os.makedirs(os.path.dirname(MESSAGES_FILE), exist_ok=True)
    with _lock:
        kept = []
        if os.path.exists(MESSAGES_FILE):
            with open(MESSAGES_FILE, encoding="utf-8") as f:
                for line in f:
                    try:
                        if json.loads(line).get("time", 0) >= cutoff:
                            kept.append(line.rstrip("\n"))
                    except ValueError:
                        continue
        kept.append(json.dumps(entry, ensure_ascii=False))
        with open(MESSAGES_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(kept) + "\n")


def send_email(entry):
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError("SMTP_USER / SMTP_PASSWORD are not set")
    msg = EmailMessage()
    msg["Subject"] = f"[ukgames.games] {entry['name']}"
    msg["From"] = formataddr(("UKGames website", SMTP_USER))
    msg["To"] = CONTACT_TO
    msg["Reply-To"] = formataddr((entry["name"], entry["email"]))
    msg.set_content(
        f"{entry['message']}\n\n"
        f"---\nName: {entry['name']}\nEmail: {entry['email']}\nPage language: {entry['lang']}\n"
        f"Sent: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(entry['time']))}\n"
        "Reply to this email to answer them.\n")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)


class Handler(BaseHTTPRequestHandler):
    server_version = "ukgames-contact"

    def log_message(self, fmt, *args):
        pass  # no per-request access log: nginx keeps one

    def reply(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path.split("?")[0] != "/api/contact":
            return self.reply(404, {"ok": False, "error": "not_found"})
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY_BYTES:
            return self.reply(413, {"ok": False, "error": "too_large"})
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        if "json" in (self.headers.get("Content-Type") or ""):
            try:
                data = json.loads(raw)
            except ValueError:
                return self.reply(400, {"ok": False, "error": "invalid"})
        else:
            data = {k: v[0] for k, v in parse_qs(raw).items()}

        # Honeypot: people never see this field; bots fill in every field. Pretend it worked.
        if str(data.get("website", "")).strip():
            return self.reply(200, {"ok": True})

        name = str(data.get("name", "")).strip()[:MAX_NAME]
        email = str(data.get("email", "")).strip()[:MAX_EMAIL]
        message = str(data.get("message", "")).strip()[:MAX_MESSAGE]
        lang = "tr" if str(data.get("lang", "")) == "tr" else "en"
        if not name or not EMAIL_PATTERN.match(email) or len(message) < MIN_MESSAGE:
            return self.reply(400, {"ok": False, "error": "invalid"})

        ip = self.headers.get("X-Real-IP") or self.client_address[0]
        if is_rate_limited(ip):
            return self.reply(429, {"ok": False, "error": "rate_limited"})

        entry = {"time": int(time.time()), "name": name, "email": email, "message": message, "lang": lang}
        try:
            store(entry)
        except OSError as ex:
            log(f"store failed: {ex}")
        try:
            send_email(entry)
        except Exception as ex:  # the message is stored; the developer sees it on the server
            log(f"email failed: {ex}")
            return self.reply(502, {"ok": False, "error": "send_failed"})
        log(f"message from {email} sent")
        return self.reply(200, {"ok": True})


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    log(f"contact server on {HOST}:{PORT}, sending to {CONTACT_TO or '(not set)'}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
