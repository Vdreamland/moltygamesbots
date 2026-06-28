const wsUri = "ws://127.0.0.1:8000";
let websocket;
let auditHistory = [];

function connect() {
    websocket = new WebSocket(wsUri);
    
    websocket.onopen = () => {
        const box = document.getElementById("status-box");
        box.innerHTML = '<i class="fa-solid fa-circle mr-1 animate-pulse"></i> LIVE';
        box.className = "bg-emerald-950 px-3 py-1 rounded border border-emerald-800 text-[9px] font-bold text-emerald-400";
    };

    websocket.onclose = () => {
        const box = document.getElementById("status-box");
        box.innerHTML = '<i class="fa-solid fa-circle mr-1"></i> OFFLINE';
        box.className = "bg-red-950 px-3 py-1 rounded border border-red-800 text-[9px] font-bold text-red-400";
        setTimeout(connect, 2000);
    };

    websocket.onmessage = (evt) => {
        const data = JSON.parse(evt.data);
        updateUI(data);
    };
}

function updateUI(d) {
    document.getElementById("turn-num").innerText = "T-" + String(d.turn).padStart(2, '0');
    document.getElementById("game-id-text").innerText = "Match: " + d.game_id.substring(0, 13) + "...";
    document.getElementById("location-name").innerText = d.location_name;
    
    document.getElementById("hp-text").innerText = `${d.hp}/${d.max_hp}`;
    document.getElementById("hp-bar").style.width = (d.hp / d.max_hp * 100) + "%";
    document.getElementById("ep-text").innerText = `${d.ep}/${d.max_ep}`;
    document.getElementById("ep-bar").style.width = (d.ep / d.max_ep * 100) + "%";
    
    document.getElementById("stat-def-kills").innerText = `${d.defense} / ${d.kills}`;
    document.getElementById("alert-gauge").innerText = `${d.alert_gauge}/10`;
    document.getElementById("badai-status").innerText = "STORM: " + d.badai_status;
    
    document.getElementById("decision-header").innerText = d.decision;
    document.getElementById("decision-detail").innerText = d.thought;
    document.getElementById("cooldown-status").innerText = d.can_act ? "READY TO ACT" : "COOLDOWN (30s)";

    // Inventory List Grouping
    const bagHtml = d.bag_items.map(i => `<li>• ${i.name} (T${i.tier})</li>`).join("");
    document.getElementById("bag-items").innerHTML = bagHtml || "<li>Tas Kosong</li>";

    const groundHtml = d.ground_items.map(i => `<li>• ${i.name} (T${i.tier})</li>`).join("");
    document.getElementById("ground-items").innerHTML = groundHtml || "<li>No Loot</li>";

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
        detail: d.decision_detail,
        thought: d.thought,
        stats: `HP:${d.hp} EP:${d.ep} Loc:${d.location_name}`
    };

    auditHistory.unshift(record);
    if (auditHistory.length > 100) auditHistory.pop();

    const body = document.getElementById("audit-log-body");
    if (auditHistory.length === 1) body.innerHTML = "";

    const row = document.createElement("tr");
    row.className = "border-b border-slate-800/50 hover:bg-indigo-900/10 transition-colors";
    row.innerHTML = `
        <td class="p-2 text-indigo-400 font-bold">T-${d.turn}</td>
        <td class="p-2 text-slate-500 font-bold">${d.mode}</td>
        <td class="p-2 text-slate-200">${d.decision}</td>
        <td class="p-2 italic text-slate-400">${d.thought}</td>
        <td class="p-2 text-slate-500 text-[9px]">${record.stats}</td>
    `;
    body.insertBefore(row, body.firstChild);
}

function copyAuditLog() {
    if (auditHistory.length === 0) return alert("Belum ada data untuk di copy.");
    
    const text = auditHistory.map(r => 
        `[TURN ${r.turn}] [MODE ${r.mode}] ACTION: ${r.action}\n` +
        `DETAIL: ${r.detail}\n` +
        `REASON: ${r.thought}\n` +
        `STATS: ${r.stats}\n` +
        `----------------------------------------`
    ).join("\n");

    navigator.clipboard.writeText(text).then(() => {
        alert("AUDIT LOG COPIED! Silakan tempel (Ctrl+V) ke chat AI untuk dianalisis.");
    });
}

window.onload = connect;