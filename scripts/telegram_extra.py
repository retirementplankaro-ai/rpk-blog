"""Extra Telegram channel posts between article posts (free, runs on GitHub Actions).
  python scripts/telegram_extra.py calculator   -> calculator of the day (1 PM IST)
  python scripts/telegram_extra.py old_article  -> re-share an older article with its cover (7 PM IST)
"""
import datetime
import json
import os
import pathlib
import re
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT = os.environ.get("TELEGRAM_CHAT", "").strip()
SITE, BLOG = "https://retirementplankaro.com", "https://blog.retirementplankaro.com"
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
FOLLOW = "\n\n📲 Instagram: instagram.com/retirementplankaro\nEducational only, not investment advice."


def send(method, **data):
    r = requests.post(f"https://api.telegram.org/bot{TOKEN}/{method}", data=data, timeout=60).json()
    if not r.get("ok"):
        raise SystemExit(f"Telegram error: {r.get('description', r)}")
    print("posted message", r["result"]["message_id"])


def calculator(today):
    calcs = json.loads((ROOT / "data" / "telegram_calculators.json").read_text(encoding="utf-8"))
    c = calcs[today.toordinal() % len(calcs)]
    slug = "calc-" + c["path"].strip("/")
    link = f"{SITE}{c['path']}?utm_source=telegram&utm_medium=social&utm_campaign={slug}"
    send("sendMessage", chat_id=CHAT, text=f"🧮 Aaj ka free tool: {c['name']}\n\n{c['text']}\n\n👉 {link}{FOLLOW}")


def posts():
    out = []
    for p in sorted((ROOT / "content" / "posts").glob("*.md")):
        m = re.match(r"---\n(.*?)\n---", p.read_text(encoding="utf-8"), re.S)
        meta = dict(l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)
        out.append({k.strip(): v.strip().strip('"') for k, v in meta.items()})
    return out


def old_article(today):
    # skip anything from the last 2 days (it was just posted), rotate through the rest
    cutoff = (today - datetime.timedelta(days=2)).isoformat()
    pool = [p for p in posts() if p.get("date", "") <= cutoff] or posts()
    p = pool[today.toordinal() % len(pool)]
    utm = f"utm_source=telegram&utm_medium=social&utm_campaign={p['slug']}"
    tool = p.get("tool_url", "")
    tool_line = f"\n🧮 {p.get('tool_name', 'Free calculator')}: {tool}{'&' if '?' in tool else '?'}{utm}" if tool else ""
    caption = (f"📖 Agar miss ho gaya ho:\n\n{p['title']}\n\n{p['description']}\n\n"
               f"👉 Pura article: {BLOG}/{p['slug']}/?{utm}{tool_line}")
    send("sendPhoto", chat_id=CHAT, photo=f"{BLOG}/{p['slug']}/cover.jpg", caption=caption[:1024])


if __name__ == "__main__":
    if not TOKEN or not CHAT:
        raise SystemExit("Telegram secret/variable not set")
    kind = sys.argv[1] if len(sys.argv) > 1 else ""
    if kind not in ("calculator", "old_article"):
        now = datetime.datetime.now(IST)
        kind = "calculator" if now.hour < 16 else "old_article"
    {"calculator": calculator, "old_article": old_article}[kind](datetime.datetime.now(IST).date())
