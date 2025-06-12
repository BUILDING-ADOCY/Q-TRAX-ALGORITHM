
import streamlit as st
import time
import os

LOG_PATH = "logs/traffic_results.log"

st.set_page_config(page_title="Q-TRAX Traffic Dashboard", layout="wide")
st.title("🚦 Q-TRAX Live Traffic Generator Dashboard")

placeholder = st.empty()

while True:
    if os.path.exists(LOG_PATH):
        # read last 20 lines
        with open(LOG_PATH, "r") as f:
            lines = f.readlines()[-20:]
        text = "".join(lines)
    else:
        text = "waiting for logs…"

    placeholder.code(text, language="plaintext")
    time.sleep(1)
