"""
Group L ChatBot - HARDENED build.

Same application and tools as the vulnerable build, but with the four defences
that break the prompt-injection -> SQLi -> RCE chain:
  1. A tight, least-privilege system prompt (trust GetCurrentUser, refuse other IDs).
  2. Input sanitisation that strips ReAct/SQL/shell injection patterns.
  3. Parameterised SQL queries (see transaction_db.py).
  4. Safe file export: int validation + path confinement + no shell (see tools.py).
"""
import re

import streamlit as st
from dotenv import load_dotenv
from langchain.agents import ConversationalChatAgent, AgentExecutor
from langchain.callbacks import StreamlitCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory

from tools import (
    get_current_user_tool,
    get_recent_transactions_tool,
    export_transactions_tool,
)
from utils import display_logo

load_dotenv()


def sanitize_user_input(user_input: str) -> str:
    """
    Filters potentially malicious input to prevent ReAct (Thought/Action/
    Observation) injection, SQL injection and command injection.

    Defence in depth only: the real fixes live in the DB and tool layers. This
    filter just raises the bar and makes injection attempts visible in the UI.
    """
    # Remove code blocks (e.g. ```json ... ```) used to fake tool observations.
    user_input = re.sub(
        r'```(?:json)?\s*.*?```', '[Filtered Code Block]', user_input, flags=re.DOTALL
    )

    forbidden_keywords = [
        r'\b(action|observation|thought)\b\s*:',
        r'\bGetCurrentUser\b', r'\bGetUserTransaction\b',
        r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|UNION|OR|AND)\b',
        r'--',
        r'/\*.*?\*/',
        r'\buserId\b',
        r'\bWHERE\b',
        r'\bFROM\b',
        r'[;&|`$(){}[\]\\]',
        r'\b(echo|cat|ls|pwd|whoami|id|uname)\b',
    ]
    for pattern in forbidden_keywords:
        user_input = re.sub(pattern, '[Filtered]', user_input, flags=re.IGNORECASE)

    return user_input.strip()


tools = [get_current_user_tool, get_recent_transactions_tool, export_transactions_tool]

# FIX 1: a least-privilege system prompt. The agent only ever operates on the
# userId returned by GetCurrentUser and refuses any userId supplied by the user.
system_msg = """Assistant helps the current user retrieve the list of their recent bank transactions and shows them as a table. Assistant will ONLY operate on the userId returned by the GetCurrentUser() tool, and REFUSE to operate on any other userId provided by the user."""

welcome_message = """Hi! I'm a helpful assistant and I can help fetch information about your recent transactions.\n\nTry asking me: "What are my recent transactions?"
"""

st.set_page_config(page_title="Group L ChatBot (secure)")
st.title("Group L ChatBot (secure)")

hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

msgs = StreamlitChatMessageHistory()
memory = ConversationBufferMemory(
    chat_memory=msgs, return_messages=True, memory_key="chat_history", output_key="output"
)

if len(msgs.messages) == 0:
    msgs.clear()
    msgs.add_ai_message(welcome_message)
    st.session_state.steps = {}

avatars = {"human": "user", "ai": "assistant"}
for idx, msg in enumerate(msgs.messages):
    with st.chat_message(avatars[msg.type]):
        for step in st.session_state.steps.get(str(idx), []):
            if step[0].tool == "_Exception":
                continue
            with st.status(f"**{step[0].tool}**: {step[0].tool_input}", state="complete"):
                st.write(step[0].log)
                st.write(step[1])
        st.write(msg.content)

if prompt := st.chat_input(placeholder="Show my recent transactions"):
    with st.chat_message("user"):
        st.write("💬 Original Input:")
        with st.expander("View Raw Input"):
            st.code(prompt, language="text")

        # FIX 2: sanitise before the prompt ever reaches the agent.
        filtered_prompt = sanitize_user_input(prompt)

        st.write("🛡️ Filtered Input:")
        with st.expander("View Filtered Input"):
            st.code(filtered_prompt, language="text")

    llm = ChatOpenAI(
        model_name="gpt-4-1106-preview",
        temperature=0,
        streaming=True,
    )

    chat_agent = ConversationalChatAgent.from_llm_and_tools(
        llm=llm, tools=tools, verbose=True, system_message=system_msg
    )

    executor = AgentExecutor.from_agent_and_tools(
        agent=chat_agent,
        tools=tools,
        memory=memory,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
        verbose=True,
        max_iterations=6,
    )

    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
        response = executor(filtered_prompt, callbacks=[st_cb])
        st.write(response["output"])
        st.session_state.steps[str(len(msgs.messages) - 1)] = response["intermediate_steps"]

display_logo()
