import os
import sqlite3
import json
from flask import Flask, request, jsonify, render_template
import openai

# ===== OPENAI KEY (ТОЛЬКО ИЗ ENV) =====
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise RuntimeError("OPENAI_API_KEY is not set in environment variables")

# ===== FLASK APP =====
app = Flask(__name__)

# ===== DATABASE =====
DB_FILE = "db.sqlite"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
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
    c = conn.cursor()
    c.execute("SELECT level, score, history FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
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

def save_user(user_id, user):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)",
        (user_id, user["level"], user["score"], json.dumps(user["history"]))
    )
    conn.commit()
    conn.close()

init_db()

# ===== ROUTES =====

@app.route("/")
def home():
    return "English AI Assistant is running ✅"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_id = data.get("user_id", "user1")
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Empty message"}), 400

    user = get_user(user_id)

    system_prompt = f"""
You are a friendly English teacher.
User level: {user['level']}.

Rules:
- Give ONE task at a time
- Types: translation, fill the blank, simple question
- Wait for answer
- Correct and explain simply
- Encourage the user
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages += user["history"][-6:]
    messages.append({"role": "user", "content": message})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    reply = response.choices[0].message.content

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

# ===== LOCAL RUN (Railway игнорирует) =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
