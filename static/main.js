const chat = document.getElementById("chat");
const msgInput = document.getElementById("msg");

// ====== ОТПРАВКА СООБЩЕНИЯ ======
function send() {
  const text = msgInput.value.trim();
  if (!text) return;

  chat.innerHTML += `<div><b>You:</b> ${text}</div>`;
  chat.scrollTop = chat.scrollHeight;

  fetch("/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      user_id: "user1",
      message: text
    })
  })
  .then(res => res.json())
  .then(data => {
    chat.innerHTML += `<div><b>AI:</b> ${data.reply}</div>`;
    chat.scrollTop = chat.scrollHeight;

    document.getElementById("level").innerText = data.level;
    document.getElementById("score").innerText = data.score;

    speak(data.reply); // 🔊 голос ИИ
  })
  .catch(() => {
    chat.innerHTML += `<div><b>AI:</b> Error connecting to server</div>`;
  });

  msgInput.value = "";
}

// ====== МИКРОФОН (Speech → Text) ======
function startVoice() {
  if (!('webkitSpeechRecognition' in window)) {
    alert("Speech recognition not supported");
    return;
  }

  const recognition = new webkitSpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;

  recognition.onresult = function(event) {
    const text = event.results[0][0].transcript;
    msgInput.value = text;
    send();
  };

  recognition.onerror = function() {
    alert("Voice recognition error");
  };

  recognition.start();
}

// ====== ГОЛОС ИИ (Text → Speech) ======
function speak(text) {
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  utterance.rate = 1;
  utterance.pitch = 1;
  window.speechSynthesis.speak(utterance);
}
