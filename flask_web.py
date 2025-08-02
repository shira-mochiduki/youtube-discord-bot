import os
import json
import requests
from flask import Flask, request, redirect, render_template

app = Flask(__name__)
CONFIG_FILE = "config.json"
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return []
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] config.jsonの読み込みエラー: {e}")
            return []

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def resolve_channel_id(input_id):
    """@handleが来たらAPI経由でchannel_idに変換"""
    if input_id.startswith("@"):
        url = f"https://www.googleapis.com/youtube/v3/channels?part=id&forHandle={input_id}&key={YOUTUBE_API_KEY}"
        response = requests.get(url)
        data = response.json()
        if "items" in data and data["items"]:
            return data["items"][0]["id"]
        else:
            print(f"[ERROR] Handleの解決に失敗: {data}")
            return None
    return input_id  # UC〜形式ならそのまま返す

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", entries=load_config())

@app.route("/add", methods=["POST"])
def add_entry():
    data = load_config()
    input_id = request.form.get("channel_id", "").strip()
    webhook_url = request.form.get("webhook_url", "").strip()

    if not input_id or not webhook_url:
        return "全ての項目を入力してください", 400

    channel_id = resolve_channel_id(input_id)
    if not channel_id:
        return "チャンネルIDの取得に失敗しました（Handleが存在しない可能性）", 400

    data.append({
        "channel_id": channel_id,
        "webhook_url": webhook_url
    })
    save_config(data)
    return redirect("/")
