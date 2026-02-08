import os
import sqlite3
import json
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

# ——— Настройка Gemini ———
# Код ищет переменную GEMINI_API_KEY в настройках Railway
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    print("CRITICAL: GEMINI_API_KEY is not set in Railway environment variables!")
else:
    genai.configure(api_key=GEMINI_KEY)

# Используем модель gemini-1.5-flash. 
# Если 404 повторится, можно попробовать сменить на 'gemini-1.0-pro'
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
        print(f"DB Read Error: {e}")
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
        return jsonify({"reply": "System Error: API Key is missing. Add GEMINI_API_KEY to Railway Variables."})

    user = get_user(user_id)

    # Собираем промпт для учителя
    prompt = (
        f"You are a friendly English teacher. Current student level: {user['level']}.\n"
        f"History: {user['history'][-4:]}\n"
        f"Student says: {message}\n"
        f"Teacher: Respond briefly, correct any grammar mistakes, and give a tiny task."
    )

    try:
        # Прямой вызов генерации
        response = model.generate_content(prompt)
        
        # В новых версиях API ответ лежит в response.text
        if response and response.text:
            reply = response.text
        else:
            reply = "I received an empty response from the AI. Please try again."
            
    except Exception as e:
        error_str = str(e)
        print(f"Gemini Error: {error_str}")
        # Если это снова 404, предложим сменить модель в логах
        if "404" in error_str:
            reply = "Error 404: The model version is not found. Try updating your requirements.txt to google-generativeai>=0.8.0"
        else:
            reply = f"AI Error: {error_str}"

    # Обновляем историю
    user["history"].append({"role": "user", "content": message})
    user["history"].append({"role": "assistant", "content": reply})

    # Начисляем очки за правильные ответы (простая проверка по ключевым словам)
    check_words = ["correct", "well done", "good job", "perfect", "right"]
    if any(word in reply.lower() for word in check_words):
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
