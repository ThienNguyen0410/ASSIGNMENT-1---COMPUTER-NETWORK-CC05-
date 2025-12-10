// Utility function
const $ = id => document.getElementById(id);

// Global state
let currentUser = null;
let currentContact = null;
let currentContactType = 'direct'; // direct or channel
let isGroupChatMode = false;
let lastMessageCount = {};
let messageRefreshInterval = null;

// ===== LOGIN FUNCTIONS =====
async function login() {
    const username = $('username').value.trim();
    const password = $('password').value.trim();

    if (!username || !password) {
        showNotification('Please enter username and password', 'error');
        return;
    }

    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();
        
        if (data.status === 'success' || data.status === 'ok') {
            currentUser = username;
            $('username-display').textContent = username;
            $('login-section').style.display = 'none';
            $('main-content').style.display = 'flex';
            showNotification('Login successful!');
            await loadChannels();
            await loadContacts();
        } else {
            showNotification(data.msg || 'Login failed', 'error');
        }
    } catch (e) {
        console.error('Login error:', e);
        showNotification('Cannot connect to server', 'error');
    }
}

function logout() {
    currentUser = null;
    currentContact = null;
    $('username-display').textContent = 'Not logged in';
    $('login-section').style.display = 'block';
    $('main-content').style.display = 'none';
    $('username').value = '';
    $('password').value = '';
    clearMessages();
    if (messageRefreshInterval) clearInterval(messageRefreshInterval);
    showNotification('Logged out successfully');
}

// ===== CHANNELS FUNCTIONS =====
async function loadChannels() {
    try {
        const res = await fetch('/api/view-channels');
        const data = await res.json();
        
        const list = $('channels-list');
        list.innerHTML = '';

        if (data.all_channels_w_member) {
            // Get user's joined channels
            Object.entries(data.all_channels_w_member).forEach(([channel, members]) => {
                if (members.includes(currentUser)) {
                    const item = createContactItem(channel, 'channel', members.length);
                    item.onclick = () => selectChannel(channel);
                    list.appendChild(item);
                }
            });
        }

        if (list.children.length === 0) {
            list.innerHTML = '<div style="padding: 12px; color: #999; text-align: center;">No channels joined</div>';
        }
    } catch (e) {
        console.error('Load channels error:', e);
    }
}

async function viewAllChannels() {
    try {
        const res = await fetch('/api/view-channels');
        const data = await res.json();

        const grid = $('all-channels-list');
        grid.innerHTML = '';

        if (data.all_channels_w_member) {
            Object.entries(data.all_channels_w_member).forEach(([channel, members]) => {
                const card = document.createElement('div');
                card.className = 'channel-card';
                card.innerHTML = `
                    <h3>📺 ${channel}</h3>
                    <p>👥 ${members.length} members</p>
                    <button class="btn-join" onclick="joinChannel('${channel}')">Join Channel</button>
                `;
                grid.appendChild(card);
            });
        }

        $('channels-modal').style.display = 'flex';
    } catch (e) {
        console.error('View all channels error:', e);
    }
}

async function joinChannel(channelName) {
    if (!currentUser) {
        showNotification('Please login first', 'error');
        return;
    }

    try {
        const res = await fetch('/api/join-channel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ channel: channelName })
        });

        const data = await res.json();
        
        if (data.status === 'success' || data.status === 'ok') {
            showNotification(`Joined ${channelName}!`);
            await loadChannels();
            closeChannelsModal();
        } else {
            showNotification(data.msg || 'Failed to join channel', 'error');
        }
    } catch (e) {
        console.error('Join channel error:', e);
        showNotification('Cannot connect to server', 'error');
    }
}

// ===== CONTACTS FUNCTIONS =====
async function loadContacts() {
    try {
        const res = await fetch('/api/contacts');
        const data = await res.json();

        const list = $('contacts-list');
        list.innerHTML = '';

        if (data.peers) {
            Object.keys(data.peers).forEach(peer => {
                if (peer !== currentUser) {
                    const item = createContactItem(peer, 'direct', null);
                    item.onclick = () => selectContact(peer);
                    list.appendChild(item);
                }
            });
        }

        if (list.children.length === 0) {
            list.innerHTML = '<div style="padding: 12px; color: #999; text-align: center;">No contacts</div>';
        }
    } catch (e) {
        console.error('Load contacts error:', e);
    }
}

function selectContact(name) {
    currentContact = name;
    currentContactType = 'direct';
    isGroupChatMode = false;
    updateChatHeader(name, 'Direct Message');
    highlightContact(name);
    loadMessages(name);
    setupMessageRefresh(name);
}

function selectChannel(name) {
    currentContact = name;
    currentContactType = 'channel';
    isGroupChatMode = false;
    updateChatHeader(name, 'Channel');
    highlightContact(name);
    loadChannelMessages(name);
    setupChannelMessageRefresh(name);
    showGroupChatButton();
}

function highlightContact(name) {
    document.querySelectorAll('.contact-item').forEach(item => {
        item.classList.remove('active');
    });
    const items = document.querySelectorAll('.contact-item');
    items.forEach(item => {
        if (item.textContent.includes(name)) {
            item.classList.add('active');
        }
    });
}

function createContactItem(name, type, count) {
    const item = document.createElement('button');
    item.className = 'contact-item';
    let content = `<div class="avatar-small">${type === 'channel' ? '📺' : '👤'}</div>`;
    content += `<div class="contact-name">${name}</div>`;
    if (count !== null) {
        content += `<span style="font-size: 11px; color: #999;">${count}</span>`;
    }
    item.innerHTML = content;
    return item;
}

function updateChatHeader(name, type) {
    $('chat-contact-name').textContent = name;
    $('chat-contact-type').textContent = type;
}

// ===== MESSAGE FUNCTIONS =====
async function loadMessages(contactName) {
    try {
        const res = await fetch('/api/messages', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ receiver: contactName })
        });

        const data = await res.json();
        const container = $('messages-container');

        if (data.messages && data.messages.length > 0) {
            const lastCount = lastMessageCount[contactName] || 0;
            const currentCount = data.messages.length;

            if (currentCount > lastCount) {
                container.innerHTML = '';
                data.messages.forEach(msg => {
                    appendMessage(msg.sender, msg.msg, msg.sender === currentUser);
                });
                container.scrollTop = container.scrollHeight;
                lastMessageCount[contactName] = currentCount;
            }
        } else {
            if (!lastMessageCount[contactName]) {
                container.innerHTML = `
                    <div class="messages-empty">
                        <div class="empty-icon">💬</div>
                        <p>Start a conversation with ${contactName}</p>
                    </div>
                `;
            }
        }
    } catch (e) {
        console.error('Load messages error:', e);
    }
}

async function loadChannelMessages(channelName) {
    try {
        const res = await fetch('/api/channel-messages', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ channel: channelName })
        });

        const data = await res.json();
        const container = $('messages-container');

        if (data.messages && data.messages.length > 0) {
            const lastCount = lastMessageCount[channelName] || 0;
            const currentCount = data.messages.length;

            if (currentCount > lastCount) {
                container.innerHTML = '';
                data.messages.forEach(msg => {
                    appendMessage(msg.sender, msg.msg, msg.sender === currentUser);
                });
                container.scrollTop = container.scrollHeight;
                lastMessageCount[channelName] = currentCount;
            }
        } else {
            if (!lastMessageCount[channelName]) {
                container.innerHTML = `
                    <div class="messages-empty">
                        <div class="empty-icon">💬</div>
                        <p>No messages in ${channelName} yet</p>
                    </div>
                `;
            }
        }
    } catch (e) {
        console.error('Load channel messages error:', e);
    }
}

function appendMessage(sender, text, isOwn) {
    const container = $('messages-container');
    
    // Remove empty state
    const empty = container.querySelector('.messages-empty');
    if (empty) empty.remove();

    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${isOwn ? 'own' : 'other'}`;
    bubble.innerHTML = `
        <div class="message-content">
            <div class="message-sender">${sender}</div>
            <div class="message-text">${escapeHtml(text)}</div>
            <small class="message-time">${getTime()}</small>
        </div>
    `;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
}

async function sendMessage() {
    const text = $('message-input').value.trim();

    if (!text) {
        showNotification('Message cannot be empty', 'error');
        return;
    }

    if (!currentContact) {
        showNotification('Please select a contact first', 'error');
        return;
    }

    try {
        let url = '/api/send-message';
        let body = { receiver: currentContact, msg: text };

        if (currentContactType === 'channel' && isGroupChatMode) {
            url = '/api/broadcast-channel';
            body = { channel: currentContact, msg: text };
        }

        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const data = await res.json();

        if (data.status === 'ok' || data.msg) {
            $('message-input').value = '';
            appendMessage(currentUser, text, true);
            
            // Update message count
            if (currentContactType === 'direct') {
                lastMessageCount[currentContact] = (lastMessageCount[currentContact] || 0) + 1;
            } else {
                lastMessageCount[currentContact] = (lastMessageCount[currentContact] || 0) + 1;
            }
        } else {
            showNotification('Failed to send message', 'error');
        }
    } catch (e) {
        console.error('Send message error:', e);
        showNotification('Cannot send message', 'error');
    }
}

function setupMessageRefresh(contactName) {
    if (messageRefreshInterval) clearInterval(messageRefreshInterval);
    messageRefreshInterval = setInterval(() => {
        if (currentContact === contactName && currentContactType === 'direct') {
            loadMessages(contactName);
        }
    }, 2000);
}

function setupChannelMessageRefresh(channelName) {
    if (messageRefreshInterval) clearInterval(messageRefreshInterval);
    messageRefreshInterval = setInterval(() => {
        if (currentContact === channelName && currentContactType === 'channel') {
            loadChannelMessages(channelName);
        }
    }, 2000);
}

function clearMessages() {
    $('messages-container').innerHTML = `
        <div class="messages-empty">
            <div class="empty-icon">💬</div>
            <p>Select a contact to start chatting</p>
        </div>
    `;
}

// ===== GROUP CHAT FUNCTIONS =====
function showGroupChatButton() {
    if (currentContactType === 'channel') {
        $('btnGroupChat').style.display = 'inline-block';
    } else {
        $('btnGroupChat').style.display = 'none';
    }
}

function toggleGroupChat() {
    if (currentContactType === 'channel') {
        isGroupChatMode = !isGroupChatMode;
        const btn = $('btnGroupChat');
        if (isGroupChatMode) {
            btn.textContent = '👥 Group (ON)';
            btn.style.backgroundColor = 'rgba(255,255,255,0.3)';
        } else {
            btn.textContent = '👥 Group';
            btn.style.backgroundColor = '';
        }
    }
}

// ===== MODAL FUNCTIONS =====
function closeChannelsModal() {
    $('channels-modal').style.display = 'none';
}

// ===== SEARCH FUNCTIONS =====
function searchContacts() {
    const query = $('search-input').value.toLowerCase();
    document.querySelectorAll('.contact-item').forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(query) ? 'flex' : 'none';
    });
}

// ===== UTILITY FUNCTIONS =====
function getTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'success') {
    const notif = $('notification');
    notif.textContent = message;
    notif.className = 'notification show ' + type;
    setTimeout(() => {
        notif.classList.remove('show');
    }, 3000);
}

// ===== EVENT LISTENERS =====
document.addEventListener('DOMContentLoaded', () => {
    // Login
    $('btnLogout').addEventListener('click', logout);
    
    // Message input
    $('message-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    // Send button
    $('btn-send').addEventListener('click', sendMessage);
    
    // Search
    $('search-input').addEventListener('input', searchContacts);
    
    // Channels
    $('btnViewChannels').addEventListener('click', viewAllChannels);
    $('btnRefresh').addEventListener('click', () => {
        loadChannels();
        loadContacts();
    });
    
    // Group chat
    $('btnGroupChat').addEventListener('click', toggleGroupChat);
    
    // Modal close
    window.addEventListener('click', (e) => {
        const modal = $('channels-modal');
        if (e.target === modal) {
            closeChannelsModal();
        }
    });
});
