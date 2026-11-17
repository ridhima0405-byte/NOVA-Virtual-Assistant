
import streamlit as st

from assistant import (
    get_response,
    speak,
    load_tasks,
    manage_tasks,
    get_all_reminders,
    get_due_reminders,
    manage_reminders
)

from streamlit_mic_recorder import speech_to_text
from datetime import datetime


# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="NOVA | Virtual Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------------- CUSTOM DESIGN ----------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 10% 10%, #252052 0%, transparent 30%),
        radial-gradient(circle at 90% 80%, #172c50 0%, transparent 30%),
        #0b1020;
    color: #f4f4ff;
}

.block-container {
    max-width: 1100px;
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

[data-testid="stSidebar"] {
    background: #10172b;
    border-right: 1px solid #28304b;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #c4b5fd;
}

.nova-logo {
    font-size: 42px;
    font-weight: 800;
    letter-spacing: 3px;
    text-align: center;
    background: linear-gradient(90deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.nova-subtitle {
    color: #a5b4d4;
    text-align: center;
    font-size: 14px;
    margin-bottom: 20px;
}

.hero {
    background: linear-gradient(120deg, #1b2140, #25204b);
    border: 1px solid #484078;
    border-radius: 20px;
    padding: 28px;
    margin: 15px 0 25px 0;
    text-align: center;
}

.hero h2 {
    color: white;
    font-size: 27px;
}

.hero p {
    color: #c0c8e5;
    font-size: 14px;
}

.feature-card {
    background: rgba(255,255,255,0.045);
    border: 1px solid #303957;
    border-radius: 15px;
    padding: 17px;
    text-align: center;
    min-height: 105px;
}

.feature-icon {
    font-size: 25px;
}

.feature-title {
    font-size: 13px;
    font-weight: 600;
    color: #e4e4ff;
    margin-top: 7px;
}

[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.045);
    border: 1px solid #303957;
    border-radius: 16px;
    padding: 14px;
    margin-bottom: 12px;
}

[data-testid="stChatInput"] {
    border: 1px solid #6256a5;
    border-radius: 15px;
    background: #151d35;
}

.stButton > button {
    border-radius: 12px;
    border: 1px solid #51458c;
    background: #242348;
    color: white;
    font-weight: 600;
}

.stButton > button:hover {
    background: #51458c;
    border-color: #a78bfa;
    color: white;
}

.status {
    text-align: center;
    color: #86efac;
    font-size: 12px;
    margin-top: 5px;
}

hr {
    border-color: #303957;
}
</style>
""", unsafe_allow_html=True)


# ---------------- SESSION STATE ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = False

if "last_voice_input" not in st.session_state:
    st.session_state.last_voice_input = ""

if "announced_reminders" not in st.session_state:
    st.session_state.announced_reminders = []


# ---------------- SIDEBAR ----------------

with st.sidebar:

    st.markdown("## 🤖 NOVA")
    st.caption("YOUR PERSONAL ASSISTANT")

    st.markdown("---")

    st.markdown("### ⚙️ Preferences")

    st.session_state.voice_enabled = st.toggle(
        "Enable voice response",
        value=st.session_state.voice_enabled
    )

    st.caption("Voice output depends on your device's speech engine.")

    st.markdown("---")

    st.markdown("### ✨ What I can do")

    commands = [
        ("👋", "Greetings", "Hello"),
        ("🕒", "Time and Date", "What is the time?"),
        ("🧮", "Calculator", "Calculate 25 * 5"),
        ("🌐", "Google Search", "Search machine learning"),
        ("▶️", "YouTube", "Open YouTube"),
        ("📚", "Knowledge Search", "Tell me about Python"),
        ("📝", "Task Manager", "Add task complete assignment"),
        ("📋", "View Tasks", "Show my tasks"),
        ("🔔", "Reminders", "Remind me to study at 7 PM")
    ]

    for icon, title, example in commands:
        st.markdown(f"**{icon} {title}**")
        st.caption(example)

    st.markdown("---")

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_voice_input = ""
        st.rerun()

    st.markdown("---")

    st.caption("NOVA v2.0")
    st.caption("Built with Python + Streamlit")


# ---------------- HEADER ----------------

st.markdown(
    '<div class="nova-logo">✦ NOVA</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="nova-subtitle">YOUR INTELLIGENT DIGITAL COMPANION</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="status">● SYSTEM READY | READY TO ASSIST</div>',
    unsafe_allow_html=True
)


# ---------------- TASK DASHBOARD ----------------

st.markdown("### 📝 My Tasks")

tasks = load_tasks()

total_tasks = len(tasks)
completed_tasks = sum(1 for task in tasks if task["completed"])
pending_tasks = total_tasks - completed_tasks

col1, col2, col3 = st.columns(3)

col1.metric("Total Tasks", total_tasks)
col2.metric("Completed", completed_tasks)
col3.metric("Pending", pending_tasks)

if total_tasks == 0:

    st.info(
        "You don't have any tasks yet. "
        "Try: Add task complete my assignment"
    )

else:

    for i, task in enumerate(tasks):

        col_task, col_complete, col_remove = st.columns([6, 1, 1])

        with col_task:

            if task["completed"]:
                st.markdown(f"~~{i + 1}. {task['task']}~~ ✅")
            else:
                st.markdown(f"**{i + 1}. {task['task']}** ⏳")

        with col_complete:

            if not task["completed"]:

                if st.button("✓", key=f"complete_task_{i}"):
                    manage_tasks(f"complete task {i + 1}")
                    st.rerun()

        with col_remove:

            if st.button("✕", key=f"remove_task_{i}"):
                manage_tasks(f"remove task {i + 1}")
                st.rerun()


# ---------------- REMINDER DASHBOARD ----------------

st.markdown("---")
st.markdown("### 🔔 My Reminders")

reminders = get_all_reminders()
due_reminders = get_due_reminders()

total_reminders = len(reminders)

completed_reminders = sum(
    1 for reminder in reminders if reminder["completed"]
)

pending_reminders = total_reminders - completed_reminders

col1, col2, col3 = st.columns(3)

col1.metric("Total Reminders", total_reminders)
col2.metric("Completed", completed_reminders)
col3.metric("Pending", pending_reminders)

if not reminders:

    st.info(
        "No reminders yet. "
        "Try: Remind me to study at 7 PM"
    )

else:

    for i, reminder in enumerate(reminders):

        try:
            reminder_time = datetime.fromisoformat(
                reminder["datetime"]
            )

            time_text = reminder_time.strftime(
                "%d %B %Y | %I:%M %p"
            )

        except (ValueError, KeyError):
            time_text = "Invalid date"

        col_reminder, col_complete, col_delete = st.columns([6, 1, 1])

        with col_reminder:

            if reminder["completed"]:
                st.markdown(
                    f"~~{i + 1}. {reminder['task']}~~ ✅"
                )
                st.caption(time_text)

            else:
                st.markdown(
                    f"**{i + 1}. {reminder['task']}** 🔔"
                )
                st.caption(time_text)

        with col_complete:

            if not reminder["completed"]:

                if st.button("✓", key=f"complete_reminder_{i}"):
                    manage_reminders(f"complete reminder {i + 1}")
                    st.rerun()

        with col_delete:

            if st.button("✕", key=f"delete_reminder_{i}"):
                manage_reminders(f"delete reminder {i + 1}")
                st.rerun()


# ---------------- DUE REMINDER NOTIFICATIONS ----------------

for reminder in due_reminders:

    reminder_id = reminder["id"]

    if reminder_id not in st.session_state.announced_reminders:

        st.warning(
            f"🔔 Reminder: {reminder['task']}"
        )

        st.session_state.announced_reminders.append(reminder_id)

        if st.session_state.voice_enabled:
            speak("Reminder. " + reminder["task"])


# ---------------- WELCOME SCREEN ----------------

if not st.session_state.messages:

    st.markdown("""
    <div class="hero">
        <h2>Welcome to NOVA ✨</h2>
        <p>
        Your personal virtual assistant is ready.
        Ask a question, perform a calculation,
        manage your tasks or set reminders.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Explore NOVA")

    col1, col2, col3 = st.columns(3)

    features = [
        ("🧮", "Smart Calculator"),
        ("🌐", "Web Search"),
        ("🎙️", "Voice Interaction"),
        ("📅", "Date & Time"),
        ("📚", "Knowledge Search"),
        ("📝", "Task Manager"),
        ("🔔", "Reminder System"),
        ("🔊", "Voice Responses"),
        ("💾", "Saved Tasks")
    ]

    for i, (icon, title) in enumerate(features):

        with [col1, col2, col3][i % 3]:

            st.markdown(f"""
            <div class="feature-card">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{title}</div>
            </div>
            """, unsafe_allow_html=True)

        if i % 3 == 2:
            st.write("")


# ---------------- CHAT HISTORY ----------------

st.markdown("---")
st.markdown("### 💬 Conversation")

for message in st.session_state.messages:

    with st.chat_message(
        message["role"],
        avatar="🤖" if message["role"] == "assistant" else "👤"
    ):

        st.markdown(message["content"])


# ---------------- MESSAGE PROCESSING ----------------

def process_message(user_input):

    user_input = user_input.strip()

    if not user_input:
        return

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🤖"):

        with st.spinner("NOVA is thinking..."):

            try:
                answer = get_response(
                    user_input
                )

            except Exception as e:

                print("NOVA error:", repr(e))

                answer = (
                    f"Something went wrong: "
                    f"{type(e).__name__}: {e}"
                )

        st.markdown(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    if st.session_state.voice_enabled:
        speak(answer)


# ---------------- VOICE INPUT ----------------

st.markdown("---")
st.markdown("### 🎙️ Voice Input")

voice_input = speech_to_text(
    start_prompt="🎙️ Start Speaking",
    stop_prompt="⏹️ Stop Recording",
    language="en",
    use_container_width=True,
    key="nova_voice"
)

if voice_input and voice_input != st.session_state.last_voice_input:

    st.session_state.last_voice_input = voice_input

    process_message(voice_input)

    st.rerun()


# ---------------- TEXT INPUT ----------------

user_input = st.chat_input("Message NOVA... Ask me anything")

if user_input:

    process_message(user_input)

    st.rerun()


# ---------------- FOOTER ----------------

st.markdown("---")

st.markdown(
    '<div style="text-align:center;color:#7784a8;'
    'font-size:12px;">NOVA • AI-POWERED VIRTUAL ASSISTANT'
    '<br>Designed with Python and Streamlit</div>',
    unsafe_allow_html=True
)
