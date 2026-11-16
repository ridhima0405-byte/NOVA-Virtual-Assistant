
import streamlit as st
from assistant import get_response, speak
from streamlit_mic_recorder import speech_to_text

st.set_page_config(
    page_title="NOVA Virtual Assistant",
    page_icon="🤖",
    layout="wide"
)

# Styling
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #101426, #1b2140);
    color: white;
}
h1 {
    color: #9b8cff;
    text-align: center;
}
.subtitle {
    text-align: center;
    color: #b8b9d0;
    font-size: 18px;
}
[data-testid="stChatMessage"] {
    background-color: rgba(255,255,255,0.07);
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 NOVA")
st.markdown(
    '<p class="subtitle">Your Personal AI Virtual Assistant</p>',
    unsafe_allow_html=True
)

st.sidebar.title("⚙️ Settings")
voice_enabled = st.sidebar.toggle("Enable voice response", value=True)

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.write("### Available Commands")
st.sidebar.write("""
- Hello
- What is the time?
- What is today's date?
- Open Google
- Open YouTube
- Search machine learning
- Calculate 25 * 5
""")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Welcome message
if not st.session_state.messages:
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Hello! I am NOVA. How can I help you today?"
    })

# Display conversation
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User input
col1, col2 = st.columns([4, 1])

with col1:
    user_input = st.chat_input("Ask NOVA anything...")

with col2:
    voice_input = speech_to_text(
        start_prompt="🎤 Speak",
        stop_prompt="⏹️ Stop",
        language="en",
        use_container_width=True,
        key="nova_voice"
    )

if voice_input:
    user_input = voice_input

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.write(user_input)

    answer = get_response(user_input)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    with st.chat_message("assistant"):
        st.write(answer)

    if voice_enabled:
        speak(answer)
