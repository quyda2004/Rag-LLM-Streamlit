import os
import streamlit as st
from werkzeug.utils import secure_filename
from rag_pipeline import Chatbot

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------- CACHE CHATBOT -----------------
@st.cache_resource
def load_chatbot(pdf_path, api_key):
    bot = Chatbot(pdf_path=pdf_path, google_api_key=api_key)
    bot.reset(pdf_path, api_key)
    return bot

# ----------------- SESSION STATE -----------------
if "chatbot" not in st.session_state:
    st.session_state.chatbot = None

# ----------------- UI -----------------
tab1, tab2 = st.tabs(["📂 Upload tài liệu", "💬 Chatbot"])

# ========== TAB 1: UPLOAD ==========
with tab1:
    st.header("Tải lên tài liệu PDF")
    api_key = st.text_input("Gemini API Key:", type="password", value="YOUR_DEFAULT_GOOGLE_API_KEY")
    uploaded_file = st.file_uploader("Chọn file PDF", type=["pdf"])

    if uploaded_file:
        filename = secure_filename(uploaded_file.name)
        pdf_path = os.path.join(UPLOAD_FOLDER, filename)

        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.read())

        # Chỉ load 1 lần và lưu vào cache
        st.session_state.chatbot = load_chatbot(pdf_path, api_key)
        st.success(f"✅ File {filename} đã tải lên và Chatbot đã sẵn sàng!")

# ========== TAB 2: CHAT ==========
with tab2:
    st.header("Trò chuyện với Chatbot")

    if st.session_state.chatbot:
        query = st.text_input("Nhập câu hỏi:")
        if st.button("Gửi câu hỏi"):
            if query.strip():
                with st.spinner("🤖 Đang suy nghĩ..."):
                    answer = st.session_state.chatbot.ask(query)
                st.markdown(f"*Trả lời:* {answer}")
            else:
                st.warning("⚠ Vui lòng nhập câu hỏi trước khi gửi")
    else:
        st.info("⬆ Vui lòng tải lên file PDF ở tab 'Upload tài liệu' trước.")