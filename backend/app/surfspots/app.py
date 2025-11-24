import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
st.set_page_config(page_title="Ceylon Surfers AI", page_icon="🌊", layout="wide")

SPOTS = {
    "Arugam Bay": {
        "path": "arugambay/arugambay_forecast.json",
        "type": "Point Break",
        "difficulty": "Intermediate to Expert",
        "best_wind": "West / South-West"
    },
    "Ahangama": {
        "path": "ahangama/ahangama_forecast.json",
        "type": "Reef Break",
        "difficulty": "Intermediate",
        "best_wind": "North / North-East"
    },
    "Mirissa": {
        "path": "mirissa/mirissa_forecast.json",
        "type": "Point/Reef",
        "difficulty": "All Levels",
        "best_wind": "North"
    },
    "Hikkaduwa": {
        "path": "hikkaduwa/hikkaduwa_forecast.json",
        "type": "Reef Break",
        "difficulty": "Advanced (Main Reef)",
        "best_wind": "North-East"
    }
}

with st.sidebar:
    st.title(" Ceylon Surfers")
    st.markdown("### Select Surf Spot")
    
    # PAGINATION: The Dropdown
    selected_spot_name = st.selectbox("Location", list(SPOTS.keys()))
    current_spot_config = SPOTS[selected_spot_name]
    
    st.divider()
    
    # SPOT INFO CARD
    st.subheader(" Spot Profile")
    st.write(f"**Type:** {current_spot_config['type']}")
    st.write(f"**Level:** {current_spot_config['difficulty']}")
    st.write(f"**Ideal Wind:** {current_spot_config['best_wind']}")
    
    st.divider()
    st.info(
        """
        **System Architecture:**
        1. **ConvLSTM:** Spatiotemporal validation.
        2. **ECMWF + Open-Meteo:** Boundary physics.
        3. **SWAN:** Nearshore refraction model.
        """
    )

@st.cache_data(ttl=3600) 
def load_forecast(json_path):
    # Handle relative paths safely
    if not os.path.exists(json_path):
        # Try to find it relative to current script if running from root
        if os.path.exists(os.path.join("surfspots", json_path)):
            json_path = os.path.join("surfspots", json_path)
        else:
            return None
            
    with open(json_path, 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data)

# Load data for the SELECTED spot
df = load_forecast(current_spot_config['path'])

st.title(f"{selected_spot_name} 7-Day Forecast")

if df is None:
    st.error(f" Data not found for {selected_spot_name}. Expected path: {current_spot_config['path']}")
    st.info("Tip: Ensure you have run the pipeline for this specific spot folder.")
    st.stop()

# Clean Data
df['time'] = pd.to_datetime(df['time'], unit='ms')

# FIX: Convert UTC to Sri Lanka Time (+5:30)
df['time'] = df['time'] + pd.Timedelta(hours=5, minutes=30)

# FIX: Patch initial zero direction artifact
if len(df) > 1 and df.iloc[0]['dir'] == 0:
    df.loc[0, 'dir'] = df.loc[1, 'dir']

# --- A. CURRENT CONDITIONS METRIC ---
now = datetime.utcnow() + pd.Timedelta(hours=5, minutes=30)
# Find row closest to "Now"
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
    st.metric("Direction", f"{current_row['dir']:.0f}°", "Local Wrap")
with col4:
    # Logic: Red if Flat or XL/Dangerous, Green if Good
    status_color = "green" 
    if current_row['quality'] in ["FLAT", "POOR", "XL / DANGEROUS"]:
        status_color = "red"
    elif current_row['quality'] == "FAIR":
        status_color = "orange"
    
    st.markdown(f"### Status: :{status_color}[{current_row['quality']}]")

st.divider()

# --- B. CHARTS & TABLES ---
col_chart, col_data = st.columns([2, 1])

with col_chart:
    st.subheader("Forecast Trend")
    
    fig = px.line(df, x='time', y='surf_ft', markers=True, title="Predicted Face Height (ft)")
    
    # Quality Bands
    fig.add_hrect(y0=0, y1=2, line_width=0, fillcolor="red", opacity=0.1, annotation_text="Flat")
    fig.add_hrect(y0=2, y1=4, line_width=0, fillcolor="yellow", opacity=0.1, annotation_text="Fun")
    fig.add_hrect(y0=4, y1=8, line_width=0, fillcolor="green", opacity=0.1, annotation_text="Good")
    fig.add_hrect(y0=8, y1=15, line_width=0, fillcolor="purple", opacity=0.1, annotation_text="Heavy")
    
    # X-Axis Formatting (Daily Ticks)
    fig.update_xaxes(dtick="D1", tickformat="%b %d")
    fig.update_layout(height=400)
    
    st.plotly_chart(fig, use_container_width=True)

with col_data:
    st.subheader("Detailed Schedule")
    display_df = df[['time', 'surf_ft', 'quality', 'dir']].copy()
    display_df['time'] = display_df['time'].dt.strftime('%a %H:%M')
    display_df.columns = ['Time', 'Height (ft)', 'Rating', 'Dir']
    st.dataframe(display_df, hide_index=True, height=400)


st.divider()
st.subheader(f" AI Guide: {selected_spot_name}")
st.caption(f"Ask about conditions at {selected_spot_name}. I know about skill levels and timing.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Is it good for beginners tomorrow?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        if not GROQ_API_KEY:
            response = " AI is offline. Please set GROQ_API_KEY in .env file."
            message_placeholder.markdown(response)
        else:
            try:
                from groq import Groq
                client = Groq(api_key=GROQ_API_KEY)
                
                # 1. PREPARE GLOBAL CONTEXT (All Spots)
                all_spots_info = []
                now_sl = datetime.utcnow() + pd.Timedelta(hours=5, minutes=30)
                
                for s_name, s_config in SPOTS.items():
                    try:
                        s_df = load_forecast(s_config['path'])
                        if s_df is not None:
                            s_df['time'] = pd.to_datetime(s_df['time'], unit='ms') + pd.Timedelta(hours=5, minutes=30)
                            # Get current condition
                            future = s_df[s_df['time'] >= now_sl]
                            if not future.empty:
                                curr = future.iloc[0]
                                all_spots_info.append(
                                    f"- {s_name}: {curr['surf_ft']:.1f}ft ({curr['quality']}) | {s_config['difficulty']} | {s_config['type']}"
                                )
                    except Exception:
                        continue
                
                global_context = "\n".join(all_spots_info)

                # 2. PREPARE LOCAL CONTEXT (Detailed for Selected Spot)
                context_df = df[['time', 'surf_ft', 'quality']].copy()
                context_df['hour'] = context_df['time'].dt.hour
                context_df['is_night'] = context_df['hour'].apply(lambda h: "YES" if (h >= 18 or h <= 5) else "NO")
                context_df['time'] = context_df['time'].dt.strftime('%A %H:%M')
                local_context_str = context_df.to_string(index=False)
                
                # 3. SYSTEM PROMPT (Global Awareness)
                system_prompt = f"""
                You are an expert surf guide for Sri Lanka. You have real-time data for multiple spots.
                
                CURRENT CONDITIONS (ALL SPOTS):
                {global_context}
                
                DETAILED FORECAST FOR SELECTED SPOT ({selected_spot_name}):
                {local_context_str}
                
                STRICT RULES:
                1. **GLOBAL AWARENESS:** If the user asks "Where should I surf?", compare spots based on their skill level and current conditions.
                2. **BEGINNERS:** Recommend spots with 2-4ft waves and "Beginner" or "All Levels" difficulty. Warn against "Advanced" spots if they are big.
                3. **NIGHT TIME:** No surfing 6PM-6AM.
                4. **SAFETY:** Always mention reef/rock hazards for Reef breaks.
                
                User Question: "{prompt}"
                
                Answer concisely. If recommending other spots, mention why (e.g., "Mirissa is better for learning today").
                """
                
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3, # Low temp for strict adherence to data
                    max_tokens=250
                )
                
                response = completion.choices[0].message.content
                message_placeholder.markdown(response)
                
            except Exception as e:
                response = f"Sorry, radio interference. Error: {e}"
                message_placeholder.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})