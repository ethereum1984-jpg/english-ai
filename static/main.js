const chat = document.getElementById("chat");

function add(role, text) {
  chat.innerHTML += `<p><b>${role}:</b> ${text}</p>`;
  chat.scrollTop = chat.scrollHeight;
}

async function send(text = null) {
  const input = document.getElementById("msg");
  const msg = text || input.value;
  if (!msg) return;
  input.value = "";

  add("You", msg);

  const res = await fetch("/chat", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      message: msg,
      user_id: "user1"
    })
  });

  const data = await res.json();
  add("AI", data.reply);

  document.getElementById("level").innerText = data.level;
  document.getElementById("score").innerText = data.score;

  speak(data.reply);
}

function speak(text) {
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = "en-US";
  speechSynthesis.speak(utter);
}

// 🎤 Speech to Text
function startVoice() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recog = new SpeechRecognition();
  recog.lang = "en-US";
  recog.start();

  recog.onresult = e => {
    const text = e.results[0][0].transcript;
    send(text);
  };
}
