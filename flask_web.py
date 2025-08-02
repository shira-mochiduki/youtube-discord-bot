from flask import Flask, request, render_template, redirect
import json
import os

app = Flask(__name__)

CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return []
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/", methods=["GET"])
def index():
    config = load_config()
    return render_template("index.html", config=config)

@app.route("/add", methods=["POST"])
def add_entry():
    data = load_config()
    channel_id = request.form.get("channel_id", "").strip()
    webhook_url = request.form.get("webhook_url", "").strip()
    if channel_id and webhook_url:
        data.append({
            "channel_id": channel_id,
            "webhook_url": webhook_url
        })
        save_config(data)
    return redirect("/")

@app.route("/delete/<int:index>", methods=["POST"])
def delete_entry(index):
    data = load_config()
    if 0 <= index < len(data):
        data.pop(index)
        save_config(data)
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
