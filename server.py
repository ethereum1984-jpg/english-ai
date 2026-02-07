import sqlite3
from flask import Flask, request, jsonify, render_template
import openai, os

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# --- РАБОТА С БАЗОЙ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            level TEXT,
            score INTEGER,
            history TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT level, score, history FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        import json
        return {"level": row[0], "score": row[1], "history": json.loads(row[2])}
    return {"level": "Beginner", "score": 0, "history": []}

def save_user(user_id, user_data):
    import json
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, level, score, history)
        VALUES (?, ?, ?, ?)
    ''', (user_id, user_data['level'], user_data['score'], json.dumps(user_data['history'])))
    conn.commit()
    conn.close()

init_db()
# ------------------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_id = request.json.get("user_id", "user1")
    user_msg = request.json.get("message", "")

    user = get_user(user_id)

    system_prompt = f"""
    You are a friendly English teacher. User level: {user['level']}.
    Rules: Give tasks (Translation, Fill in the blank, Multiple choice), check answers, explain simply.
    """

    messages = [{"role": "system", "content": system_prompt}]
    messages += user["history"][-6:]
    messages.append({"role": "user", "content": user_msg})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    reply = response.choices[0].message.content
    user["history"].append({"role": "user", "content": user_msg})
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
