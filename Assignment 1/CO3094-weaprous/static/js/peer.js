function $(id) { return document.getElementById(id); }

async function login() {
    let username = $("username").value;
    let password = $("password").value;

    let res = await fetch("/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({username, password})
    });
    let data = await res.json();

    if (data.status === "success") {
        alert("Login success!");
    } else {
        alert("Login failed!");
    }
}

async function viewChannels() {
    let res = await fetch("/view-channels");
    let data = await res.json();
    $("channels").innerText = JSON.stringify(data, null, 2);
}

async function joinChannel() {
    let channel = prompt("Enter channel name:");
    let res = await fetch("/join-channel", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({channel})
    });
    alert(JSON.stringify(await res.json()));
}

async function sendMsg() {
    let msg = $("msg").value;

    let res = await fetch("/send", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({msg})
    });
}

function appendMsg(sender, msg) {
    let box = $("chat-box");
    box.innerHTML += `<div><b>${sender}:</b> ${msg}</div>`;
}

async function pollMessages() {
    let res = await fetch("/poll");
    let msgs = await res.json();

    for (let m of msgs) {
        appendMsg(m.username, m.msg);
    }

    await fetch("/clear-poll", {method: "POST"});
}

setInterval(pollMessages, 1000);
