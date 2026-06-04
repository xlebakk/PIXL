import { loadFile } from './upload.js';
import { runCommand, resetImage, downloadResult, CHIPS } from './commands.js';
import { addLog } from './ui.js';

// Инициализация чипов
const chipsEl = document.getElementById("chips");
CHIPS.forEach(([label, cmd]) => {
  const el = document.createElement("button");
  el.className = "chip";
  el.textContent = label;
  el.onclick = () => { document.getElementById("cmd-input").value = cmd; runCommand(); };
  chipsEl.appendChild(el);
});

// События загрузки
const dropZone = document.getElementById("drop-zone");
dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("over"); });
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("over"));
dropZone.addEventListener("drop", e => {
  e.preventDefault(); dropZone.classList.remove("over");
  if (e.dataTransfer.files[0]) loadFile(e.dataTransfer.files[0]);
});
document.getElementById("file-input").addEventListener("change", e => {
  if (e.target.files[0]) loadFile(e.target.files[0]);
});

// Кнопки и команды
document.getElementById("run-btn").onclick = runCommand;
document.getElementById("reset-btn").onclick = resetImage;
document.getElementById("dl-btn").onclick = downloadResult;
document.getElementById("cmd-input").addEventListener("keydown", e => { if (e.key === "Enter") runCommand(); });

addLog("sys", "pixl ready", "rule-based parser · opencv");

document.getElementById('snap-btn').onclick = () => {
    const canvas = document.createElement('canvas');
    const img = document.querySelector('#camera-view img');
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    canvas.getContext('2d').drawImage(img, 0, 0);
    const b64 = canvas.toDataURL('image/jpeg');
    
    // Передаем в твою функцию обработки
    loadFileFromBase64(b64); 
    document.getElementById('camera-view').style.display = 'none';
};