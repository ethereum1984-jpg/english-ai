import os
import sqlite3
import json
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

# ——— Настройка Gemini ———
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    print("CRITICAL: GEMINI_API_KEY IS MISSING")
else:
    genai.configure(api_key=GEMINI_KEY)

# МЕНЯЕМ МОДЕЛЬ НА ПРОФЕССИОНАЛЬНУЮ СТАБИЛЬНУЮ ВЕРСИЮ
model = genai.GenerativeModel('gemini-1.0-pro')

app = Flask(__name__, static_folder="static", template_folder="templates")

# ——— База данных ———
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
    try:
        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        cursor.execute("SELECT level, score, history FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"level": row[0], "score": row[1], "history": json.loads(row[2])}
    except: pass
    return {"level": "Beginner", "score": 0, "history": []}

def save_user(user_id, user):
    try:
        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)",
                       (user_id, user["level"], user["score"], json.dumps(user["history"])))
        conn.commit()
        conn.close()
    except: pass

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_id = data.get("user_id", "user1")
    message = data.get("message", "")

    if not GEMINI_KEY:
        return jsonify({"reply": "API Key error. Check Railway Variables."})

    user = get_user(user_id)

    # Упрощенный промпт для стабильности
    prompt = (
        f"You are a helpful English teacher. Student level: {user['level']}.\n"
        f"Correct mistakes and respond briefly to: {message}"
    )

    try:
        # Используем старый проверенный метод генерации
        response = model.generate_content(prompt)
        reply = response.text
    except Exception as e:
        print(f"Error detail: {e}")
        # Если даже Pro выдает 404, значит проблема в регионе сервера Railway
        reply = f"Error: {str(e)}. Try to change Railway server region to US East."

    user["history"].append({"role": "user", "content": message})
    user["history"].append({"role": "assistant", "content": reply})

    if "correct" in reply.lower() or "good" in reply.lower():
        user["score"] += 10
        if user["score"] >= 50: user["level"] = "Intermediate"

    save_user(user_id, user)

    return jsonify({"reply": reply, "level": user["level"], "score": user["score"]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
