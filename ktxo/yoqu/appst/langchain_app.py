import json
import os
from io import StringIO

import streamlit as st

from ktxo.yoqu.api_client import APIWrapper
from ktxo.yoqu.langchain.yoqu_llm import YoquChatGPTLLM, load_template, save_template, build_template

st.set_page_config(layout="wide")
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
st.title("(Yoqu) NLP POC")

api = APIWrapper()

if not "template_prompt" in st.session_state:
    st.session_state.template_prompt = None

with st.sidebar:
    try:
        resources = api.list_resources()
    except Exception as e:
        st.error(f"Encountered an error while accessing the API: {e}")
        st.stop()
    st.session_state.resource = st.selectbox("Select Resource", resources)
    if st.button("Refresh"):
        api.refresh_resource(st.session_state.resource)
    if st.button("Restart"):
        api.start_resource(st.session_state.resource)
    if st.button("Status"):
        st.json(api.info_resource(st.session_state.resource))

tab1, tab2 = st.tabs(["Summarization (Langchain)", "About this 🤌"])


def layout_tab2(container):
    container.markdown("""
    - POC ChatGPT _Yoqu Resource_ as a Custom LLM for Langchain (https://python.langchain.com/docs/modules/model_io/llms/custom_llm):
        - Summarization
        - NER   
    - Yoqu API http://localhost:8000/docs
    - For this POC a _Yoqu Resource_ is a RPA controlling a Chrome browser using to https://chat.openai.com 
    """)

TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), "..", "langchain", "templates")
def list_templates() -> list[str]:
    return sorted(f for f in os.listdir(TEMPLATE_FOLDER) if f.lower().endswith(".json"))

def layout_tab1(container):
    c1, c2 = container.columns(2)
    templates = list_templates()
    with c2:
        template_file = st.selectbox("Select Template",
                                     templates,
                                     format_func=lambda x: os.path.splitext(x)[0].replace("_", " ").title(),
                                     key="template_file")
        st.json(load_template(template_file).json(), expanded=False)


        with st.expander("Create a new Prompt Template from a prompt"):
            with st.form("create_template"):
                template_string = st.text_area("Enter prompt text",
                                               placeholder="Provide a synonym for the following text:\n"
                                                           "{text}")
                template_file = st.text_input("Template filename",
                                              placeholder="prompt_test",
                                              help="Enter template filename, don't use spaces, use '_' instead")
                if template_file and not template_file.lower().endswith(".json"):
                    template_file += ".json"
                if st.form_submit_button("Validate"):
                    try:
                        if template_file and template_string:
                            build_template(template_string)
                            st.success("OK")
                    except Exception as e:
                        st.error(f"Cannot build a template from text. ({e})")
                        st.stop()
                if st.form_submit_button("Create"):
                        try:
                            if template_file and template_string:
                                save_template(build_template(template_string), template_file)
                                st.success(f"Template '{template_file}' created. Refresh Page")
                        except Exception as e:
                            st.error(f"Cannot build a template from file. ({e})")
                            st.stop()

        # if template_file:
        #     try:
        #         st.json(load_template(template_file).template, expanded=False)
        #     except Exception as e:
        #         st.error(f"Cannot open template file '{template_file}'. ({e})")
        #         st.stop()
        #     st.text_area("Template Json",
        #                  value=st.session_state.template_prompt.json(indent=4),
        #                  height=500,
        #                  disabled=True)

    with c1:
        prompt = st.text_area("Enter Prompt",
                              placeholder="Enter text to summarize",
                              height=500,
                              label_visibility="hidden")
        execute = st.button("Execute")
        if prompt and execute:
            try:
                llm = YoquChatGPTLLM(resource=st.session_state.resource)
                template = load_template(st.session_state.template_file)
                res = llm(prompt=template.format(**{v:prompt for v in template.input_variables}),
                          template=template_file,
                          resource=st.session_state.resource)
                if res:
                    try:
                        json.loads(res)
                        st.json(res)
                    except:
                        st.write(res)
            except Exception as e:
                st.error(f"Got some error: {e}")
                st.stop()
layout_tab1(tab1)
layout_tab2(tab2)

