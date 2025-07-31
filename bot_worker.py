import time
import json
import os
import requests

API_KEY = os.getenv("YOUTUBE_API_KEY")
CONFIG_FILE = "config.json"
STATE_FILE = "notified_videos.json"
CHECK_INTERVAL = 300  # 5分

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return []
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def load_notified():
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, "r") as f:
        return set(json.load(f))

def save_notified(notified_ids):
    with open(STATE_FILE, "w") as f:
        json.dump(list(notified_ids), f)

def get_channel_id(channel):
    if channel.startswith("@"):
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={channel}&key={API_KEY}"
        r = requests.get(url)
        data = r.json()
        items = data.get("items")
        if items:
            return items[0]["snippet"]["channelId"]
        return None
    return channel

def fetch_videos(channel_id):
    url = (
        f"https://www.googleapis.com/youtube/v3/search?"
        f"part=snippet&channelId={channel_id}&eventType=upcoming&type=video&key={API_KEY}"
    )
    r = requests.get(url)
    return r.json().get("items", [])

def send_notification(webhook_url, video_id, title, thumbnail_url, is_live):
    status = "ライブ配信が開始されました" if is_live else "ライブ待機枠が公開されました"
    content = f"@here 🎬 **{status}**\nhttps://www.youtube.com/watch?v={video_id}"
    data = {
        "content": content,
        "embeds": [{
            "title": title,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "image": {"url": thumbnail_url}
        }]
    }
    requests.post(webhook_url, json=data)

def main():
    print("[INFO] Bot started.")
    notified_ids = load_notified()
    while True:
        print("[INFO] Checking channels...")
        config = load_config()
        for entry in config:
            channel = entry.get("channel_id")
            webhook = entry.get("webhook_url")
            if not channel or not webhook:
                continue
            real_channel_id = get_channel_id(channel)
            if not real_channel_id:
                continue
            videos = fetch_videos(real_channel_id)
            for video in videos:
                video_id = video["id"]["videoId"]
                if video_id in notified_ids:
                    continue
                title = video["snippet"]["title"]
                thumbnail = video["snippet"]["thumbnails"]["high"]["url"]
                send_notification(webhook, video_id, title, thumbnail, is_live=False)
                print(f"[INFO] Notified: {title}")
                notified_ids.add(video_id)
        save_notified(notified_ids)
        print("[INFO] Waiting for next check...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
