const chat = document.getElementById("chat");

function addMessage(role, text) {
    chat.innerHTML += `<p><b>${role}:</b> ${text}</p>`;
    chat.scrollTop = chat.scrollHeight;
}

async function send(text = null) {
    const input = document.getElementById("msg");
    const msg = text || input.value;
    if (!msg) return;
    input.value = "";

    addMessage("You", msg);

    const res = await fetch("/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ message: msg, user_id: "user1" })
    });

    const data = await res.json();
    addMessage("AI", data.reply);

    document.getElementById("level").innerText = data.level;
    document.getElementById("score").innerText = data.score;

    speak(data.reply);
}

function speak(text) {
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = "en-US";
    window.speechSynthesis.speak(utter);
}

function startVoice() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return alert("Ваш браузер не поддерживает распознавание речи.");
    
    const recog = new SpeechRecognition();
    recog.lang = "en-US";
    recog.start();

    recog.onresult = (e) => {
        const text = e.results[0][0].transcript;
        send(text);
    };
}
