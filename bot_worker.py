import requests
import time
import json
import os
from datetime import datetime, timezone, timedelta

API_KEY = os.getenv("YOUTUBE_API_KEY")  # Renderでは環境変数から取得
CONFIG_FILE = "config.json"
STATE_FILE = "notified_videos.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return []
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_notified():
    if not os.path.exists(STATE_FILE):
        return []
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_notified(video_ids):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(video_ids, f, ensure_ascii=False, indent=2)

def get_channel_id(username_or_id):
    if username_or_id.startswith("UC"):
        return username_or_id
    url = f"https://www.googleapis.com/youtube/v3/channels?part=id&forUsername={username_or_id}&key={API_KEY}"
    res = requests.get(url).json()
    if "items" in res and res["items"]:
        return res["items"][0]["id"]
    return username_or_id  # fallback

def fetch_upcoming_video(channel_id):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&eventType=upcoming&type=video&key={API_KEY}"
    res = requests.get(url).json()
    if "items" in res and res["items"]:
        return res["items"][0]
    return None

def fetch_live_video(channel_id):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&eventType=live&type=video&key={API_KEY}"
    res = requests.get(url).json()
    if "items" in res and res["items"]:
        return res["items"][0]
    return None

def send_discord_notification(webhook_url, video, status):
    title = video["snippet"]["title"]
    video_id = video["id"]["videoId"]
    url = f"https://www.youtube.com/watch?v={video_id}"
    thumbnail = video["snippet"]["thumbnails"]["high"]["url"]
    start_time = video["snippet"]["publishedAt"]

    # JST変換
    dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
    dt = dt.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=9)))
    jst_time = dt.strftime("%Y/%m/%d %H:%M")

    content = f"@here 🎬 **{status}**\n**{title}**\n📅 {jst_time}\n🔗 {url}"
    data = {
        "content": content,
        "embeds": [{
            "title": title,
            "url": url,
            "image": {"url": thumbnail},
            "footer": {"text": status}
        }]
    }
    requests.post(webhook_url, json=data)

def main_loop():
    notified = load_notified()
    while True:
        print("🔄 巡回中...")
        config = load_config()

        for entry in config:
            channel_id = get_channel_id(entry["channel_id"])
            webhook_url = entry["webhook_url"]

            # チェック：待機枠
            upcoming = fetch_upcoming_video(channel_id)
            if upcoming:
                vid = upcoming["id"]["videoId"]
                if vid not in notified:
                    print(f"🆕 待機枠: {vid}")
                    send_discord_notification(webhook_url, upcoming, "ライブ待機枠が公開されました")
                    notified.append(vid)

            # チェック：ライブ開始
            live = fetch_live_video(channel_id)
            if live:
                vid = live["id"]["videoId"]
                if vid not in notified:
                    print(f"🎥 ライブ配信中: {vid}")
                    send_discord_notification(webhook_url, live, "ライブ配信が開始されました")
                    notified.append(vid)

        save_notified(notified)
        time.sleep(300)  # 5分ごとにチェック

if __name__ == "__main__":
    main_loop()
