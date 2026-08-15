// ═══════════════════════════════════════════════
//  JARVIS AI — script.js v3.0
//  Always-on wake word + SSE real-time state
// ═══════════════════════════════════════════════

// ─────────────────────────────────────────
//  THREE.JS — 3D Wireframe Sphere + Rings
// ─────────────────────────────────────────
let scene, camera, renderer, coreGroup;
let rings = [];
let coreMesh, outerMesh, innerMesh;
let vizIntensity = 0;   // 0=idle, 1=listening, 2=processing
let currentState = 'WAITING';

function initThree() {
    const container = document.getElementById('canvas-container');
    const W = container.clientWidth, H = container.clientHeight;

    scene    = new THREE.Scene();
    camera   = new THREE.PerspectiveCamera(60, W / H, 0.1, 1000);
    camera.position.z = 6;

    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(W, H);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    coreGroup = new THREE.Group();
    scene.add(coreGroup);

    // Outer geodesic wireframe
    outerMesh = new THREE.Mesh(
        new THREE.IcosahedronGeometry(2.0, 3),
        new THREE.MeshBasicMaterial({ color: 0x00c8ff, wireframe: true, transparent: true, opacity: 0.35 })
    );
    coreGroup.add(outerMesh);

    // Inner wireframe
    innerMesh = new THREE.Mesh(
        new THREE.IcosahedronGeometry(1.3, 2),
        new THREE.MeshBasicMaterial({ color: 0x00eeff, wireframe: true, transparent: true, opacity: 0.5 })
    );
    coreGroup.add(innerMesh);

    // Glowing core
    coreMesh = new THREE.Mesh(
        new THREE.SphereGeometry(0.45, 32, 32),
        new THREE.MeshBasicMaterial({ color: 0xaaf8ff, transparent: true, opacity: 0.9 })
    );
    coreGroup.add(coreMesh);

    // Orbital rings
    [
        { r: 2.6, tube: 0.012, rx: Math.PI/2, ry: 0,          rz: 0          },
        { r: 2.4, tube: 0.010, rx: 0.4,       ry: Math.PI/6,  rz: 0          },
        { r: 2.8, tube: 0.008, rx: 0,         ry: 0,          rz: Math.PI/3  },
    ].forEach(cfg => {
        const ring = new THREE.Mesh(
            new THREE.TorusGeometry(cfg.r, cfg.tube, 16, 120),
            new THREE.MeshBasicMaterial({ color: 0x00c8ff, transparent: true, opacity: 0.55 })
        );
        ring.rotation.set(cfg.rx, cfg.ry, cfg.rz);
        coreGroup.add(ring);
        rings.push(ring);
    });

    // Particles
    const pos = new Float32Array(180 * 3);
    for (let i = 0; i < 180; i++) {
        const r   = 3.2 + Math.random() * 1.5;
        const phi = Math.acos(2 * Math.random() - 1);
        const th  = Math.random() * Math.PI * 2;
        pos[i*3]   = r * Math.sin(phi) * Math.cos(th);
        pos[i*3+1] = r * Math.sin(phi) * Math.sin(th);
        pos[i*3+2] = r * Math.cos(phi);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    scene.add(new THREE.Points(geo, new THREE.PointsMaterial({ color: 0x00c8ff, size: 0.04, transparent: true, opacity: 0.7 })));

    animateThree();
}

const clock3 = { start: Date.now(), t: () => (Date.now() - clock3.start) / 1000 };

function animateThree() {
    requestAnimationFrame(animateThree);
    const t = clock3.t();

    if (coreGroup) {
        let rotSpeed, breatheRate, breatheAmp, coreScale;

        switch (currentState) {
            case 'LISTENING':
                // Pulsing slow — breathes fast, red glow
                rotSpeed   = 0.5;
                breatheRate = 2.8;
                breatheAmp  = 0.12;
                coreScale   = 1.0;
                break;
            case 'WAKE':
                // Quick burst spin
                rotSpeed   = 3.5;
                breatheRate = 4.0;
                breatheAmp  = 0.18;
                coreScale   = 1.15;
                break;
            case 'PROCESSING':
                // Fast continuous spin
                rotSpeed   = 4.0;
                breatheRate = 1.5;
                breatheAmp  = 0.06;
                coreScale   = 1.05;
                break;
            case 'SLEEP':
                // Almost still
                rotSpeed   = 0.08;
                breatheRate = 0.4;
                breatheAmp  = 0.01;
                coreScale   = 0.85;
                break;
            case 'SPEAKING':
                // Gentle glow + slow expand — Jarvis is talking
                rotSpeed   = 0.35;
                breatheRate = 1.8;
                breatheAmp  = 0.08;
                coreScale   = 1.08;
                break;
            case 'SHUTDOWN':
                rotSpeed   = 6.0;
                breatheRate = 5.0;
                breatheAmp  = 0.25;
                coreScale   = 1.2;
                break;
            default: // WAITING / READY
                rotSpeed   = 0.18;
                breatheRate = 1.2;
                breatheAmp  = 0.03;
                coreScale   = 1.0;
        }

        coreGroup.rotation.y = t * rotSpeed;
        coreGroup.rotation.z = t * rotSpeed * 0.33;

        const breathe = coreScale + Math.sin(t * breatheRate) * breatheAmp;
        coreGroup.scale.setScalar(breathe);
    }

    const ringBase = currentState === 'PROCESSING' ? 0.025
                  : currentState === 'LISTENING'   ? 0.012
                  : currentState === 'SLEEP'        ? 0.001
                  : 0.005;
    rings[0] && (rings[0].rotation.z += ringBase * 0.8);
    rings[1] && (rings[1].rotation.y += ringBase * 1.2);
    rings[2] && (rings[2].rotation.x += ringBase * 0.6);

    renderer.render(scene, camera);
}

// ─── Update Three.js materials per state ───────────────
const STATE_COLORS = {
    WAITING:    { core: 0xaaf8ff, outer: 0x00c8ff, inner: 0x00eeff, coreOpacity: 0.9,  outerOpacity: 0.35 },
    LISTENING:  { core: 0x9b59ff, outer: 0x7b3fff, inner: 0xbb88ff, coreOpacity: 1.0,  outerOpacity: 0.55 },
    WAKE:       { core: 0x00ff88, outer: 0x00ff88, inner: 0x88ffcc, coreOpacity: 1.0,  outerOpacity: 0.6  },
    PROCESSING: { core: 0x00eeff, outer: 0x00c8ff, inner: 0x44ffff, coreOpacity: 1.0,  outerOpacity: 0.5  },
    SPEAKING:   { core: 0x00ff88, outer: 0x00dd77, inner: 0x44ffaa, coreOpacity: 1.0,  outerOpacity: 0.50 },
    SLEEP:      { core: 0x334455, outer: 0x223344, inner: 0x334466, coreOpacity: 0.4,  outerOpacity: 0.12 },
    SHUTDOWN:   { core: 0xff2222, outer: 0xff0000, inner: 0xff4444, coreOpacity: 1.0,  outerOpacity: 0.7  },
    READY:      { core: 0xaaf8ff, outer: 0x00c8ff, inner: 0x00eeff, coreOpacity: 0.9,  outerOpacity: 0.35 },
};

function applyOrbState(stateKey) {
    const c = STATE_COLORS[stateKey] || STATE_COLORS.WAITING;
    if (!coreMesh) return;
    coreMesh.material.color.setHex(c.core);
    coreMesh.material.opacity = c.coreOpacity;
    outerMesh.material.color.setHex(c.outer);
    outerMesh.material.opacity = c.outerOpacity;
    innerMesh.material.color.setHex(c.inner);
    rings.forEach(r => r.material.color.setHex(c.outer));
}

window.addEventListener('resize', () => {
    const c = document.getElementById('canvas-container');
    camera.aspect = c.clientWidth / c.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(c.clientWidth, c.clientHeight);
});


// ─────────────────────────────────────────
//  CLOCK & UPTIME
// ─────────────────────────────────────────
const uptimeStart = Date.now();

function updateTime() {
    const now = new Date();
    document.getElementById('current-time').textContent =
        now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    document.getElementById('current-date').textContent =
        now.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

    const diff = Math.floor((Date.now() - uptimeStart) / 1000);
    const h = Math.floor(diff / 3600).toString().padStart(2,'0');
    const m = Math.floor((diff % 3600) / 60).toString().padStart(2,'0');
    const s = (diff % 60).toString().padStart(2,'0');
    document.getElementById('uptime-val').textContent = `${h}:${m}:${s}`;
}


// ─────────────────────────────────────────
//  SYSTEM STATS
// ─────────────────────────────────────────
async function fetchStats() {
    try {
        const res  = await fetch('/api/stats');
        const data = await res.json();
        document.getElementById('cpu-bar').style.width = data.cpu + '%';
        document.getElementById('cpu-val').textContent  = data.cpu + '%';
        document.getElementById('ram-bar').style.width = data.ram + '%';
        document.getElementById('ram-val').textContent  = data.ram + '%';
    } catch (_) {}
}


// ─────────────────────────────────────────
//  TERMINAL LOG
// ─────────────────────────────────────────
function addLog(msg, type = '') {
    const log  = document.getElementById('terminal-log');
    const line = document.createElement('div');
    line.className = 'log-line' + (type ? ` ${type}-line` : '');
    line.textContent = `> ${msg}`;
    log.appendChild(line);
    log.scrollTop = log.scrollHeight;
}

// ─── Chat bubble (primary conversation UI) ───────────────
function addChatBubble(msg, role) {
    // role: 'user' | 'jarvis'
    const body   = document.getElementById('chat-body');
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role}`;

    const label = document.createElement('span');
    label.className = 'bubble-label';
    label.textContent = role === 'user' ? 'YOU' : 'JARVIS';

    const text = document.createElement('div');
    text.className = 'bubble-text';
    text.textContent = msg;

    bubble.appendChild(label);
    bubble.appendChild(text);
    body.appendChild(bubble);
    body.scrollTop = body.scrollHeight;
}


// ─────────────────────────────────────────
//  STATUS + WAKE WORD INDICATOR
// ─────────────────────────────────────────
const STATUS_MAP = {
    WAITING:    { label: 'WAITING FOR WAKE WORD',  dot: '#4a7a99',  glow: '0 0 8px #4a7a99',   intensity: 0 },
    WAKE:       { label: 'WAKE WORD DETECTED!',    dot: '#00ff88',  glow: '0 0 18px #00ff88',  intensity: 1 },
    LISTENING:  { label: 'LISTENING...',            dot: '#9b59ff',  glow: '0 0 20px #9b59ff',  intensity: 1 },
    PROCESSING: { label: 'PROCESSING...',           dot: '#00c8ff',  glow: '0 0 18px #00c8ff',  intensity: 1 },
    SPEAKING:   { label: 'SPEAKING...',             dot: '#00ff88',  glow: '0 0 18px #00ff88',  intensity: 0.5 },
    SLEEP:      { label: 'SLEEP MODE',              dot: '#333355',  glow: '0 0 5px #333355',   intensity: 0 },
    SHUTDOWN:   { label: 'SHUTTING DOWN...',        dot: '#ff4b4b',  glow: '0 0 20px #ff4b4b',  intensity: 2 },
    RESTART:    { label: 'RESTARTING...',           dot: '#00c8ff',  glow: '0 0 20px #00c8ff',  intensity: 2 },
    READY:      { label: 'SYSTEM READY',            dot: '#00ff88',  glow: '0 0 12px #00ff88',  intensity: 0 },
};

function setStatus(statusKey, customLabel) {
    const s   = STATUS_MAP[statusKey] || STATUS_MAP.READY;
    const dot = document.getElementById('status-glow');
    const txt = document.getElementById('status-text');
    txt.textContent  = customLabel || s.label;
    dot.style.background = s.dot;
    dot.style.boxShadow  = s.glow;
    vizIntensity = s.intensity;

    // 🔑 Set data-state on body so CSS can react globally
    document.body.setAttribute('data-state', statusKey);

    // 🔮 Update Three.js orb to match state
    currentState = statusKey;
    applyOrbState(statusKey);

    // Update mic button appearance
    const mic = document.getElementById('mic-btn');
    if (statusKey === 'LISTENING' || statusKey === 'WAKE') {
        mic.classList.add('active');
    } else {
        mic.classList.remove('active');
    }
}

// Also update the wake-word badge
function setWakeLabel(text) {
    const el = document.getElementById('wake-label');
    if (el) el.textContent = text;
}


// ─────────────────────────────────────────
//  SENTIMENT GAUGE
// ─────────────────────────────────────────
const SENTIMENTS = [
    { label: 'CRITICAL', color: '#ff2222', angle: -80 },
    { label: 'NEGATIVE', color: '#ff6600', angle: -45 },
    { label: 'STABLE',   color: '#00ff88', angle:  20 },
    { label: 'POSITIVE', color: '#00cc88', angle:  55 },
    { label: 'OPTIMAL',  color: '#00ffcc', angle:  80 },
];
let sentimentIdx = 2;

function updateSentiment(idx) {
    const s   = SENTIMENTS[Math.max(0, Math.min(SENTIMENTS.length - 1, idx))];
    document.getElementById('sentiment-arrow').style.transform = `rotate(${s.angle}deg)`;
    const lbl = document.getElementById('sentiment-label');
    lbl.textContent = s.label;
    lbl.style.color = s.color;
    lbl.style.textShadow = `0 0 8px ${s.color}`;
}


// ─────────────────────────────────────────
//  SSE — Subscribe to backend state stream
// ─────────────────────────────────────────
function connectSSE() {
    const es = new EventSource('/api/stream');

    es.onmessage = (e) => {
        const msg = JSON.parse(e.data);

        if (msg.type === 'connected') {
            addLog('SSE stream connected. Wake word engine active.');
            // Clear stale chat bubbles from previous session
            const chatBody = document.getElementById('chat-body');
            if (chatBody) {
                chatBody.innerHTML = `
                    <div class="chat-bubble jarvis">
                        <span class="bubble-label">JARVIS</span>
                        <div class="bubble-text">Neural link established. All systems nominal, Sir. Say <em>Hey Jarvis</em> or type below to begin.</div>
                    </div>`;
            }
            return;
        }

        if (msg.type === 'state') {
            const { status, message } = msg.data;
            setStatus(status, message);
            setWakeLabel(message);

            // Sentiment nudge
            if (status === 'WAKE' || status === 'LISTENING') {
                sentimentIdx = Math.min(4, sentimentIdx + 1);
            } else if (status === 'SHUTDOWN') {
                sentimentIdx = 0;
            }
            updateSentiment(sentimentIdx);
        }

        if (msg.type === 'log') {
            const { message, type } = msg.data;
            addLog(message, type);  // always goes to debug terminal

            // Push to chat bubble UI
            if (type === 'user') {
                // Strip "User: " prefix if present
                const text = message.startsWith('User: ') ? message.slice(6) : message;
                addChatBubble(text, 'user');
            } else if (type === 'jarvis') {
                const text = message.startsWith('Jarvis: ') ? message.slice(8) : message;
                addChatBubble(text, 'jarvis');
                sentimentIdx = Math.min(4, sentimentIdx + 1);
                updateSentiment(sentimentIdx);
            }
        }
    };

    es.onerror = () => {
        addLog('SSE connection lost. Reconnecting...', 'error');
        setTimeout(connectSSE, 500);   // fast reconnect — don't miss state events
        es.close();
    };
}


// ─────────────────────────────────────────
//  MANUAL COMMAND (text input)
// ─────────────────────────────────────────
async function sendCommand(query) {
    if (!query || !query.trim()) return;
    try {
        await fetch('/api/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        // Response comes back via SSE log broadcast
    } catch (e) {
        addLog('Error: Could not reach Jarvis backend.', 'error');
    }
}


// ─────────────────────────────────────────
//  MANUAL MIC BUTTON (fallback)
// ─────────────────────────────────────────
document.getElementById('mic-btn').addEventListener('click', async () => {
    const btn = document.getElementById('mic-btn');
    btn.classList.add('active');
    try {
        const res  = await fetch('/api/voice');
        const data = await res.json();
        if (data.query) {
            sendCommand(data.query);
        } else {
            addLog('No speech detected.');
        }
    } catch (_) {
        addLog('Voice API error.', 'error');
    } finally {
        btn.classList.remove('active');
    }
});


// ─────────────────────────────────────────
//  TEXT INPUT
// ─────────────────────────────────────────
document.getElementById('user-input').addEventListener('keypress', e => {
    if (e.key === 'Enter') {
        const inp = e.target;
        sendCommand(inp.value.trim());
        inp.value = '';
    }
});


// ─────────────────────────────────────────
//  MODULE TOGGLE
// ─────────────────────────────────────────
document.querySelectorAll('.module-item').forEach(item => {
    item.addEventListener('click', () => item.classList.toggle('active'));
});


// ─────────────────────────────────────────
//  INIT
// ─────────────────────────────────────────
window.addEventListener('load', () => {
    initThree();
    updateTime();
    fetchStats();
    updateSentiment(sentimentIdx);
    connectSSE();

    setInterval(updateTime, 1000);
    setInterval(fetchStats, 3000);

    // Default to WAITING state until SSE confirms
    setStatus('WAITING');
    setTimeout(() => addLog('Neural interface loaded. Waiting for wake word...'), 500);

    // ── Debug log toggle ──────────────────────────────────
    document.getElementById('debug-toggle').addEventListener('click', () => {
        document.getElementById('chat-container').classList.add('hidden');
        document.getElementById('terminal-container').classList.remove('hidden');
    });
    document.getElementById('debug-close').addEventListener('click', () => {
        document.getElementById('terminal-container').classList.add('hidden');
        document.getElementById('chat-container').classList.remove('hidden');
    });
});
