import os
import json
import requests
from bs4 import BeautifulSoup

CHANNELS = [c.strip() for c in os.environ["TG_CHANNEL"].split(",") if c.strip()]
BALE_TOKEN = os.environ["BALE_TOKEN"]
BALE_CHAT = os.environ["BALE_CHAT_ID"]
STATE = "state.json"


def load_state():
    try:
        return json.load(open(STATE))
    except Exception:
        return {}


def save_state(state):
    json.dump(state, open(STATE, "w"))


def fetch_posts(channel):
    r = requests.get(
        f"https://t.me/s/{channel}",
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    posts = []
    for m in soup.select(".tgme_widget_message"):
        post_id = int(m["data-post"].split("/")[-1])
        text_el = m.select_one(".tgme_widget_message_text")
        text = text_el.get_text("\n").strip() if text_el else ""
        posts.append((post_id, text))
    return sorted(posts)


def send_bale(text):
    r = requests.post(
        f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage",
        json={"chat_id": BALE_CHAT, "text": text[:4000]},
        timeout=30,
    )
    r.raise_for_status()


def process(channel, state, backfill):
    posts = fetch_posts(channel)
    if not posts:
        print(f"[{channel}] no posts found")
        return

    if backfill > 0:
        for post_id, text in posts[-backfill:]:
            if text:
                send_bale(f"📢 {channel}\n\n{text}")
                print(f"[{channel}] backfill sent {post_id}")
        state[channel] = posts[-1][0]
        return

    last = state.get(channel)
    if last is None:
        state[channel] = posts[-1][0]
        print(f"[{channel}] first run, state initialized")
        return

    for post_id, text in posts:
        if post_id <= last:
            continue
        if text:
            send_bale(f"📢 {channel}\n\n{text}")
            print(f"[{channel}] sent {post_id}")
        last = post_id
        state[channel] = last


def main():
    backfill = int(os.environ.get("BACKFILL", "0") or "0")
    state = load_state()
    for channel in CHANNELS:
        try:
            process(channel, state, backfill)
        except Exception as e:
            print(f"[{channel}] error: {e}")
        save_state(state)


if __name__ == "__main__":
    main()
