const wsUri = "ws://127.0.0.1:8000";
let websocket;

function connect() {
    websocket = new WebSocket(wsUri);
    
    websocket.onopen = function(evt) {
        console.log("Connected to Telemetry Server");
        document.getElementById("status-indicator").classList.remove("bg-red-500");
        document.getElementById("status-indicator").classList.add("bg-emerald-500", "animate-pulse");
        document.getElementById("status-text").innerText = "CONNECTED";
        document.getElementById("status-text").classList.remove("text-slate-400");
        document.getElementById("status-text").classList.add("text-emerald-400");
    };
    
    websocket.onclose = function(evt) {
        console.log("Disconnected from Telemetry Server");
        document.getElementById("status-indicator").classList.remove("bg-emerald-500", "animate-pulse");
        document.getElementById("status-indicator").classList.add("bg-red-500");
        document.getElementById("status-text").innerText = "DISCONNECTED";
        document.getElementById("status-text").classList.remove("text-emerald-400");
        document.getElementById("status-text").classList.add("text-slate-400");
        
        // Auto-reconnect setiap 3 detik
        setTimeout(connect, 3000);
    };
    
    websocket.onmessage = function(evt) {
        const data = JSON.parse(evt.data);
        updateDashboard(data);
    };
    
    websocket.onerror = function(evt) {
        console.error("Telemetry websocket error:", evt);
    };
}

function updateDashboard(data) {
    // 1. Update Header & IDs
    document.getElementById("turn-num").innerText = "TURN " + String(data.turn).padStart(2, '0');
    document.getElementById("game-id").innerText = "Game ID: " + data.game_id;
    document.getElementById("location-name").innerText = data.location_name;
    document.getElementById("location-id").innerText = "(" + data.location_id.substring(0, 8) + "...)";
    
    // 2. HP Bar & Text
    const hpPercent = (data.hp / data.max_hp) * 100;
    document.getElementById("hp-bar").style.width = hpPercent + "%";
    document.getElementById("hp-text").innerText = `${data.hp}/${data.max_hp} HP`;
    
    // 3. EP Bar & Text
    const epPercent = (data.ep / data.max_ep) * 100;
    document.getElementById("ep-bar").style.width = epPercent + "%";
    document.getElementById("ep-text").innerText = `${data.ep}/${data.max_ep} EP`;
    
    // 4. Update Stats & Equipment
    document.getElementById("stat-def").innerText = data.defense;
    document.getElementById("stat-kills").innerText = data.kills;
    document.getElementById("equipped-weapon").innerText = data.weapon;
    document.getElementById("equipped-armor").innerText = data.armor;
    document.getElementById("alert-gauge").innerText = data.alert_gauge + "/10";
    document.getElementById("badai-status").innerText = data.badai_status;
    
    // Status Badai Color
    const badaiEl = document.getElementById("badai-status");
    badaiEl.className = "text-xs font-extrabold px-3 py-1 rounded ";
    if (data.badai_status === "AMAN") {
        badaiEl.classList.add("bg-emerald-950", "text-emerald-400");
    } else {
        badaiEl.classList.add("bg-red-950", "text-red-400", "animate-pulse");
    }
    
    // 5. Bag Items (Grouped Visual)
    const bagList = document.getElementById("bag-items");
    bagList.innerHTML = "";
    if (data.bag_items.length === 0) {
        bagList.innerHTML = `<li class="text-slate-500 text-sm italic py-2 text-center">Tas Kosong</li>`;
    } else {
        const counts = {};
        data.bag_items.forEach(item => {
            const key = `${item.name} (${item.type})`;
            counts[key] = (counts[key] || 0) + 1;
        });
        Object.keys(counts).forEach(key => {
            bagList.innerHTML += `
                <li class="flex justify-between items-center bg-slate-950 p-2 rounded-lg text-xs font-semibold mb-1 border border-slate-800">
                    <span>${key}</span>
                    <span class="bg-indigo-600 text-[10px] px-2 py-0.5 rounded-full font-bold">x${counts[key]}</span>
                </li>`;
        });
    }
    
    // 6. Ground Loot Items (Grouped Visual)
    const groundList = document.getElementById("ground-items");
    groundList.innerHTML = "";
    if (data.ground_items.length === 0) {
        groundList.innerHTML = `<li class="text-slate-500 text-sm italic py-2 text-center">Tidak ada barang</li>`;
    } else {
        const counts = {};
        data.ground_items.forEach(item => {
            const key = `${item.name} (${item.type})`;
            counts[key] = (counts[key] || 0) + 1;
        });
        Object.keys(counts).forEach(key => {
            groundList.innerHTML += `
                <li class="flex justify-between items-center bg-slate-950 p-2 rounded-lg text-xs font-semibold mb-1 border border-slate-800">
                    <span>${key}</span>
                    <span class="bg-amber-600 text-[10px] px-2 py-0.5 rounded-full font-bold">x${counts[key]}</span>
                </li>`;
        });
    }
    
    // 7. Connections (Fog of War Sektor)
    const connList = document.getElementById("connections");
    connList.innerHTML = "";
    data.connections.forEach(conn => {
        connList.innerHTML += `
            <span class="bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg text-xs font-bold mr-2 mb-2 flex items-center">
                <i class="fa-solid fa-circle-dot text-indigo-400 mr-2"></i>
                ${conn.name}
            </span>`;
    });
    
    // 8. Decision Header / Cooldown Status
    document.getElementById("cooldown-status").innerText = data.cooldown_status;
    document.getElementById("decision-header").innerText = data.decision;
    document.getElementById("decision-detail").innerText = data.decision_detail;
    
    // 9. Kirim ke Audit Log
    addAuditLog(data);
}

const loggedTurns = new Set();
function addAuditLog(data) {
    const key = `${data.game_id}-${data.turn}-${data.decision}`;
    if (loggedTurns.has(key)) return; 
    loggedTurns.add(key);
    
    const auditBody = document.getElementById("audit-log-body");
    
    // Bersihkan placeholder jika ini log pertama
    if (loggedTurns.size === 1) {
        auditBody.innerHTML = "";
    }
    
    const row = document.createElement("tr");
    row.className = "border-b border-slate-900 hover:bg-slate-900/50 transition-colors";
    
    const timeStr = new Date().toLocaleTimeString();
    
    row.innerHTML = `
        <td class="p-3 text-slate-500 font-mono text-[10px]">${timeStr}</td>
        <td class="p-3 text-indigo-400 font-bold font-mono">T-${String(data.turn).padStart(2, '0')}</td>
        <td class="p-3"><span class="bg-slate-900 text-[10px] font-bold px-2 py-0.5 rounded border border-slate-800">${data.decision}</span></td>
        <td class="p-3 text-slate-300 font-medium">${data.decision_detail}</td>
        <td class="p-3 italic text-slate-400 font-serif">${data.thought}</td>
    `;
    
    auditBody.insertBefore(row, auditBody.firstChild); // Masukkan ke baris paling atas
}

window.onload = function() {
    connect();
};