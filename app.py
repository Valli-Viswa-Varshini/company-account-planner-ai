import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Sync Streamlit secrets to env for LangChain
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
if "TAVILY_API_KEY" in st.secrets:
    os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]

from agent import graph  # Import the LangGraph agent AFTER env is set

# Page Config
st.set_page_config(page_title="AI Company Research Agent", layout="wide", page_icon="🏢")

# Load CSS
def load_css():
    with open("styles.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "account_plan" not in st.session_state:
    st.session_state.account_plan = None
if "research_running" not in st.session_state:
    st.session_state.research_running = False

# Sidebar
with st.sidebar:
    st.header("🔧 Input Setup")
    company = st.text_input("Company Name", "Tesla")
    goals = st.text_area("Research Goals", "Focus on recent financial performance and AI investments.")
    
    if st.button("🚀 Start Research"):
        st.session_state.research_running = True
        st.session_state.messages = [] # Clear previous chat
        st.session_state.account_plan = None
        
        # Initial State
        initial_state = {
            "company": company,
            "goals": goals,
            "messages": [],
            "research_data": [],
            "plan_sections": {},
            "critique_count": 0
        }
        
        # Run Agent
        with st.spinner("Agent is researching..."):
            try:
                # Stream events from the graph
                for event in graph.stream(initial_state):
                    print(f"DEBUG: Event received: {event.keys()}") # Debug log
                    for key, value in event.items():
                        if "messages" in value:
                            for msg in value["messages"]:
                                st.session_state.messages.append({"role": "agent", "text": msg})
                        if "plan_sections" in value:
                            print("DEBUG: Plan sections found!") # Debug log
                            st.session_state.account_plan = value["plan_sections"]
            except Exception as e:
                st.error(f"Error running agent: {e}")
                print(f"DEBUG: Error: {e}")
        
        st.session_state.research_running = False
        st.rerun()

# Main Layout
st.title("🏢 AI Company Research Assistant")
st.markdown("### Intelligent Agentic Workflow")

col_chat, col_plan = st.columns([1, 1.5])

with col_chat:
    st.subheader("💬 Research Logs & Chat")
    
    # Display Chat
    for msg in st.session_state.messages:
        role_icon = "🤖" if msg["role"] == "agent" else "👤"
        st.markdown(f"**{role_icon} {msg['role'].title()}**: {msg['text']}")

    # User Input (Post-Research)
    if st.session_state.account_plan:
        user_input = st.text_input("Ask follow-up questions:", key="chat_input")
        if st.button("Send"):
            st.session_state.messages.append({"role": "user", "text": user_input})
            # Here you would call the agent again with the new input
            st.info("Conversational updates coming soon!")
            st.rerun()

with col_plan:
    st.subheader("📑 Strategic Account Plan")
    
    if not st.session_state.account_plan:
        st.info("👈 Start research to generate a plan.")
    else:
        plan = st.session_state.account_plan
        
        # Editable Sections
        for key, content in plan.items():
            label = key.replace("_", " ").title()
            with st.expander(label, expanded=True):
                new_content = st.text_area(f"Edit {label}", content, height=150, key=key)
                if new_content != content:
                    plan[key] = new_content
                    st.success(f"Updated {label}")

