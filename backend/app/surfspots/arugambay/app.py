import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import datetime
import os
from dotenv import load_dotenv

JSON_PATH = "arugambay_forecast.json" 
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="Arugam Bay Surf AI", page_icon="🌊", layout="wide")

# =======================================================
# 1. LOAD DATA
# =======================================================
@st.cache_data(ttl=3600) 
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
        # Ensure time is datetime
        df['time'] = pd.to_datetime(df['time'])
        last_update = df['time'].iloc[0].strftime('%Y-%m-%d %H:%M')
        st.caption(f"Forecast Start: {last_update}")

# =======================================================
# 3. MAIN DASHBOARD
# =======================================================
st.title("Arugam Bay Surf Forecast (7-Day)")

if df is None:
    st.error("⚠️ Forecast data not found. Please run the pipeline script first.")
    st.stop()

# --- A. METRICS ROW (Current Status) ---
now = datetime.utcnow()
# Find the row closest to "Now" (or the first row if "Now" is before the forecast)
current_row = df.iloc[0] 
for i, row in df.iterrows():
    if row['time'] >= now:
        current_row = row
        break

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Surf Height", f"{current_row['surf_ft']:.1f} ft", f"{current_row['quality']}")
with col2:
    st.metric("Swell Period", f"{current_row['tp']:.1f} s", f"{current_row['deep_hs']:.1f}m Offshore")
with col3:
    st.metric("Direction", f"{current_row['dir']:.0f}°", "Local Refraction")
with col4:
    # Dynamic Color for Status
    color = "green" if current_row['quality'] in ['GOOD', 'EPIC'] else "orange"
    if current_row['quality'] in ['FLAT', 'POOR']: color = "red"
    st.markdown(f"### Status: :{color}[{current_row['quality']}]")

st.divider()

# --- B. CHARTS ---
col_chart, col_data = st.columns([2, 1])

with col_chart:
    st.subheader("7-Day Forecast Trend")
    
    fig = px.line(df, x='time', y='surf_ft', markers=True, title="Predicted Surf Face Height (ft)")
    
    # Color Bands for readability
    fig.add_hrect(y0=0, y1=2, line_width=0, fillcolor="red", opacity=0.1, annotation_text="Flat")
    fig.add_hrect(y0=2, y1=4, line_width=0, fillcolor="yellow", opacity=0.1, annotation_text="Fun")
    fig.add_hrect(y0=4, y1=8, line_width=0, fillcolor="green", opacity=0.1, annotation_text="Good")
    fig.add_hrect(y0=8, y1=15, line_width=0, fillcolor="purple", opacity=0.1, annotation_text="Epic")
    
    # Fix X-Axis to handle 7 days clearly
    fig.update_xaxes(
        dtick="D1", # One tick per Day
        tickformat="%b %d" # e.g., "Nov 23"
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col_data:
    st.subheader("Detailed Schedule")
    display_df = df[['time', 'surf_ft', 'quality', 'dir', 'tp']].copy()
    # Format for display
    display_df['time'] = display_df['time'].dt.strftime('%a %H:%M') # "Mon 14:00"
    st.dataframe(display_df, hide_index=True, height=400)

# =======================================================
# 4. AI SURF GUIDE (Updated for 7 Days)
# =======================================================
st.divider()
st.subheader("🤖 AI Local Guide")
st.caption("Ask about the week ahead. Example: 'Which day looks best?'")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("When is the best session this week?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        if not GROQ_API_KEY or "gsk_" not in GROQ_API_KEY:
            response = "⚠️ Please configure a valid Groq API Key in app.py."
            message_placeholder.markdown(response)
        else:
            try:
                from groq import Groq
                client = Groq(api_key=GROQ_API_KEY)
                
                # OPTIMIZED CONTEXT: Send only essential columns to save tokens
                # We convert the 7-day dataframe to a string
                context_df = df[['time', 'surf_ft', 'quality', 'dir']].copy()
                context_df['time'] = context_df['time'].dt.strftime('%A %H:%M') # Day Name + Hour
                context_str = context_df.to_string(index=False)
                
                system_prompt = f"""
                You are a local surf guide at Arugam Bay.
                Here is the 7-DAY FORECAST (3-hour intervals):
                {context_str}
                
                INTERPRETATION RULES:
                - < 2ft: Flat.
                - 2-3.5ft: Fun/Small.
                - 3.5-6ft: Good/Pumping.
                - > 6ft: Epic/Heavy.
                
                User Question: "{prompt}"
                
                Task: Analyze the data rows above. Identify the SPECIFIC DAYS and TIMES that answer the question.
                Be concise. Use surfer slang.
                """
                
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5, # Lower temp for more factual data analysis
                    max_tokens=250
                )
                
                response = completion.choices[0].message.content
                message_placeholder.markdown(response)
                
            except Exception as e:
                response = f"System Error: {e}"
                message_placeholder.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})