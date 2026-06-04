import { setDot, setEnabled, addLog, renderToCanvas } from './ui.js';
import { currentB64, originalB64, setCurrentB64 } from './upload.js';

export const CHIPS = [
  ["удалить фон", "удали фон"],
  ["поверни 90°", "поверни на 90"],
  ["поверни 180°", "поверни на 180"],
  ["отразить →", "отразить горизонтально"],
  ["отразить ↕", "отразить вертикально"],
  ["ч/б", "чёрно-белый"],
  ["красный канал", "оставь только красный"],
  ["синий канал", "оставь только синий"],
  ["инверсия", "инвертировать"],
  ["ярче +60", "увеличь яркость на 60"],
  ["темнее −40", "уменьши яркость на 40"],
  ["контраст ×1.8", "контраст 1.8"],
  ["blur ×7", "размой с радиусом 7"],
  ["гаусс ×5", "гауссово размытие 5"],
  ["сепия", "сепия"],
  ["canny edges", "найди края"],
  ["резкость", "резкость"],
];

export async function runCommand() {
  const input = document.getElementById("cmd-input");
  const cmd = input.value.trim();
  if (!cmd || !currentB64) return;

  const overlay = document.getElementById("proc-overlay");
  const bar = document.getElementById("proc-bar");
  const lbl = document.getElementById("proc-label");

  overlay.classList.add("show");
  lbl.textContent = cmd;
  bar.style.width = "0%";
  setDot("busy");
  setEnabled(false);

  let barT = setInterval(() => {
    const cur = parseFloat(bar.style.width) || 0;
    if (cur < 85) bar.style.width = (cur + Math.random() * 15) + "%";
  }, 120);

  try {
    const res = await fetch("/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command: cmd, image: currentB64 }),
    });
    const data = await res.json();

    clearInterval(barT);
    bar.style.width = "100%";

    if (data.error) {
      addLog("err", cmd, data.error);
      setDot("ready");
    } else {
      setCurrentB64(data.image);
      renderToCanvas(data.image, () => {
        document.getElementById("badge-op").textContent = data.op;
      });
      addLog("ok", cmd, data.op + " · " + data.size);
      setDot("ready");
      input.value = "";
    }
  } catch(e) {
    clearInterval(barT);
    addLog("err", "network error", e.message);
    setDot("");
  }
  setTimeout(() => overlay.classList.remove("show"), 300);
  setEnabled(true);
  input.focus();
}

export function resetImage() {
  if (!originalB64) return;
  setCurrentB64(originalB64);
  renderToCanvas(originalB64, () => {
    document.getElementById("badge-op").textContent = "reset";
  });
  addLog("sys", "reset", "restored original");
}

export function downloadResult() {
  if (!currentB64) return;
  const a = document.createElement("a");
  a.href = currentB64;
  a.download = "pixl_result.jpg";
  a.click();
}