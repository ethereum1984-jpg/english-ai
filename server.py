from flask import Flask, request, jsonify, render_template
import openai, os

# OpenAI ключ из переменных окружения
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
users = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_id = request.json.get("user_id", "user1")
    user_msg = request.json.get("message", "")

    if user_id not in users:
        users[user_id] = {
            "level": "Beginner",
            "score": 0,
            "history": []
        }

    user = users[user_id]

    system_prompt = f"""
You are a friendly English teacher.
User level: {user['level']}.

Rules:
- If user greets or says start → give a task.
- Use one task at a time:
  1) Translation
  2) Fill in the blank
  3) Multiple choice
- Wait for user's answer.
- Check it.
- Explain simply.
- Encourage.
- Then give next task.
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

    return jsonify({
        "reply": reply,
        "level": user["level"],
        "score": user["score"]
    })

# 🔹 Railway Production-ready
if __name__ == "__main__":
    # Берём порт от Railway
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
