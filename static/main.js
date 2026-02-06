async function send() {
  const input = document.getElementById("msg");
  const msg = input.value;
  if (!msg) return;

  input.value = "";

  document.getElementById("chat").innerHTML +=
    `<p><b>You:</b> ${msg}</p>`;

  const res = await fetch("/chat", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      message: msg,
      user_id: "user1"
    })
  });

  const data = await res.json();

  document.getElementById("chat").innerHTML +=
    `<p><b>AI:</b> ${data.reply}</p>`;

  document.getElementById("level").innerText = data.level;
  document.getElementById("score").innerText = data.score;
}
