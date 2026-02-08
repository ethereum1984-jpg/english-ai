import os
import sqlite3
import json
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

# ——— Настройка Gemini ———
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    print("WARNING: GEMINI_API_KEY is not set!")
genai.configure(api_key=GEMINI_KEY)

# Используем модель Gemini 1.5 Flash (она быстрая и легкая)
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__, static_folder="static", template_folder="templates")

# ——— База данных (SQLite) ———
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
    cursor.execute("SELECT level, score, history FROM users WHERE user_id = ?", (user_id,))
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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_id = data.get("user_id", "user1")
    message = data.get("message", "")

    user = get_user(user_id)

    # Формируем контекст для Gemini
    prompt_parts = [
        f"You are a friendly English teacher. User level: {user['level']}.",
        "History of conversation:",
    ]
    
    # Добавляем историю (последние 6 сообщений)
    for h in user["history"][-6:]:
        role = "Student" if h["role"] == "user" else "Teacher"
        prompt_parts.append(f"{role}: {h['content']}")
    
    prompt_parts.append(f"Student: {message}")
    prompt_parts.append("Teacher: Give a short exercise, correct mistakes, and explain simply.")

    try:
        # Генерация ответа через Gemini
        response = model.generate_content("\n".join(prompt_parts))
        reply = response.text
    except Exception as e:
        print(f"Error: {e}")
        reply = "I'm having trouble with my Google brain. Check the API Key!"

    # Сохраняем историю
    user["history"].append({"role": "user", "content": message})
    user["history"].append({"role": "assistant", "content": reply})

    # Простая геймификация
    lower_reply = reply.lower()
    if any(word in lower_reply for word in ["correct", "well done", "good job", "perfect"]):
        user["score"] += 10
        if user["score"] >= 50 and user["level"] == "Beginner":
            user["level"] = "Intermediate"

    save_user(user_id, user)

    return jsonify({
        "reply": reply,
        "level": user["level"],
        "score": user["score"]
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
