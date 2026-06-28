/**
 * dashboard/app.js
 * Tanggung jawab: Mengelola koneksi WebSocket telemetri dan merender Dashboard secara dinamis.
 */

const wsUri = "ws://127.0.0.1:8000";
let websocket;
let auditHistory = [];

function connect() {
    websocket = new WebSocket(wsUri);
    
    websocket.onopen = () => {
        const box = document.getElementById("status-box");
        box.innerText = "LIVE";
        box.className = "bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800 text-[9px] font-bold text-emerald-400";
    };

    websocket.onclose = () => {
        const box = document.getElementById("status-box");
        box.innerText = "OFFLINE";
        box.className = "bg-red-950 px-2 py-0.5 rounded border border-red-800 text-[9px] font-bold text-red-400";
        setTimeout(connect, 2000);
    };

    websocket.onmessage = (evt) => {
        try {
            const data = JSON.parse(evt.data);
            updateDashboard(data);
        } catch (e) {
            console.error("Payload Error:", e);
        }
    };
}

function updateDashboard(d) {
    // Basic Info
    document.getElementById("turn-num").innerText = "T-" + String(d.turn).padStart(2, '0');
    document.getElementById("game-id-text").innerText = "MATCH_ID: " + d.game_id;
    document.getElementById("location-name").innerText = d.location_name;
    
    // Physical Bars
    document.getElementById("hp-text").innerText = `${d.hp}/${d.max_hp}`;
    document.getElementById("hp-bar").style.width = (d.hp / d.max_hp * 100) + "%";
    document.getElementById("ep-text").innerText = `${d.ep}/${d.max_ep}`;
    document.getElementById("ep-bar").style.width = (d.ep / d.max_ep * 100) + "%";
    
    // Stats
    document.getElementById("stat-def").innerText = d.defense;
    document.getElementById("stat-kills").innerText = d.kills;
    document.getElementById("badai-status").innerText = "STORM: " + d.badai_status;
    
    // Decision Highlight
    document.getElementById("decision-header").innerText = d.decision;
    document.getElementById("decision-detail").innerText = d.thought;
    document.getElementById("cooldown-status").innerText = d.can_act ? "READY TO ACT" : "COOLDOWN (30s)";

    // List Rendering
    const renderItems = (items) => items.map(i => `<li>• ${i.name} (T${i.tier || 1})</li>`).join("");
    document.getElementById("bag-items").innerHTML = renderItems(d.bag_items) || "<li>Bag Empty</li>";
    document.getElementById("ground-items").innerHTML = renderItems(d.ground_items) || "<li>No Loot</li>";

    addAuditRecord(d);
}

function addAuditRecord(d) {
    const key = `${d.turn}-${d.decision}`;
    if (auditHistory.some(a => a.key === key)) return;

    const record = {
        key: key,
        turn: d.turn,
        mode: d.mode,
        action: d.decision,
        thought: d.thought,
        detail: d.decision_detail,
        stats: `HP:${d.hp} | EP:${d.ep} | Loc:${d.location_name}`
    };

    auditHistory.unshift(record);
    if (auditHistory.length > 50) auditHistory.pop(); // Batasi 50 riwayat terakhir

    const body = document.getElementById("audit-log-body");
    const row = document.createElement("tr");
    row.className = "border-b border-slate-800/30 hover:bg-indigo-900/10";
    row.innerHTML = `
        <td class="p-2 text-indigo-400 font-bold">T-${d.turn}</td>
        <td class="p-2 text-slate-500 font-bold uppercase text-[8px]">${d.mode}</td>
        <td class="p-2 text-center"><span class="bg-indigo-900/30 text-indigo-300 px-1.5 py-0.5 rounded text-[8px] font-bold border border-indigo-800/50">${d.decision}</span></td>
        <td class="p-2 italic text-slate-300 leading-tight">${d.thought} <br><span class="text-[8px] text-slate-500 not-italic">Target: ${d.decision_detail}</span></td>
        <td class="p-2 text-slate-500 text-[8px] text-right font-mono">${record.stats}</td>
    `;
    body.insertBefore(row, body.firstChild);
}

function copyAuditLog() {
    if (auditHistory.length === 0) return alert("Belum ada data.");
    
    const text = auditHistory.map(r => 
        `[TURN ${r.turn}] [MODE ${r.mode}] ACTION: ${r.action}\n` +
        `REASON: ${r.thought}\n` +
        `STATS: ${r.stats}\n` +
        `----------------------------------------`
    ).join("\n");

    navigator.clipboard.writeText(text).then(() => {
        alert("AUDIT LOG COPIED! Tempelkan (Ctrl+V) ke chat AI untuk dianalisis.");
    });
}

window.onload = connect;