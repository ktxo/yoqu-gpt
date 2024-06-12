#https://docs.streamlit.io/knowledge-base/tutorials/build-conversational-apps
import json

import streamlit as st
from ktxo.yoqu.client.api_client import APIWrapper

st.title("(Yoqu) ChatGPT-like clone")
with st.expander("About this 🤌"):
    st.markdown("""
    - POC using ChatGPT. ChatGPT _Yoqu Resource_ is exposed as an API (http://localhost:8000/docs)
    - For this POC a _Yoqu Resource_ is a RPA controlling a Chrome browser using to https://chat.openai.com 
    - Adapted from https://docs.streamlit.io/knowledge-base/tutorials/build-conversational-apps#build-a-chatgpt-like-app
    """)




api = APIWrapper()

if "chats" not in st.session_state:
    st.session_state.chats:list[dict[str, str]] = []
if "chat" not in  st.session_state:
    st.session_state.chat:dict[str, str] = None

if "chat_title" not in  st.session_state:
    st.session_state.chat_title:str = ""

if "chat_obj" not in st.session_state:
    st.session_state.chat_obj:dict = {}
if "message" not in st.session_state:
    st.session_state.messages:list = []

if "resource" not in st.session_state:
    st.session_state.resource = None

@st.cache_data(ttl=0)
def get_chats(resource:str):
    try:
        try:
            st.session_state.chats = api.get_chats(resource=resource)
        except Exception as e:
            st.error(f"Got some error: {e}")
            st.stop()
    except Exception as e:
        print("-----------------", e)
    if st.session_state.chats:
        print(f"Found {len(st.session_state.chats)} chats")
    else:
        st.session_state.chats = []
    return st.session_state.chats

def get_resources():
    try:
        return api.list_resources()
    except Exception as e:
        st.error(f"Got some error: {e}")
        st.stop()


with st.expander(f"Select Chat 💬"):
    c1, c2, c3, c4 = st.columns(4)
    c1.write(f"Found {len(st.session_state.chats)} chats")
    c2.checkbox("Raw response", help="Show response raw (not html)", key="raw_response")
    c3.checkbox("Restart resource", help="Restart resource", key="restart_resource")
    c4.checkbox("Refresh resource", help="Refresh resource", key="refresh_resource")
    if st.session_state.refresh_resource:
        api.refresh_resource(st.session_state.resource)

    if st.session_state.restart_resource:
        api.stop_resource(st.session_state.resource)
        api.start_resource(st.session_state.resource)
    st.session_state.resource = st.selectbox("Select a resource", get_resources())

    if st.session_state.resource is None:
        st.warning(f"Not resources available. :-(")
        st.stop()
    chats = {chat["chat_id"]:chat["name"] for chat in get_chats(st.session_state.resource)}
    st.session_state.chat = st.selectbox("Select a chat", [c for c in chats.keys()],
                                         index=None,
                                         format_func=lambda x: chats[x])
    if st.session_state.chat is None:
        st.session_state.chat_obj = {}
        st.session_state.chat_title = None

if st.session_state.chat:
    try:
        chat_id = st.session_state.chat
        obj = api.get_chat(chat_id, resource=st.session_state.resource)
        if obj:
            st.session_state.chat_obj = obj
        else:
            st.error(f"Got some error, please retry the operation")
            st.stop()
    except:
        st.error(f"Got some error, retry")
        st.stop()

st.session_state.messages = []
for m in st.session_state.chat_obj.get("messages", []):
    if m["type"] == "REQUEST":
        role = "user"
    else:
        role = "assistant"
    st.session_state.messages.append({"role": role, "content": m["raw_text"]})

    with st.chat_message(role):
        if st.session_state.raw_response:
            st.text(m["text"])
        else:
            if m["raw_text"]:
                st.markdown(m["raw_text"], unsafe_allow_html=True)
            else:
                st.markdown(m["text"])

if prompt := st.chat_input("What is up?"):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        #print(f"RPA >> {prompt[0:20]}")
        if st.session_state.chat_obj:
            obj = api.update_chat(st.session_state.chat, prompt, resource=st.session_state.resource)
        else:
            obj = api.new_chat(prompt, resource=st.session_state.resource)
            if obj: st.info(f"Please refrest list of chats")
        if obj:
            st.session_state.chat_obj = obj
        else:
            st.error(f"Got some error, please retry the operation")
            st.stop()
        full_response = st.session_state.chat_obj["messages"][-1]["text"]
        #print(f"RPA << '{full_response[0:20]}...'")
        message_placeholder.write(full_response, unsafe_allow_html=True)
    st.session_state.messages.append({"role": "assistant", "content": full_response[-1]})

if st.session_state.chat_obj and st.session_state.chat:
    st.download_button("Download chat as json",
                       data=json.dumps(st.session_state.chat_obj, indent=4),
                       file_name=f"{st.session_state.chat}.json",
                       mime="application/json")