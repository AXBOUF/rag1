import streamlit as st
import requests

# --- CONFIG ---
OLLAMA_BASE = "http://192.168.1.186:11434"
DEFAULT_MODEL = "qwen2.5:7b"  # Change to whatever model you have pulled

st.set_page_config(page_title="Local AI Chat", page_icon="🧠", layout="centered")

# --- STYLING ---
st.markdown("""
<style>
    body { font-family: 'Courier New', monospace; }
    .stChatMessage { border-radius: 12px; }
    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: model picker ---
with st.sidebar:
    st.title("⚙️ Settings")

    # Fetch available models from Ollama
    try:
        res = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
        model_names = [m["name"] for m in res.json().get("models", [])]
    except Exception:
        model_names = [DEFAULT_MODEL]
        st.warning("⚠️ Could not reach Ollama. Is it running?")

    model = st.selectbox("Model", model_names)
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
    if st.button("🗑️ Clear chat"):
        st.session_state.messages = []
        st.rerun()

# --- CHAT STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🧠 Local AI Chat")

# --- RENDER HISTORY ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- INPUT ---
if prompt := st.chat_input("Say something..."):

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call Ollama with full history
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{OLLAMA_BASE}/api/chat",
                    json={
                        "model": model,
                        "messages": st.session_state.messages,
                        "stream": False,
                        "options": {"temperature": temperature}
                    },
                    timeout=120
                )
                reply = response.json()["message"]["content"]
            except requests.exceptions.ConnectionError:
                reply = "❌ Cannot connect to Ollama. Make sure it's running with `ollama serve`."
            except Exception as e:
                reply = f"❌ Error: {e}"

        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})