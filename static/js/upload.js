import { renderToCanvas, setEnabled, setDot, addLog } from './ui.js';

export let currentB64 = null;
export let originalB64 = null;

export function setCurrentB64(val) { currentB64 = val; }

export function loadFile(file) {
    const reader = new FileReader();
    reader.onload = ev => {
        originalB64 = ev.target.result;
        currentB64 = ev.target.result;
        renderToCanvas(currentB64, () => {
            document.getElementById("file-info").classList.add("show");
            document.getElementById("file-name").textContent = file.name;
            document.getElementById("file-meta").textContent = Math.round(file.size / 1024) + " KB";
            setEnabled(true);
            setDot("ready");
            addLog("ok", file.name, "loaded");
            document.getElementById("badge-op").textContent = "original";
        });
    };
    reader.readAsDataURL(file);
}