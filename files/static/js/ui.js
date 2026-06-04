export function setDot(state) {
    const d = document.getElementById("status-dot");
    d.className = "";
    if (state) d.classList.add(state);
}

export function setEnabled(v) {
    ["cmd-input", "run-btn", "reset-btn", "dl-btn"].forEach(id => {
        document.getElementById(id).disabled = !v;
    });
}

export function addLog(type, main, sub) {
    const feed = document.getElementById("log");
    const tick = type === "ok" ? "+" : type === "err" ? "×" : "·";
    const entry = document.createElement("div");
    entry.className = "log-entry";
    entry.innerHTML = 
        `<span class="log-tick ${type}">${tick}</span>` +
        `<div class="log-text"><b>${main}</b><span class="log-code">${sub || ""}</span></div>`;
    feed.insertBefore(entry, feed.firstChild);
}

export function renderToCanvas(src, cb) {
    const img = new Image();
    img.onload = () => {
        const canvas = document.getElementById("preview-canvas");
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        canvas.getContext("2d").drawImage(img, 0, 0);
        document.getElementById("empty-state").style.display = "none";
        document.getElementById("canvas-wrap").style.display = "block";
        document.getElementById("badge-size").textContent = `${img.naturalWidth} × ${img.naturalHeight} px`;
        if (cb) cb();
    };
    img.src = src;
}