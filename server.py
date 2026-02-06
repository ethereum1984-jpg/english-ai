from flask import Flask, request, jsonify, render_template
import openai, os

openai.api_key = os.getenv("OPENAI_API_KEY")
app = Flask(__name__)
users_progress = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message","")
    return jsonify({"reply":"Hello! This is AI English Assistant.","level":"Beginner","score":0})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
