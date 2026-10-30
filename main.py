import os
import requests
from bs4 import BeautifulSoup

CHANNEL = os.environ["TG_CHANNEL"]
BALE_TOKEN = os.environ["BALE_TOKEN"]
BALE_CHAT = os.environ["BALE_CHAT_ID"]
STATE = "last_id.txt"

MEDIA_SELECTORS = (
    ".tgme_widget_message_photo_wrap, "
    ".tgme_widget_message_video_player, "
    ".tgme_widget_message_document_wrap, "
    ".tgme_widget_message_voice, "
    ".tgme_widget_message_sticker_wrap, "
    ".tgme_widget_message_roundvideo_wrap, "
    ".tgme_widget_message_poll"
)


def get_last_id():
    try:
        return int(open(STATE).read().strip())
    except Exception:
        return None


def fetch_posts():
    r = requests.get(
        f"https://t.me/s/{CHANNEL}",
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    posts = []
    for m in soup.select(".tgme_widget_message"):
        post_id = int(m["data-post"].split("/")[-1])
        text_el = m.select_one(".tgme_widget_message_text")
        has_media = m.select_one(MEDIA_SELECTORS)
        is_text_only = bool(text_el) and not has_media
        posts.append((post_id, is_text_only, text_el.get_text("\n").strip() if text_el else ""))
    return sorted(posts)


def send_bale(text):
    r = requests.post(
        f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage",
        json={"chat_id": BALE_CHAT, "text": text[:4000]},
        timeout=30,
    )
    r.raise_for_status()


def main():
    posts = fetch_posts()
    if not posts:
        print("No posts found")
        return

    last = get_last_id()

    # First run: don't spam old posts, just remember the latest one
    if last is None:
        open(STATE, "w").write(str(posts[-1][0]))
        print("First run, state initialized")
        return

    for post_id, is_text_only, text in posts:
        if post_id <= last:
            continue
        if text:
            send_bale(text)
            print(f"Sent {post_id}")
        last = post_id

    open(STATE, "w").write(str(last))


if __name__ == "__main__":
    main()
