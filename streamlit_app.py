import json
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="SPOPS Live Signal Chart", page_icon="📈", layout="wide")

TOKEN_ADDRESS = "EkDGB5fbPXiRmDDjxKcC7dFjzvFZj2KT9t7oeyyPx4SX"
POOL_ADDRESS = "8LTRgxZ2KWDc2sDGuYAe5VtDgguAzteSeQUJisLQ5BVA"

html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<style>
body {{ margin:0; font-family:Helvetica,Arial,sans-serif; background:#fff; color:#111; }}
.wrap {{ max-width:1250px; margin:0 auto; padding:24px; }}
.top {{ display:flex; justify-content:space-between; gap:20px; border-bottom:1px solid #e6e8ec; padding-bottom:16px; margin-bottom:16px; }}
h1 {{ margin:0; font-size:32px; letter-spacing:-.04em; }}
.sub {{ color:#667085; font-size:13px; margin-top:6px; }}
.priceBox {{ text-align:right; }}
.label {{ color:#667085; font-size:12px; letter-spacing:.08em; text-transform:uppercase; }}
#price {{ font-size:36px; font-weight:800; letter-spacing:-.05em; }}
#status {{ color:#667085; font-size:12px; margin-top:4px; }}
button {{ border:1px solid #d0d5dd; background:#fff; border-radius:9px; padding:10px 14px; margin:4px; cursor:pointer; font-family:Helvetica,Arial,sans-serif; }}
button.primary {{ background:#0033A0; color:white; border-color:#0033A0; font-weight:800; }}
button.gold {{ background:#fff8db; color:#8A6A00; border-color:#e6c65c; font-weight:700; }}
.cards {{ display:grid; grid-template-columns:repeat(7,minmax(110px,1fr)); gap:8px; margin:14px 0; }}
.card {{ background:#f5f7fa; border:1px solid #e4e7ec; border-radius:14px; padding:11px 13px; }}
.cardName {{ color:#667085; font-size:11px; letter-spacing:.08em; text-transform:uppercase; }}
.cardValue {{ font-size:18px; font-weight:800; margin-top:5px; }}
.positive {{ color:#087443; }} .negative {{ color:#b42318; }} .neutral {{ color:#667085; }}
.shell {{ border:1px solid #e4e7ec; border-radius:17px; padding:18px; box-shadow:0 10px 30px rgba(16,24,40,.06); }}
canvas {{ width:100%; height:540px; display:block; }}
.footer {{ display:flex; justify-content:space-between; flex-wrap:wrap; color:#667085; font-size:12px; margin-top:12px; }}
.error {{ color:#b42318; font-weight:800; }} .ok {{ color:#087443; font-weight:800; }}
@media(max-width:900px){{ .top{{flex-direction:column}} .priceBox{{text-align:left}} .cards{{grid-template-columns:repeat(2,1fr)}} canvas{{height:420px}} }}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div>
      <h1>SPOPS Live Signal Chart</h1>
      <div class="sub">Jupiter Quote live price · GeckoTerminal 1-year history · browser audio signals</div>
    </div>
    <div class="priceBox">
      <div class="label">Current Jupiter Quote Price</div>
      <div id="price">$0.00000000</div>
      <div id="status">Click Start to unlock audio.</div>
    </div>
  </div>

  <div>
    <button id="startBtn" class="primary">Start Live Chart + Unlock Audio</button>
    <button id="stopBtn">Stop</button>
    <button id="historyBtn" class="gold">Load 1 Year History</button>
    <button id="liveViewBtn">Live View</button>
    <button id="historyViewBtn">History View</button>
    <button id="upTest">Test Up</button>
    <button id="downTest">Test Down</button>
    <button id="boomTest">Test Signal Boom</button>
  </div>

  <div class="cards">
    <div class="card"><div class="cardName">Minute</div><div id="m1" class="cardValue neutral">—</div></div>
    <div class="card"><div class="cardName">Hour</div><div id="h1" class="cardValue neutral">—</div></div>
    <div class="card"><div class="cardName">Day</div><div id="d1" class="cardValue neutral">—</div></div>
    <div class="card"><div class="cardName">Week</div><div id="w1" class="cardValue neutral">—</div></div>
    <div class="card"><div class="cardName">Month</div><div id="mo1" class="cardValue neutral">—</div></div>
    <div class="card"><div class="cardName">Year</div><div id="y1" class="cardValue neutral">—</div></div>
    <div class="card"><div class="cardName">All Time</div><div id="all" class="cardValue neutral">—</div></div>
  </div>

  <div class="shell"><canvas id="chart"></canvas></div>
  <div class="footer"><div id="modeLabel">Mode: Live chart</div><div id="lastUpdate">Waiting for data…</div></div>
</div>

<script>
const TOKEN_ADDRESS = {json.dumps(TOKEN_ADDRESS)};
const POOL_ADDRESS = {json.dumps(POOL_ADDRESS)};

const USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";
const ONE_SPOPS_AMOUNT = "100000000"; // 1 SPOPS with 8 decimals

const JUPITER_QUOTE_URL =
  "https://quote-api.jup.ag/v6/quote?inputMint=" +
  TOKEN_ADDRESS +
  "&outputMint=" +
  USDC_MINT +
  "&amount=" +
  ONE_SPOPS_AMOUNT +
  "&slippageBps=50";

const HISTORY_URL = "https://api.geckoterminal.com/api/v2/networks/solana/pools/" + POOL_ADDRESS + "/ohlcv/day?aggregate=1&limit=365";
const FETCH_INTERVAL_MS = 1000;
const PRICE_MOVEMENT_THRESHOLD = 1e-8;

let running=false, timer=null, audioCtx=null, chartMode="live";
let prices=[], times=[], historicalPoints=[];
let startTime=null, lastPrice=null, bullishCounter=0;

const priceEl=document.getElementById("price");
const statusEl=document.getElementById("status");
const lastUpdateEl=document.getElementById("lastUpdate");
const modeLabelEl=document.getElementById("modeLabel");
const canvas=document.getElementById("chart");
const ctx=canvas.getContext("2d");

function ensureAudio(){
  if(!audioCtx){ audioCtx=new (window.AudioContext || window.webkitAudioContext)(); }
  if(audioCtx.state==="suspended"){ audioCtx.resume(); }
}
function playTone(freq,duration=0.12,gain=0.65){
  ensureAudio();
  const osc=audioCtx.createOscillator();
  const amp=audioCtx.createGain();
  osc.type="sine"; osc.frequency.value=freq;
  const now=audioCtx.currentTime;
  amp.gain.setValueAtTime(0.0001,now);
  amp.gain.exponentialRampToValueAtTime(gain,now+0.015);
  amp.gain.exponentialRampToValueAtTime(0.0001,now+duration);
  osc.connect(amp); amp.connect(audioCtx.destination);
  osc.start(now); osc.stop(now+duration+0.02);
}
function playBoom(){
  ensureAudio();
  const now=audioCtx.currentTime;
  const o1=audioCtx.createOscillator(), o2=audioCtx.createOscillator(), amp=audioCtx.createGain();
  o1.type="sine"; o2.type="triangle"; o1.frequency.value=78; o2.frequency.value=43;
  amp.gain.setValueAtTime(0.0001,now);
  amp.gain.exponentialRampToValueAtTime(0.8,now+0.025);
  amp.gain.exponentialRampToValueAtTime(0.0001,now+0.55);
  o1.connect(amp); o2.connect(amp); amp.connect(audioCtx.destination);
  o1.start(now); o2.start(now); o1.stop(now+0.58); o2.stop(now+0.58);
}
function formatPrice(p){ return Number.isFinite(p) ? "$"+p.toFixed(8) : "$0.00000000"; }
function pct(current,base){ return (!base || base===0) ? 0 : ((current-base)/base)*100; }
function metricClass(v){ return v>0 ? "positive" : v<0 ? "negative" : "neutral"; }
function setMetric(id,value){
  const el=document.getElementById(id);
  el.innerText=(value>=0?"+":"")+value.toFixed(2)+"%";
  el.className="cardValue "+metricClass(value);
}
function baselineFor(seconds){
  if(prices.length===0) return null;
  if(seconds===null) return prices[0];
  const current=times[times.length-1], threshold=current-seconds;
  for(let i=0;i<times.length;i++){ if(times[i]>=threshold) return prices[i]; }
  return prices[0];
}
function updateMetrics(price){
  setMetric("m1",pct(price,baselineFor(60)));
  setMetric("h1",pct(price,baselineFor(3600)));
  setMetric("d1",pct(price,baselineFor(86400)));
  setMetric("w1",pct(price,baselineFor(604800)));
  setMetric("mo1",pct(price,baselineFor(2592000)));
  setMetric("y1",pct(price,baselineFor(31536000)));
  setMetric("all",pct(price,baselineFor(null)));
}

async function fetchJupiterPrice(){
  const res = await fetch(JUPITER_QUOTE_URL, { headers: { "Accept": "application/json" } });
  if (!res.ok) throw new Error("Jupiter quote returned " + res.status);

  const data = await res.json();
  if (!data.outAmount) throw new Error("Jupiter returned no quote.");

  const usdcReceived = parseFloat(data.outAmount) / 1000000; // USDC has 6 decimals
  return usdcReceived; // quoted exactly 1 SPOPS
}

async function fetchHistory(){
  if(!POOL_ADDRESS || POOL_ADDRESS.includes("PASTE_")) throw new Error("Add your GeckoTerminal pool address in streamlit_app.py first.");
  const res=await fetch(HISTORY_URL,{headers:{"Accept":"application/json"}});
  if(!res.ok) throw new Error("GeckoTerminal returned "+res.status);
  const data=await res.json();
  const list=data?.data?.attributes?.ohlcv_list;
  if(!Array.isArray(list) || list.length===0) throw new Error("No historical candles returned.");
  historicalPoints=list.map(x=>({t:new Date(x[0]*1000),close:+x[4]})).filter(x=>Number.isFinite(x.close)).reverse();
  if(historicalPoints.length>1){
    const first=historicalPoints[0].close, last=historicalPoints[historicalPoints.length-1].close;
    setMetric("y1",pct(last,first)); setMetric("all",pct(last,first));
  }
  chartMode="history"; modeLabelEl.innerText="Mode: 1-year historical chart"; drawChart();
}
function resizeCanvas(){
  const ratio=window.devicePixelRatio || 1, rect=canvas.getBoundingClientRect();
  canvas.width=Math.floor(rect.width*ratio); canvas.height=Math.floor(rect.height*ratio);
  ctx.setTransform(ratio,0,0,ratio,0,0);
}
function drawEmpty(msg){
  resizeCanvas(); const w=canvas.clientWidth,h=canvas.clientHeight;
  ctx.clearRect(0,0,w,h); ctx.fillStyle="#fff"; ctx.fillRect(0,0,w,h);
  ctx.fillStyle="#667085"; ctx.font="14px Helvetica, Arial"; ctx.fillText(msg,70,60);
}
function drawGrid(w,h,padL,padR,padT,padB,minP,maxP){
  const plotH=h-padT-padB;
  ctx.strokeStyle="#d9dde3"; ctx.lineWidth=1; ctx.setLineDash([4,5]);
  for(let i=0;i<=5;i++){ const y=padT+(plotH/5)*i; ctx.beginPath(); ctx.moveTo(padL,y); ctx.lineTo(w-padR,y); ctx.stroke(); }
  ctx.setLineDash([]); ctx.fillStyle="#667085"; ctx.font="11px Helvetica, Arial"; ctx.textAlign="right";
  for(let i=0;i<=5;i++){ const y=padT+(plotH/5)*i; const val=maxP-((maxP-minP)/5)*i; ctx.fillText("$"+val.toFixed(8),padL-10,y+4); }
}
function drawLiveChart(){
  resizeCanvas(); const w=canvas.clientWidth,h=canvas.clientHeight,padL=76,padR=30,padT=34,padB=54;
  ctx.clearRect(0,0,w,h); ctx.fillStyle="#fff"; ctx.fillRect(0,0,w,h);
  if(prices.length<1){ drawEmpty("Waiting for live Jupiter quote data…"); return; }
  const current=times[times.length-1], windowStart=Math.max(0,current-300);
  const pts=[]; for(let i=0;i<prices.length;i++){ if(times[i]>=windowStart) pts.push({t:times[i],p:prices[i]}); }
  let minP=Math.min(...pts.map(x=>x.p)), maxP=Math.max(...pts.map(x=>x.p));
  if(minP===maxP){ minP*=0.995; maxP*=1.005; } else { const r=maxP-minP; minP-=r*.07; maxP+=r*.07; }
  const plotW=w-padL-padR, plotH=h-padT-padB;
  const xScale=t=>padL+((t-windowStart)/Math.max(1,current-windowStart))*plotW;
  const yScale=p=>padT+(1-(p-minP)/(maxP-minP))*plotH;
  drawGrid(w,h,padL,padR,padT,padB,minP,maxP);
  if(pts.length>1){
    ctx.strokeStyle="#0033A0"; ctx.lineWidth=2.4; ctx.beginPath();
    pts.forEach((pt,i)=>{ const x=xScale(pt.t), y=yScale(pt.p); if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y); });
    ctx.stroke();
    const last=pts[pts.length-1]; ctx.fillStyle="#0033A0"; ctx.beginPath(); ctx.arc(xScale(last.t),yScale(last.p),4,0,Math.PI*2); ctx.fill();
  }
  ctx.fillStyle="#111"; ctx.font="bold 16px Helvetica, Arial"; ctx.textAlign="left";
  ctx.fillText("Live Jupiter Quote: "+formatPrice(prices[prices.length-1]),padL,padT-10);
  ctx.fillStyle="#667085"; ctx.font="12px Helvetica, Arial"; ctx.textAlign="center"; ctx.fillText("Live view: last 5 minutes",padL+plotW/2,h-18);
}
function drawHistoryChart(){
  resizeCanvas(); const w=canvas.clientWidth,h=canvas.clientHeight,padL=76,padR=30,padT=34,padB=54;
  ctx.clearRect(0,0,w,h); ctx.fillStyle="#fff"; ctx.fillRect(0,0,w,h);
  if(historicalPoints.length<2){ drawEmpty("Click Load 1 Year History after adding the GeckoTerminal pool address."); return; }
  const closes=historicalPoints.map(x=>x.close); let minP=Math.min(...closes), maxP=Math.max(...closes);
  if(minP===maxP){ minP*=0.995; maxP*=1.005; } else { const r=maxP-minP; minP-=r*.07; maxP+=r*.07; }
  const plotW=w-padL-padR, plotH=h-padT-padB;
  const xScale=i=>padL+(i/(historicalPoints.length-1))*plotW;
  const yScale=p=>padT+(1-(p-minP)/(maxP-minP))*plotH;
  drawGrid(w,h,padL,padR,padT,padB,minP,maxP);
  ctx.strokeStyle="#0033A0"; ctx.lineWidth=2.4; ctx.beginPath();
  historicalPoints.forEach((pt,i)=>{ const x=xScale(i), y=yScale(pt.close); if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y); });
  ctx.stroke();
  const first=historicalPoints[0], last=historicalPoints[historicalPoints.length-1];
  ctx.fillStyle="#111"; ctx.font="bold 16px Helvetica, Arial"; ctx.textAlign="left";
  ctx.fillText("1 Year History: "+formatPrice(first.close)+" → "+formatPrice(last.close),padL,padT-10);
  ctx.fillStyle="#667085"; ctx.font="12px Helvetica, Arial"; ctx.textAlign="center";
  ctx.fillText("GeckoTerminal daily OHLCV",padL+plotW/2,h-18);
}
function drawChart(){ chartMode==="history" ? drawHistoryChart() : drawLiveChart(); }
async function tick(){
  if(!running) return;
  try{
    const price=await fetchJupiterPrice();
    const nowSec=(Date.now()-startTime)/1000;
    prices.push(price); times.push(nowSec);
    priceEl.innerText=formatPrice(price);
    statusEl.innerText="Live · Jupiter Quote source · audio unlocked";
    lastUpdateEl.innerText="Last live update: "+new Date().toLocaleTimeString();
    if(lastPrice!==null){
      const delta=price-lastPrice;
      if(delta>=PRICE_MOVEMENT_THRESHOLD){ bullishCounter+=1; playTone(1040,0.12,0.65); }
      else if(delta<=-PRICE_MOVEMENT_THRESHOLD){ bullishCounter=0; playTone(330,0.16,0.75); }
      else { bullishCounter=0; }
      if(bullishCounter>=3){ playBoom(); bullishCounter=0; }
    }
    lastPrice=price; updateMetrics(price); if(chartMode==="live") drawLiveChart();
  } catch(e){ statusEl.innerHTML="<span class='error'>Live quote error:</span> "+e.message; }
}
function start(){
  ensureAudio(); running=true; startTime=Date.now(); if(timer) clearInterval(timer);
  chartMode="live"; modeLabelEl.innerText="Mode: Live chart"; statusEl.innerText="Starting Jupiter quote feed…";
  tick(); timer=setInterval(tick,FETCH_INTERVAL_MS);
}
function stop(){ running=false; if(timer) clearInterval(timer); timer=null; statusEl.innerText="Stopped."; }
document.getElementById("startBtn").addEventListener("click",start);
document.getElementById("stopBtn").addEventListener("click",stop);
document.getElementById("historyBtn").addEventListener("click",async()=>{ try{ statusEl.innerText="Loading 1-year history…"; await fetchHistory(); statusEl.innerHTML="<span class='ok'>History loaded.</span>"; lastUpdateEl.innerText="History loaded: "+new Date().toLocaleTimeString(); } catch(e){ statusEl.innerHTML="<span class='error'>History error:</span> "+e.message; } });
document.getElementById("liveViewBtn").addEventListener("click",()=>{ chartMode="live"; modeLabelEl.innerText="Mode: Live chart"; drawLiveChart(); });
document.getElementById("historyViewBtn").addEventListener("click",()=>{ chartMode="history"; modeLabelEl.innerText="Mode: 1-year historical chart"; drawHistoryChart(); });
document.getElementById("upTest").addEventListener("click",()=>playTone(1040,0.12,0.65));
document.getElementById("downTest").addEventListener("click",()=>playTone(330,0.16,0.75));
document.getElementById("boomTest").addEventListener("click",playBoom);
window.addEventListener("resize",drawChart);
resizeCanvas(); drawEmpty("Click Start Live Chart + Unlock Audio. Then click Load 1 Year History if pool address is added.");
</script>
</body>
</html>
"""
components.html(html, height=920, scrolling=True)

