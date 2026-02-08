import os
import sqlite3
import json
from flask import Flask, request, jsonify, render_template
import openai

# ——— OpenAI ключ из окружения (надо указать в Railway) ———
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise RuntimeError("OPENAI_API_KEY is not set")

# ——— Flask ———
app = Flask(__name__, static_folder="static", template_folder="templates")

# ——— SQLite ———
DB = "db.sqlite"

def init_db():
    conn = sqlite3.connect(DB)
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
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT level, score, history FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"level": row[0], "score": row[1], "history": json.loads(row[2])}
    return {"level": "Beginner", "score": 0, "history": []}

def save_user(user_id, user):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)",
        (user_id, user["level"], user["score"], json.dumps(user["history"]))
    )
    conn.commit()
    conn.close()

init_db()

# ——— Main UI ———
@app.route("/")
def index():
    return render_template("index.html")

# ——— Chat API ———
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_id = data.get("user_id", "user1")
    message = data.get("message", "")

    user = get_user(user_id)

    system_prompt = f"""
You are a friendly English teacher.
User level: {user['level']}.

Give a short English language exercise,
wait for the answer, correct it, explain simply,
and encourage the user.
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

    return jsonify({
        "reply": reply,
        "level": user["level"],
        "score": user["score"]
    })

# ——— Start server ———
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
