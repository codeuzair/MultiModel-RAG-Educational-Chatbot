# import streamlit as st
# import requests
# from exception.exceptions import TradingBotException
# import sys

# BASE_URL = "http://localhost:8002"  # Backend endpoint

# st.set_page_config(
#     page_title="📈 Stock Market Agentic Chatbot",
#     page_icon="📈",
#     layout="centered",
#     initial_sidebar_state="expanded",
# )

# st.title("📈 Stock Market Agentic Chatbot")

# # Initialize chat history
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # Sidebar: Upload documents
# with st.sidebar:
#     st.header("📄 Upload Documents")
#     st.markdown("Upload **stock market PDFs or DOCX** to create knowledge base.")
#     uploaded_files = st.file_uploader("Choose files", type=["pdf", "docx"], accept_multiple_files=True)

#     if st.button("Upload and Ingest"):
#         if uploaded_files:
#             files = []
#             for f in uploaded_files:
#                 file_data = f.read()
#                 if not file_data:
#                     continue
#                 files.append(("files", (getattr(f, "name", "file.pdf"), file_data, f.type)))

#             if files:
#                 try:
#                     with st.spinner("Uploading and processing files..."):
#                         response = requests.post(f"{BASE_URL}/upload", files=files)
#                         if response.status_code == 200:
#                             st.success("✅ Files uploaded and processed successfully!")
#                         else:
#                             st.error("❌ Upload failed: " + response.text)
#                 except Exception as e:
#                     raise TradingBotException(e, sys)
#             else:
#                 st.warning("Some files were empty or unreadable.")

# # Display chat history
# st.header("💬 Chat")
# for chat in st.session_state.messages:
#     if chat["role"] == "user":
#         st.markdown(f"**🧑 You:** {chat['content']}")
#     else:
#         st.markdown(f"**🤖 Bot:** {chat['content']}")

# # Chat input box at bottom
# with st.form(key="chat_form", clear_on_submit=True):
#     user_input = st.text_input("Your message", placeholder="e.g. Tell me about NIFTY 50")
#     submit_button = st.form_submit_button("Send")

# if submit_button and user_input.strip():
#     try:
#         # Show user message
#         st.session_state.messages.append({"role": "user", "content": user_input})

#         # Show thinking spinner while backend processes
#         with st.spinner("Bot is thinking..."):
#             payload = {"question": user_input}
#             response = requests.post(f"{BASE_URL}/query", json=payload)

#         if response.status_code == 200:
#             answer = response.json().get("answer", "No answer returned.")
#             st.session_state.messages.append({"role": "bot", "content": answer})
#             st.rerun()  # 🔁 fixed here
#         else:
#             st.error("❌ Bot failed to respond: " + response.text)

#     except Exception as e:
#         raise TradingBotException(e, sys)




import streamlit as st
import requests
# from exception.exceptions import TradingBotException
import sys
BASE_URL = "http://localhost:8000"  # Change if backend runs elsewhere

st.set_page_config(
    page_title="Physics Helping Chatbot",
    page_icon="",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.title("Physics helping Chatbot")

# Sidebar: Upload Files
with st.sidebar:
    st.header("📄 Upload Documents")
    st.markdown("Upload your **physics document** to prepare the knowledge base.")
    uploaded_files = st.file_uploader("Choose files", type=["pdf", "docx"], accept_multiple_files=True)
    print(uploaded_files)
    if st.button("Upload and Ingest"):
        if uploaded_files:
            files = []
            for f in uploaded_files:
                file_data = f.read()
                if not file_data:
                    continue  # skip empty files
                files.append(("files", (getattr(f, "name", "file.pdf"), file_data, f"type")))

            if files:
                try:
                    with st.spinner("Uploading and processing files..."):
                        response = requests.post(f"{BASE_URL}/upload", files=files)
                        if response.status_code == 200:
                            st.success("✅ Files uploaded and processed successfully!")
                        else:
                            st.error("❌ Upload failed: " + response.text)
                except Exception as e:
                    raise TradingBotException(e,sys)
            else:
                st.warning("Some files were empty or unreadable.")

        
# Main Panel: Ask a Question
st.header("Ask a Question")
st.markdown("Enter your **Physics-related** question. The chatbot will search the documents and respond intelligently.")

question = st.text_input("Your question", placeholder="e.g. What is velocity")

if st.button("Ask"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Thinking..."):
            payload = {"question": question}
            response = requests.post(f"{BASE_URL}/query", json=payload)
            if response.status_code == 200:
                answer = response.json().get("answer", "No answer returned.")
                st.markdown("### 💬 Answer")
                st.write(answer)
            else:
                st.error("❌ Failed to get answer: " + response.text)