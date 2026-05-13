import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="SPOPS Live Signal Chart",
    page_icon="📈",
    layout="wide",
)

TOKEN_ADDRESS = "EkDGB5fbPXiRmDDjxKcC7dFjzvFZj2KT9t7oeyyPx4SX"
POOL_ADDRESS = "8LTRgxZ2KWDc2sDGuYAe5VtDgguAzteSeQUJisLQ5BVA"
html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <style>
    :root {{
      --ink: #111111;
      --muted: #5f6368;
      --blue: #0033A0;
      --grid: #d9dde3;
      --paper: #ffffff;
      --soft: #f5f7fa;
      --green: #0b7a3b;
      --red: #b42318;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: Helvetica, Arial, sans-serif;
    }}

    .wrap {{
      padding: 24px 28px 32px;
      max-width: 1280px;
      margin: 0 auto;
    }}

    .header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      gap: 20px;
      border-bottom: 1px solid #e4e7ec;
      padding-bottom: 18px;
      margin-bottom: 18px;
    }}

    .title {{
      font-size: 30px;
      font-weight: 700;
      letter-spacing: -0.03em;
      margin: 0;
    }}

    .subtitle {{
      color: var(--muted);
      margin-top: 6px;
      font-size: 13px;
    }}

    .priceBox {{
      text-align: right;
    }}

    .priceLabel {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}

    .price {{
      font-size: 34px;
      font-weight: 700;
      letter-spacing: -0.04em;
      margin-top: 2px;
    }}

    .status {{
      font-size: 12px;
      color: var(--muted);
      margin-top: 4px;
    }}

    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 18px;
      align-items: center;
    }}

    button {{
      appearance: none;
      border: 1px solid #d0d5dd;
      background: #ffffff;
      color: #111111;
      border-radius: 8px;
      padding: 9px 14px;
      font-family: Helvetica, Arial, sans-serif;
      font-size: 13px;
      cursor: pointer;
      transition: all 0.12s ease;
    }}

    button:hover {{
      border-color: var(--blue);
      color: var(--blue);
    }}

    button.primary {{
      background: var(--blue);
      color: #ffffff;
      border-color: var(--blue);
      font-weight: 700;
    }}

    button.primary:hover {{
      background: #002878;
    }}

    .note {{
      font-size: 12px;
      color: var(--muted);
      margin-left: 4px;
    }}

    .tabs {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 6px 0 16px;
    }}

    .tab {{
      background: var(--soft);
      border: 1px solid #e4e7ec;
      border-radius: 12px;
      padding: 10px 14px;
      min-width: 132px;
    }}

    .tabName {{
      font-size: 11px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 4px;
    }}

    .tabValue {{
      font-size: 18px;
      font-weight: 700;
    }}

    .positive {{
      color: var(--green);
    }}

    .negative {{
      color: var(--red);
    }}

    .neutral {{
      color: var(--muted);
    }}

    .chartShell {{
      border: 1px solid #e4e7ec;
      border-radius: 16px;
      padding: 18px;
      background: #ffffff;
      box-shadow: 0 10px 30px rgba(16, 24, 40, 0.06);
    }}

    canvas {{
      width: 100%;
      height: 540px;
      display: block;
    }}

    .footer {{
      display: flex;
      justify-content: space-between;
      color: var(--muted);
      font-size: 12px;
      margin-top: 12px;
      gap: 16px;
      flex-wrap: wrap;
    }}

    .error {{
      color: var(--red);
      font-weight: 700;
    }}
  </style>
</head>

<body>
  <div class="wrap">
    <div class="header">
      <div>
        <h1 class="title">SPOPS Live Signal Chart</h1>
        <div class="subtitle">Browser-native audio signals · DEX Screener live feed · 8-decimal sensitivity</div>
      </div>

      <div class="priceBox">
        <div class="priceLabel">Current Price</div>
        <div id="price" class="price">$0.00000000</div>
        <div id="status" class="status">Click Start to unlock audio.</div>
      </div>
    </div>

    <div class="controls">
      <button id="startBtn" class="primary">Start Live Chart + Unlock Audio</button>
      <button id="stopBtn">Stop</button>
      <button id="upTest">Test Up Sound</button>
      <button id="downTest">Test Down Sound</button>
      <button id="canonTest">Test Canon Sound</button>
      <span class="note">If test sounds work, live signals will work when price changes.</span>
    </div>

    <div class="tabs">
      <div class="tab"><div class="tabName">Minute</div><div id="m1" class="tabValue neutral">—</div></div>
      <div class="tab"><div class="tabName">Hour</div><div id="h1" class="tabValue neutral">—</div></div>
      <div class="tab"><div class="tabName">Day</div><div id="d1" class="tabValue neutral">—</div></div>
      <div class="tab"><div class="tabName">Week</div><div id="w1" class="tabValue neutral">—</div></div>
      <div class="tab"><div class="tabName">Month</div><div id="mo1" class="tabValue neutral">—</div></div>
      <div class="tab"><div class="tabName">Year</div><div id="y1" class="tabValue neutral">—</div></div>
      <div class="tab"><div class="tabName">All Time</div><div id="all" class="tabValue neutral">—</div></div>
    </div>

    <div class="chartShell">
      <canvas id="chart"></canvas>
    </div>

    <div class="footer">
      <div>Audio threshold: 0.00000001 price movement.</div>
      <div id="lastUpdate">Waiting for data…</div>
    </div>
  </div>

  <script>
    const TOKEN_ADDRESS = "{TOKEN_ADDRESS}";
    const API_URL = "https://api.dexscreener.com/latest/dex/tokens/" + TOKEN_ADDRESS;

    const FETCH_INTERVAL_MS = 500;
    const WINDOW_DURATION_SECONDS = 60;
    const PRICE_MOVEMENT_THRESHOLD = 1e-8;

    let running = false;
    let timer = null;
    let audioCtx = null;

    let prices = [];
    let times = [];
    let startTime = null;
    let lastPrice = null;
    let bullishCounter = 0;

    const priceEl = document.getElementById("price");
    const statusEl = document.getElementById("status");
    const lastUpdateEl = document.getElementById("lastUpdate");
    const canvas = document.getElementById("chart");
    const ctx = canvas.getContext("2d");

    function ensureAudio() {{
      if (!audioCtx) {{
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }}
      if (audioCtx.state === "suspended") {{
        audioCtx.resume();
      }}
    }}

    function playTone(freq, duration = 0.16, gain = 0.16) {{
      ensureAudio();

      const osc = audioCtx.createOscillator();
      const amp = audioCtx.createGain();

      osc.type = "sine";
      osc.frequency.value = freq;

      const now = audioCtx.currentTime;
      amp.gain.setValueAtTime(0.0001, now);
      amp.gain.exponentialRampToValueAtTime(gain, now + 0.015);
      amp.gain.exponentialRampToValueAtTime(0.0001, now + duration);

      osc.connect(amp);
      amp.connect(audioCtx.destination);

      osc.start(now);
      osc.stop(now + duration + 0.02);
    }}

    function playCanon() {{
      ensureAudio();

      const now = audioCtx.currentTime;

      const osc1 = audioCtx.createOscillator();
      const osc2 = audioCtx.createOscillator();
      const amp = audioCtx.createGain();

      osc1.type = "sine";
      osc2.type = "triangle";
      osc1.frequency.value = 78;
      osc2.frequency.value = 43;

      amp.gain.setValueAtTime(0.0001, now);
      amp.gain.exponentialRampToValueAtTime(0.24, now + 0.03);
      amp.gain.exponentialRampToValueAtTime(0.0001, now + 0.75);

      osc1.connect(amp);
      osc2.connect(amp);
      amp.connect(audioCtx.destination);

      osc1.start(now);
      osc2.start(now);
      osc1.stop(now + 0.8);
      osc2.stop(now + 0.8);
    }}

    function formatPrice(p) {{
      if (!Number.isFinite(p)) return "$0.00000000";
      return "$" + p.toFixed(8);
    }}

    function pct(current, baseline) {{
      if (!baseline || baseline === 0) return 0;
      return ((current - baseline) / baseline) * 100;
    }}

    function metricClass(v) {{
      if (v > 0) return "positive";
      if (v < 0) return "negative";
      return "neutral";
    }}

    function setMetric(id, value) {{
      const el = document.getElementById(id);
      el.innerText = (value >= 0 ? "+" : "") + value.toFixed(2) + "%";
      el.className = "tabValue " + metricClass(value);
    }}

    function baselineFor(seconds) {{
      if (prices.length === 0) return null;
      if (seconds === null) return prices[0];

      const currentTime = times[times.length - 1];
      const threshold = currentTime - seconds;

      for (let i = 0; i < times.length; i++) {{
        if (times[i] >= threshold) {{
          return prices[i];
        }}
      }}
      return prices[0];
    }}

    function updateMetrics(price) {{
      setMetric("m1", pct(price, baselineFor(60)));
      setMetric("h1", pct(price, baselineFor(3600)));
      setMetric("d1", pct(price, baselineFor(86400)));
      setMetric("w1", pct(price, baselineFor(604800)));
      setMetric("mo1", pct(price, baselineFor(2592000)));
      setMetric("y1", pct(price, baselineFor(31536000)));
      setMetric("all", pct(price, baselineFor(null)));
    }}

    async function fetchPrice() {{
      const res = await fetch(API_URL);
      if (!res.ok) throw new Error("DEX Screener returned " + res.status);

      const data = await res.json();
      const pairs = data.pairs || [];

      if (!pairs.length) throw new Error("No pairs returned.");

      pairs.sort((a, b) => {{
        const la = (a.liquidity && a.liquidity.usd) ? a.liquidity.usd : 0;
        const lb = (b.liquidity && b.liquidity.usd) ? b.liquidity.usd : 0;
        return lb - la;
      }});

      const price = parseFloat(pairs[0].priceUsd);
      if (!Number.isFinite(price)) throw new Error("No valid priceUsd.");

      return price;
    }}

    function resizeCanvas() {{
      const ratio = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = Math.floor(rect.width * ratio);
      canvas.height = Math.floor(rect.height * ratio);
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    }}

    function drawChart() {{
      resizeCanvas();

      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      const padL = 70;
      const padR = 30;
      const padT = 30;
      const padB = 54;

      ctx.clearRect(0, 0, width, height);

      // background
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, width, height);

      if (prices.length < 1) {{
        ctx.fillStyle = "#5f6368";
        ctx.font = "14px Helvetica, Arial";
        ctx.fillText("Waiting for live price data…", padL, padT + 20);
        return;
      }}

      const currentTime = times[times.length - 1];
      const windowStart = Math.max(0, currentTime - WINDOW_DURATION_SECONDS);

      const points = [];
      for (let i = 0; i < prices.length; i++) {{
        if (times[i] >= windowStart) {{
          points.push({{ t: times[i], p: prices[i] }});
        }}
      }}

      let minP = Math.min(...points.map(x => x.p));
      let maxP = Math.max(...points.map(x => x.p));

      if (minP === maxP) {{
        minP *= 0.995;
        maxP *= 1.005;
      }} else {{
        const range = maxP - minP;
        minP -= range * 0.07;
        maxP += range * 0.07;
      }}

      const plotW = width - padL - padR;
      const plotH = height - padT - padB;

      function xScale(t) {{
        const denom = Math.max(1, currentTime - windowStart);
        return padL + ((t - windowStart) / denom) * plotW;
      }}

      function yScale(p) {{
        return padT + (1 - (p - minP) / (maxP - minP)) * plotH;
      }}

      // grid
      ctx.strokeStyle = "#d9dde3";
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 5]);

      for (let i = 0; i <= 5; i++) {{
        const y = padT + (plotH / 5) * i;
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(width - padR, y);
        ctx.stroke();
      }}

      ctx.setLineDash([]);

      // axes labels
      ctx.fillStyle = "#5f6368";
      ctx.font = "11px Helvetica, Arial";
      ctx.textAlign = "right";

      for (let i = 0; i <= 5; i++) {{
        const y = padT + (plotH / 5) * i;
        const val = maxP - ((maxP - minP) / 5) * i;
        ctx.fillText("$" + val.toFixed(8), padL - 10, y + 4);
      }}

      // line
      if (points.length > 1) {{
        ctx.strokeStyle = "#0033A0";
        ctx.lineWidth = 2.4;
        ctx.beginPath();

        points.forEach((pt, idx) => {{
          const x = xScale(pt.t);
          const y = yScale(pt.p);
          if (idx === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }});

        ctx.stroke();

        // latest dot
        const last = points[points.length - 1];
        ctx.fillStyle = "#0033A0";
        ctx.beginPath();
        ctx.arc(xScale(last.t), yScale(last.p), 4, 0, Math.PI * 2);
        ctx.fill();
      }}

      // current price annotation
      ctx.fillStyle = "#111111";
      ctx.font = "bold 16px Helvetica, Arial";
      ctx.textAlign = "left";
      ctx.fillText("Current: " + formatPrice(prices[prices.length - 1]), padL, padT - 8);

      // x label
      ctx.fillStyle = "#5f6368";
      ctx.font = "12px Helvetica, Arial";
      ctx.textAlign = "center";
      ctx.fillText("Last 60 seconds", padL + plotW / 2, height - 18);
    }}

    async function tick() {{
      if (!running) return;

      try {{
        const price = await fetchPrice();

        const nowSec = (Date.now() - startTime) / 1000;
        prices.push(price);
        times.push(nowSec);

        priceEl.innerText = formatPrice(price);
        statusEl.innerText = "Live · audio unlocked";
        statusEl.className = "status";
        lastUpdateEl.innerText = "Last update: " + new Date().toLocaleTimeString();

        if (lastPrice !== null) {{
          const delta = price - lastPrice;

          if (delta >= PRICE_MOVEMENT_THRESHOLD) {{
            bullishCounter += 1;
            playTone(1040, 0.16, 0.16);
          }} else if (delta <= -PRICE_MOVEMENT_THRESHOLD) {{
            bullishCounter = 0;
            playTone(330, 0.22, 0.18);
          }} else {{
            bullishCounter = 0;
          }}

          if (bullishCounter >= 3) {{
            playCanon();
            bullishCounter = 0;
          }}
        }}

        lastPrice = price;
        updateMetrics(price);
        drawChart();

      }} catch (e) {{
        statusEl.innerHTML = "<span class='error'>Data error:</span> " + e.message;
      }}
    }}

    function start() {{
      ensureAudio();

      running = true;
      startTime = Date.now();

      if (timer) clearInterval(timer);

      statusEl.innerText = "Starting live feed…";
      tick();
      timer = setInterval(tick, FETCH_INTERVAL_MS);
    }}

    function stop() {{
      running = false;
      if (timer) clearInterval(timer);
      timer = null;
      statusEl.innerText = "Stopped.";
    }}

    document.getElementById("startBtn").addEventListener("click", start);
    document.getElementById("stopBtn").addEventListener("click", stop);
    document.getElementById("upTest").addEventListener("click", () => playTone(1040, 0.16, 0.16));
    document.getElementById("downTest").addEventListener("click", () => playTone(330, 0.22, 0.18));
    document.getElementById("canonTest").addEventListener("click", playCanon);

    window.addEventListener("resize", drawChart);

    resizeCanvas();
    drawChart();
  </script>
</body>
</html>
"""

components.html(html, height=900, scrolling=True)
