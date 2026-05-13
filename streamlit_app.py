import io
import math
import time
import wave
from datetime import datetime

import requests
import streamlit as st


# ============================================================
# SPOPS LIVE SIGNAL DASHBOARD
# Server-side price fetching: fixes browser "failed to fetch"
# ============================================================

st.set_page_config(
    page_title="SPOPS Live Signal Chart",
    page_icon="📈",
    layout="wide",
)

# ----------------------------
# EDIT THESE IF NEEDED
# ----------------------------

TOKEN_NAME = "SPOPS"
TOKEN_ADDRESS = "EkDGB5fbPXiRmDDjxKcC7dFjzvFZj2KT9t7oeyyPx4SX"

# SPOPS has 8 decimals, so 1 SPOPS = 100000000 raw units.
ONE_TOKEN_AMOUNT = 100000000

# USDC on Solana. USDC has 6 decimals.
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

# Add your GeckoTerminal Solana pool address here later for 1-year history.
# Live Jupiter quote works even if this is left as-is.
POOL_ADDRESS = "PASTE_GECKOTERMINAL_POOL_ADDRESS_HERE"

# How often the app checks the price.
# 1.0 = every 1 second.
FETCH_INTERVAL_SECONDS = 1.0

# Sound triggers when price changes at the 8th decimal.
PRICE_MOVEMENT_THRESHOLD = 0.00000001


# ----------------------------
# AUDIO HELPERS
# ----------------------------

def make_tone_wav(frequency: float, duration: float = 0.12, volume: float = 0.9) -> bytes:
    sample_rate = 44100
    frames = int(sample_rate * duration)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        for i in range(frames):
            t = i / sample_rate
            # Soft fade to avoid clicking.
            fade = min(1.0, i / 600, (frames - i) / 600)
            value = volume * fade * math.sin(2 * math.pi * frequency * t)
            wav.writeframes(int(value * 32767).to_bytes(2, byteorder="little", signed=True))

    return buffer.getvalue()


def make_boom_wav(duration: float = 0.55, volume: float = 1.0) -> bytes:
    sample_rate = 44100
    frames = int(sample_rate * duration)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        for i in range(frames):
            t = i / sample_rate
            decay = math.exp(-5 * t)
            wave_value = (
                0.7 * math.sin(2 * math.pi * 78 * t)
                + 0.5 * math.sin(2 * math.pi * 43 * t)
            )
            value = volume * decay * wave_value
            value = max(-1.0, min(1.0, value))
            wav.writeframes(int(value * 32767).to_bytes(2, byteorder="little", signed=True))

    return buffer.getvalue()


UP_SOUND = make_tone_wav(1040, duration=0.12, volume=0.95)
DOWN_SOUND = make_tone_wav(330, duration=0.16, volume=1.0)
BOOM_SOUND = make_boom_wav(duration=0.55, volume=1.0)


# ----------------------------
# DATA FETCHING — SERVER SIDE
# ----------------------------

def fetch_jupiter_quote_price() -> float:
    """
    Uses Jupiter Quote API server-side.
    This avoids browser CORS / failed-to-fetch errors.
    """

    url = "https://quote-api.jup.ag/v6/quote"

    params = {
        "inputMint": TOKEN_ADDRESS,
        "outputMint": USDC_MINT,
        "amount": str(ONE_TOKEN_AMOUNT),
        "slippageBps": "50",
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()

    data = response.json()

    if "outAmount" not in data:
        raise RuntimeError(f"Jupiter returned no outAmount. Response: {data}")

    # USDC has 6 decimals.
    usdc_received = float(data["outAmount"]) / 1_000_000

    # We quoted exactly 1 SPOPS.
    return usdc_received


def fetch_gecko_history():
    """
    Uses GeckoTerminal OHLCV daily candles for 1-year history.
    Requires POOL_ADDRESS to be filled in.
    """

    if not POOL_ADDRESS or "PASTE_" in POOL_ADDRESS:
        raise RuntimeError("Add your GeckoTerminal pool address in POOL_ADDRESS first.")

    url = (
        f"https://api.geckoterminal.com/api/v2/networks/solana/pools/"
        f"{POOL_ADDRESS}/ohlcv/day"
    )

    params = {
        "aggregate": "1",
        "limit": "365",
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()

    data = response.json()
    candles = data.get("data", {}).get("attributes", {}).get("ohlcv_list", [])

    if not candles:
        raise RuntimeError("No historical candles returned from GeckoTerminal.")

    # GeckoTerminal format:
    # [timestamp, open, high, low, close, volume]
    rows = []
    for c in reversed(candles):
        rows.append(
            {
                "date": datetime.fromtimestamp(c[0]).strftime("%Y-%m-%d"),
                "close": float(c[4]),
            }
        )

    return rows


# ----------------------------
# SESSION STATE
# ----------------------------

if "running" not in st.session_state:
    st.session_state.running = False

if "prices" not in st.session_state:
    st.session_state.prices = []

if "times" not in st.session_state:
    st.session_state.times = []

if "last_price" not in st.session_state:
    st.session_state.last_price = None

if "last_sound" not in st.session_state:
    st.session_state.last_sound = None

if "bullish_counter" not in st.session_state:
    st.session_state.bullish_counter = 0

if "history_rows" not in st.session_state:
    st.session_state.history_rows = []


# ----------------------------
# UI
# ----------------------------

st.title("SPOPS Live Signal Chart")
st.caption("Live price uses Jupiter Quote API server-side. This avoids browser 'failed to fetch' errors.")

top_left, top_right = st.columns([2, 1])

with top_left:
    st.write("**Source setup:**")
    st.write("Live price = Jupiter Quote API")
    st.write("1-year history = GeckoTerminal OHLCV after pool address is added")

with top_right:
    current_price = st.session_state.prices[-1] if st.session_state.prices else None
    st.metric("Current Jupiter Quote Price", f"${current_price:.8f}" if current_price else "$0.00000000")


# Controls
c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    if st.button("Start Live", type="primary"):
        st.session_state.running = True

with c2:
    if st.button("Stop"):
        st.session_state.running = False

with c3:
    if st.button("Test Up"):
        st.audio(UP_SOUND, format="audio/wav", autoplay=True)

with c4:
    if st.button("Test Down"):
        st.audio(DOWN_SOUND, format="audio/wav", autoplay=True)

with c5:
    if st.button("Test Boom"):
        st.audio(BOOM_SOUND, format="audio/wav", autoplay=True)

with c6:
    if st.button("Clear Chart"):
        st.session_state.prices = []
        st.session_state.times = []
        st.session_state.last_price = None
        st.session_state.last_sound = None
        st.session_state.bullish_counter = 0


# ----------------------------
# LIVE FETCH
# ----------------------------

if st.session_state.running:
    try:
        price = fetch_jupiter_quote_price()
        now_label = datetime.now().strftime("%H:%M:%S")

        st.session_state.prices.append(price)
        st.session_state.times.append(now_label)

        # Keep chart reasonably light.
        if len(st.session_state.prices) > 600:
            st.session_state.prices = st.session_state.prices[-600:]
            st.session_state.times = st.session_state.times[-600:]

        previous = st.session_state.last_price

        if previous is not None:
            delta = price - previous

            if delta >= PRICE_MOVEMENT_THRESHOLD:
                st.session_state.last_sound = "up"
                st.session_state.bullish_counter += 1

            elif delta <= -PRICE_MOVEMENT_THRESHOLD:
                st.session_state.last_sound = "down"
                st.session_state.bullish_counter = 0

            else:
                st.session_state.last_sound = None
                st.session_state.bullish_counter = 0

            if st.session_state.bullish_counter >= 3:
                st.session_state.last_sound = "boom"
                st.session_state.bullish_counter = 0

        st.session_state.last_price = price

    except Exception as e:
        st.error(f"Live price error: {e}")


# Play sound after fetch.
if st.session_state.last_sound == "up":
    st.audio(UP_SOUND, format="audio/wav", autoplay=True)
elif st.session_state.last_sound == "down":
    st.audio(DOWN_SOUND, format="audio/wav", autoplay=True)
elif st.session_state.last_sound == "boom":
    st.audio(BOOM_SOUND, format="audio/wav", autoplay=True)

# Reset so it does not replay endlessly.
st.session_state.last_sound = None


# ----------------------------
# LIVE CHART
# ----------------------------

st.subheader("Live Chart")

if st.session_state.prices:
    chart_data = {
        "time": st.session_state.times,
        "price": st.session_state.prices,
    }
    st.line_chart(chart_data, x="time", y="price", height=420)

    if len(st.session_state.prices) >= 2:
        change = st.session_state.prices[-1] - st.session_state.prices[-2]
        st.write(f"Last movement: {change:+.8f}")

else:
    st.info("Click Start Live to begin.")


# ----------------------------
# HISTORY
# ----------------------------

st.subheader("1-Year Historical Chart")

if st.button("Load 1 Year History"):
    try:
        st.session_state.history_rows = fetch_gecko_history()
        st.success("1-year history loaded.")
    except Exception as e:
        st.error(f"History error: {e}")

if st.session_state.history_rows:
    st.line_chart(st.session_state.history_rows, x="date", y="close", height=420)
else:
    st.info("To use history, add your GeckoTerminal pool address in POOL_ADDRESS first.")


# ----------------------------
# AUTO REFRESH
# ----------------------------

if st.session_state.running:
    time.sleep(FETCH_INTERVAL_SECONDS)
    st.rerun()
