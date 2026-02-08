import os
import sqlite3
import json
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

# ——— Настройка Gemini ———
# Код берет ключ из переменной GEMINI_API_KEY в Railway
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    print("CRITICAL ERROR: GEMINI_API_KEY is not set in environment variables!")
else:
    genai.configure(api_key=GEMINI_KEY)

# Используем модель Gemini 1.5 Flash
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
    try:
        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        cursor.execute("SELECT level, score, history FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"level": row[0], "score": row[1], "history": json.loads(row[2])}
    except Exception as e:
        print(f"DB Error: {e}")
    return {"level": "Beginner", "score": 0, "history": []}

def save_user(user_id, user):
    try:
        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)",
            (user_id, user["level"], user["score"], json.dumps(user["history"]))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Save Error: {e}")

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
        return jsonify({"reply": "Error: GEMINI_API_KEY is missing in Railway settings.", "level": "---", "score": 0})

    user = get_user(user_id)

    # Формируем промпт
    prompt_parts = [
        f"You are a friendly English teacher. User level: {user['level']}.",
        "Rules: Be concise, correct mistakes, and give a small task.",
        "Conversation History:"
    ]
    
    for h in user["history"][-6:]:
        role = "Student" if h["role"] == "user" else "Teacher"
        prompt_parts.append(f"{role}: {h['content']}")
    
    prompt_parts.append(f"Student: {message}")
    prompt_parts.append("Teacher:")

    try:
        # Пытаемся получить ответ
        response = model.generate_content("\n".join(prompt_parts))
        reply = response.text
    except Exception as e:
        # Если ошибка — выводим её текст, чтобы понять причину
        error_msg = str(e)
        print(f"Gemini Error: {error_msg}")
        return jsonify({
            "reply": f"Gemini Error: {error_msg}. (Check if your API key supports your server's region)",
            "level": user["level"],
            "score": user["score"]
        })

    # Обновляем историю и прогресс
    user["history"].append({"role": "user", "content": message})
    user["history"].append({"role": "assistant", "content": reply})

    # Простая логика баллов
    if any(word in reply.lower() for word in ["correct", "good", "well done"]):
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
    # Railway передает порт через переменную окружения
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
