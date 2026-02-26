/* ─────────────────────────────────────────────────────────────────────────
   app.js  –  PQC-Chatt vanilla JS frontend
   Connects to FastAPI backend at http://localhost:8000
───────────────────────────────────────────────────────────────────────── */
const API = "http://localhost:8000";
const WS_BASE = "ws://localhost:8000";

/* ── State ─────────────────────────────────────────────────────────────── */
let token = localStorage.getItem("token") || null;
let currentUser = JSON.parse(localStorage.getItem("currentUser") || "null");
let receiver = null;
let socket = null;
let allUsers = [];

/* ── DOM refs ──────────────────────────────────────────────────────────── */
const $ = (id) => document.getElementById(id);

/* ── Screens ───────────────────────────────────────────────────────────── */
function showScreen(name) {
    document.querySelectorAll(".screen").forEach((s) => s.classList.remove("active"));
    $(`screen-${name}`).classList.add("active");
}

/* ══════════════════════════════════════════════════════════════════════════
   AUTH
══════════════════════════════════════════════════════════════════════════ */
function initAuth() {
    const tabs = document.querySelectorAll(".tab-btn");
    const loginForm = $("login-form");
    const regForm = $("reg-form");
    const authErr = $("auth-error");

    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            tabs.forEach((t) => t.classList.remove("active"));
            tab.classList.add("active");
            authErr.classList.remove("show");
            if (tab.dataset.tab === "login") {
                loginForm.style.display = "flex";
                regForm.style.display = "none";
            } else {
                loginForm.style.display = "none";
                regForm.style.display = "flex";
            }
        });
    });

    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        await doAuth("login", {
            username: $("login-username").value.trim(),
            password: $("login-password").value,
        });
    });

    regForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        await doAuth("register", {
            username: $("reg-username").value.trim(),
            password: $("reg-password").value,
        });
    });
}

async function doAuth(mode, body) {
    const btn = $(`${mode}-btn`);
    const errEl = $("auth-error");
    btn.disabled = true;
    btn.textContent = "Please wait…";
    errEl.classList.remove("show");

    try {
        const res = await fetch(`${API}/${mode}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || `${mode} failed`);

        token = data.access_token;
        // Decode JWT to get user id (sub)
        const payload = JSON.parse(atob(token.split(".")[1]));
        currentUser = { id: payload.sub, username: body.username };
        localStorage.setItem("token", token);
        localStorage.setItem("currentUser", JSON.stringify(currentUser));

        initApp();
        showScreen("app");
    } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.add("show");
    } finally {
        btn.disabled = false;
        btn.textContent = mode === "login" ? "Login" : "Create Account";
    }
}

/* ══════════════════════════════════════════════════════════════════════════
   APP — INIT
══════════════════════════════════════════════════════════════════════════ */
function initApp() {
    $("sidebar-username").textContent = currentUser.username;
    $("sidebar-initial").textContent = currentUser.username[0].toUpperCase();

    $("logout-btn").addEventListener("click", logout);

    $("user-search").addEventListener("input", (e) => {
        renderUserList(e.target.value.toLowerCase());
    });

    $("chat-form").addEventListener("submit", sendMessage);

    loadUsers();
    connectWS();
}

function logout() {
    disconnectWS();
    localStorage.removeItem("token");
    localStorage.removeItem("currentUser");
    token = null;
    currentUser = null;
    receiver = null;
    allUsers = [];
    $("user-list").innerHTML = "";
    showChatEmpty();
    showScreen("auth");
}

/* ══════════════════════════════════════════════════════════════════════════
   USERS
══════════════════════════════════════════════════════════════════════════ */
async function loadUsers() {
    try {
        const res = await fetch(`${API}/users`, { headers: authHeader() });
        const data = await res.json();
        allUsers = data.filter((u) => u.id !== currentUser.id);
        renderUserList("");
    } catch (err) {
        console.error("[Users]", err);
    }
}

function renderUserList(query = "") {
    const list = $("user-list");
    const filtered = allUsers.filter((u) =>
        u.username.toLowerCase().includes(query)
    );

    list.innerHTML = filtered.length === 0
        ? '<li class="user-list-empty">No users found</li>'
        : "";

    filtered.forEach((u) => {
        const li = document.createElement("li");
        li.className = `user-item${receiver?.id === u.id ? " active" : ""}`;
        li.innerHTML = `
      <div class="avatar">${u.username[0].toUpperCase()}</div>
      <span class="user-name">${escHtml(u.username)}</span>`;
        li.addEventListener("click", () => selectUser(u));
        list.appendChild(li);
    });
}

function selectUser(u) {
    receiver = u;
    renderUserList($("user-search").value.toLowerCase());
    showChatHeader(u);
    loadMessages(u.id);
}

/* ══════════════════════════════════════════════════════════════════════════
   CHAT HEADER
══════════════════════════════════════════════════════════════════════════ */
function showChatEmpty() {
    $("chat-empty").style.display = "flex";
    $("chat-header").style.display = "none";
    $("chat-messages").style.display = "none";
    $("chat-form").style.display = "none";
}

function showChatHeader(u) {
    $("chat-empty").style.display = "none";
    $("chat-header").style.display = "flex";
    $("chat-messages").style.display = "flex";
    $("chat-form").style.display = "flex";
    $("chat-header-initial").textContent = u.username[0].toUpperCase();
    $("chat-header-name").textContent = u.username;
}

/* ══════════════════════════════════════════════════════════════════════════
   MESSAGES
══════════════════════════════════════════════════════════════════════════ */
async function loadMessages(receiverId) {
    const box = $("chat-messages");
    box.innerHTML = '<p class="chat-loading">Loading…</p>';

    try {
        const res = await fetch(`${API}/messages/${receiverId}`, { headers: authHeader() });
        const data = await res.json();
        box.innerHTML = "";
        data.forEach((m) => appendMessage(m));
        scrollToBottom();
    } catch (err) {
        box.innerHTML = `<p class="chat-loading">Failed to load messages.</p>`;
        console.error("[Messages]", err);
    }
}

function appendMessage(m) {
    const box = $("chat-messages");
    const isMine = m.senderId === currentUser.id;
    const time = new Date(m.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    const row = document.createElement("div");
    row.className = `msg-row ${isMine ? "mine" : "theirs"}`;
    row.innerHTML = `
    <div class="msg-bubble">
      <p class="msg-text">${escHtml(m.payload)}</p>
      <span class="msg-time">${time}</span>
    </div>`;
    box.appendChild(row);
}

function scrollToBottom() {
    const box = $("chat-messages");
    box.scrollTop = box.scrollHeight;
}

/* ══════════════════════════════════════════════════════════════════════════
   SEND MESSAGE
══════════════════════════════════════════════════════════════════════════ */
function sendMessage(e) {
    e.preventDefault();
    if (!receiver) return;

    const input = $("chat-input");
    const payload = input.value.trim();
    if (!payload) return;

    const sent = wsSend(receiver.id, payload);
    if (!sent) {
        // WS not open – fall back to HTTP
        sendHTTP(receiver.id, payload);
    }
    input.value = "";
    input.focus();
}

async function sendHTTP(receiverId, payload) {
    try {
        const res = await fetch(`${API}/messages`, {
            method: "POST",
            headers: { ...authHeader(), "Content-Type": "application/json" },
            body: JSON.stringify({ receiverId, payload }),
        });
        const m = await res.json();
        appendMessage(m);
        scrollToBottom();
    } catch (err) {
        console.error("[HTTP send]", err);
    }
}

/* ══════════════════════════════════════════════════════════════════════════
   WEBSOCKET
══════════════════════════════════════════════════════════════════════════ */
function connectWS() {
    if (!currentUser || !token) return;
    const url = `${WS_BASE}/ws/${currentUser.id}?token=${token}`;
    socket = new WebSocket(url);

    socket.onopen = () => {
        setWsStatus("connected");
        console.log("[WS] Connected");
    };

    socket.onmessage = (event) => {
        try {
            const m = JSON.parse(event.data);
            // Only show if this message belongs to the active conversation
            if (
                receiver &&
                (
                    (m.senderId === currentUser.id && m.receiverId === receiver.id) ||
                    (m.senderId === receiver.id && m.receiverId === currentUser.id)
                )
            ) {
                appendMessage(m);
                scrollToBottom();
            }
        } catch { /* ignore non-JSON */ }
    };

    socket.onerror = () => setWsStatus("error");
    socket.onclose = () => {
        setWsStatus("disconnected");
        socket = null;
    };
}

function disconnectWS() {
    socket?.close();
    socket = null;
}

function wsSend(receiverId, payload) {
    if (!socket || socket.readyState !== WebSocket.OPEN) return false;
    socket.send(JSON.stringify({ receiverId, payload }));
    return true;
}

function setWsStatus(status) {
    const dot = $("ws-dot");
    const badge = $("ws-badge");
    dot.className = `ws-dot ${status}`;
    badge.className = `ws-badge ${status}`;
    badge.textContent = status;
}

/* ══════════════════════════════════════════════════════════════════════════
   HELPERS
══════════════════════════════════════════════════════════════════════════ */
function authHeader() {
    return { Authorization: `Bearer ${token}` };
}

function escHtml(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/* ══════════════════════════════════════════════════════════════════════════
   BOOT
══════════════════════════════════════════════════════════════════════════ */
document.addEventListener("DOMContentLoaded", () => {
    initAuth();

    if (token && currentUser) {
        initApp();
        showScreen("app");
    } else {
        showScreen("auth");
    }
});
