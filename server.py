import sqlite3
import json
import os
from flask import Flask, request, jsonify, render_template
from openai import OpenAI

# --- OpenAI client ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

# --- Инициализация БД ---
def init_db():
    conn = sqlite3.connect("db.sqlite")
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

def get_user_data(user_id):
    conn = sqlite3.connect("db.sqlite")
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

    return {
        "level": "Beginner",
        "score": 0,
        "history": []
    }

def save_user_data(user_id, data):
    conn = sqlite3.connect("db.sqlite")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)",
        (
            user_id,
            data["level"],
            data["score"],
            json.dumps(data["history"])
        )
    )
    conn.commit()
    conn.close()

init_db()

# --- Routes ---
@app.route("/")
def index():
    return "English AI is running 🚀"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_id = data.get("user_id", "user1")
    user_msg = data.get("message", "")

    user = get_user_data(user_id)

    system_prompt = (
        f"You are a friendly English teacher. "
        f"User level: {user['level']}. "
        f"Give exercises, check answers, be encouraging."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages += user["history"][-6:]
    messages.append({"role": "user", "content": user_msg})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    reply = response.choices[0].message.content

    user["history"].append({"role": "user", "content": user_msg})
    user["history"].append({"role": "assistant", "content": reply})

    if "correct" in reply.lower():
        user["score"] += 10
        if user["score"] >= 50:
            user["level"] = "Intermediate"

    save_user_data(user_id, user)

    return jsonify({
        "reply": reply,
        "level": user["level"],
        "score": user["score"]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
