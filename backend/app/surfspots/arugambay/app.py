import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import datetime
import os

# CONFIGURATION
JSON_PATH = "arugambay_forecast.json"
# If you have a GROQ API Key, put it here, otherwise set to None
# Get one free at https://console.groq.com/keys
GROQ_API_KEY = "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"  # <--- REPLACE THIS or set to os.environ.get("GROQ_API_KEY")

st.set_page_config(page_title="Arugam Bay Surf AI", page_icon="🌊", layout="wide")

# =======================================================
# 1. LOAD DATA
# =======================================================
@st.cache_data(ttl=3600) # Cache for 1 hour
def load_forecast():
    if not os.path.exists(JSON_PATH):
        return None
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data)

df = load_forecast()

# =======================================================
# 2. SIDEBAR (The Science Pitch)
# =======================================================
with st.sidebar:
    st.title("🌊 Ceylon Surfers")
    st.markdown("### Hybrid Forecasting System")
    st.info(
        """
        **Architecture:**
        1. **ConvLSTM (Research):** Validated spatiotemporal wave patterns (2020-2024).
        2. **ECMWF (Input):** Live deep-water physics boundary conditions.
        3. **SWAN (Physics):** Simulates nearshore refraction & shoaling.
        """
    )
    st.write("---")
    st.write(f"**Status:** {'✅ Online' if df is not None else '❌ Offline'}")
    if df is not None:
        last_update = df['time'].iloc[0]
        st.caption(f"Last Prediction: {last_update}")

# =======================================================
# 3. MAIN DASHBOARD
# =======================================================
st.title("Arugam Bay Surf Forecast")

if df is None:
    st.error("⚠️ Forecast data not found. Please run the pipeline script first.")
    st.stop()

# --- A. METRICS ROW ---
# Get the "Current" hour (or nearest future hour)
now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
current_row = df[df['time'] >= now].iloc[0] if not df[df['time'] >= now].empty else df.iloc[-1]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Surf Height", f"{current_row['surf_ft']:.1f} ft", f"{current_row['quality']}")
with col2:
    st.metric("Swell Period", f"{current_row['tp']:.1f} s", f"{current_row['deep_hs']:.1f}m Offshore")
with col3:
    st.metric("Direction", f"{current_row['dir']:.0f}°", "Local Refraction")
with col4:
    color = "green" if current_row['quality'] in ['GOOD', 'EPIC'] else "orange"
    st.markdown(f"### Status: :{color}[{current_row['quality']}]")

st.divider()

# --- B. CHARTS ---
col_chart, col_data = st.columns([2, 1])

with col_chart:
    st.subheader("24-Hour Forecast Trend")
    # Convert time to datetime for plotting
    df['time'] = pd.to_datetime(df['time'])
    
    fig = px.line(df, x='time', y='surf_ft', markers=True, title="Predicted Surf Face Height (ft)")
    fig.add_hrect(y0=0, y1=2, line_width=0, fillcolor="red", opacity=0.1, annotation_text="Flat")
    fig.add_hrect(y0=2, y1=5, line_width=0, fillcolor="yellow", opacity=0.1, annotation_text="Fun")
    fig.add_hrect(y0=5, y1=10, line_width=0, fillcolor="green", opacity=0.1, annotation_text="Pumping")
    st.plotly_chart(fig, use_container_width=True)

with col_data:
    st.subheader("Detailed Data")
    display_df = df[['time', 'surf_ft', 'quality', 'dir', 'tp']].copy()
    display_df['time'] = display_df['time'].dt.strftime('%H:%M')
    st.dataframe(display_df, hide_index=True, height=350)

# =======================================================
# 4. AI SURF GUIDE (The "Wow" Factor)
# =======================================================
st.divider()
st.subheader("🤖 AI Local Guide")
st.caption("Ask about the conditions, best time to surf, or board recommendations.")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Logic
if prompt := st.chat_input("Is it good for beginners today?"):
    # 1. User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. AI Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        if not GROQ_API_KEY or "gsk_" not in GROQ_API_KEY:
            response = "⚠️ Please configure a valid Groq API Key in app.py to enable the AI Chatbot."
            message_placeholder.markdown(response)
        else:
            try:
                from groq import Groq
                client = Groq(api_key=GROQ_API_KEY)
                
                # CONTEXT INJECTION (The "Simple RAG")
                # We feed the dataframe as a string context
                context_str = df.to_string()
                
                system_prompt = f"""
                You are a stoked, helpful local surf guide at Arugam Bay, Sri Lanka.
                Here is the forecast for the next 24 hours:
                {context_str}
                
                INTERPRETATION RULES:
                - < 2ft: Flat, stay home or longboard.
                - 2-4ft: Fun, good for beginners/intermediate.
                - 4-6ft: Good, pumping, main point is working.
                - > 6ft: Epic, experts only.
                
                Answer the user's question based ONLY on this data. Keep it short and surf-slangy.
                """
                
                completion = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=200
                )
                
                response = completion.choices[0].message.content
                message_placeholder.markdown(response)
                
            except Exception as e:
                response = f"Sorry, my radio is broken. Error: {e}"
                message_placeholder.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})