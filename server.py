import os
import sqlite3
import json
from flask import Flask, request, jsonify, render_template
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__, static_folder="static", template_folder="templates")

DB_FILE = "db.sqlite"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            level TEXT,
            score INTEGER,
            history TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT level, score, history FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "level": row[0],
            "score": row[1],
            "history": json.loads(row[2])
        }

    return {"level": "Beginner", "score": 0, "history": []}

def save_user(user_id, user_data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)",
        (user_id, user_data["level"], user_data["score"], json.dumps(user_data["history"]))
    )
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    # Отдаёт HTML интерфейс
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_id = data.get("user_id", "user1")
    message = data.get("message", "")

    user = get_user(user_id)

    system_prompt = f"""
You are a friendly English teacher.
User level: {user['level']}.
Give tasks, check answers, be encouraging.
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages += user["history"][-6:]
    messages.append({"role": "user", "content": message})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = "Sorry, I can't answer right now."

    user["history"].append({"role": "user", "content": message})
    user["history"].append({"role": "assistant", "content": reply})

    if "correct" in reply.lower():
        user["score"] += 10
        if user["score"] >= 50:
            user["level"] = "Intermediate"

    save_user(user_id, user)

    return jsonify({"reply": reply, "level": user["level"], "score": user["score"]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
