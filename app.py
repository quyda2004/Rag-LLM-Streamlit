import streamlit as st
import tempfile
from rag_pipeline import Chatbot
import traceback

# Page config
st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
    .question-box { background-color: #e3f2fd; padding: 0.5rem; border-radius: 0.3rem; border-left: 4px solid #2196f3; }
    .answer-box { background-color: #f3e5f5; padding: 0.5rem; border-radius: 0.3rem; border-left: 4px solid #9c27b0; }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "pdf_processed" not in st.session_state:
        st.session_state.pdf_processed = False
    if "processing" not in st.session_state:
        st.session_state.processing = False


def load_chatbot_from_bytes(pdf_bytes, api_key):
    """Load chatbot from in-memory PDF bytes"""
    try:
        # Tạo file tạm trong bộ nhớ
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name

        bot = Chatbot(pdf_path=tmp_path, google_api_key=api_key)
        success = bot.reset(tmp_path, api_key)
        return bot if success else None
    except Exception as e:
        st.error(f"Lỗi khi khởi tạo chatbot: {str(e)}")
        st.code(traceback.format_exc())
        return None


def main():
    init_session_state()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Cài đặt")
        api_key = st.text_input("🔑 Gemini API Key:", type="password")
        if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

        st.header("📊 Trạng thái")
        if st.session_state.pdf_processed:
            st.success("✅ PDF đã xử lý")
        else:
            st.info("⏳ Chưa tải PDF")

    st.title("🤖 RAG Chatbot - PDF Q&A")

    tab1, tab2 = st.tabs(["📂 Upload tài liệu", "💬 Chatbot"])

    with tab1:
        uploaded_file = st.file_uploader("Chọn file PDF", type=["pdf"])
        if uploaded_file and api_key:
            if st.button("🚀 Xử lý tài liệu", use_container_width=True):
                st.session_state.processing = True
                try:
                    pdf_bytes = uploaded_file.read()
                    chatbot = load_chatbot_from_bytes(pdf_bytes, api_key)
                    if chatbot:
                        st.session_state.chatbot = chatbot
                        st.session_state.pdf_processed = True
                        st.session_state.chat_history = []
                        st.success("✅ Xử lý thành công!")
                        st.balloons()
                    else:
                        st.error("❌ Không thể xử lý file PDF")
                finally:
                    st.session_state.processing = False
        elif not api_key:
            st.warning("⚠️ Nhập API Key trước")
        elif not uploaded_file:
            st.info("📄 Chọn file PDF")

    with tab2:
        if st.session_state.chatbot and st.session_state.pdf_processed:
            if st.session_state.chat_history:
                st.subheader("📋 Lịch sử hội thoại")
                for i, (q, a) in enumerate(st.session_state.chat_history):
                    st.markdown(f'<div class="question-box"><b>🙋 Câu hỏi {i+1}:</b> {q}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="answer-box"><b>🤖 Trả lời:</b> {a}</div>', unsafe_allow_html=True)
                st.markdown("---")

            with st.form("question_form", clear_on_submit=True):
                query = st.text_area("Nhập câu hỏi:", height=100)
                if st.form_submit_button("🚀 Gửi") and query.strip():
                    with st.spinner("🤔 Đang xử lý..."):
                        answer = st.session_state.chatbot.ask(query)
                        st.session_state.chat_history.append((query, answer))
                        st.success("✅ Đã có câu trả lời!")
                        st.markdown(f'<div class="question-box"><b>🙋 Câu hỏi:</b> {query}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="answer-box"><b>🤖 Trả lời:</b> {answer}</div>', unsafe_allow_html=True)
        else:
            st.info("⬆️ Tải và xử lý file PDF ở tab 'Upload tài liệu' trước.")


if __name__ == "__main__":
    main()































# import os
# import streamlit as st
# from werkzeug.utils import secure_filename
# from rag_pipeline import Chatbot
# import traceback

# # Configuration
# UPLOAD_FOLDER = "uploads"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # Page config
# st.set_page_config(
#     page_title="RAG Chatbot",
#     page_icon="🤖",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # CSS for better styling
# st.markdown("""
# <style>
#     .stAlert > div {
#         padding: 1rem;
#         border-radius: 0.5rem;
#     }
#     .chat-container {
#         background-color: #f8f9fa;
#         padding: 1rem;
#         border-radius: 0.5rem;
#         margin: 1rem 0;
#     }
#     .question-box {
#         background-color: #e3f2fd;
#         padding: 0.5rem;
#         border-radius: 0.3rem;
#         margin: 0.5rem 0;
#         border-left: 4px solid #2196f3;
#     }
#     .answer-box {
#         background-color: #f3e5f5;
#         padding: 0.5rem;
#         border-radius: 0.3rem;
#         margin: 0.5rem 0;
#         border-left: 4px solid #9c27b0;
#     }
# </style>
# """, unsafe_allow_html=True)


# # Initialize session state
# def init_session_state():
#     if "chatbot" not in st.session_state:
#         st.session_state.chatbot = None
#     if "chat_history" not in st.session_state:
#         st.session_state.chat_history = []
#     if "pdf_processed" not in st.session_state:
#         st.session_state.pdf_processed = False
#     if "processing" not in st.session_state:
#         st.session_state.processing = False


# # Load chatbot function
# def load_chatbot(pdf_path, api_key):
#     """Load and initialize chatbot"""
#     try:
#         bot = Chatbot(pdf_path=pdf_path, google_api_key=api_key)
#         success = bot.reset(pdf_path, api_key)
#         if success:
#             return bot
#         else:
#             return None
#     except Exception as e:
#         st.error(f"Lỗi khi khởi tạo chatbot: {str(e)}")
#         return None


# # Main app
# def main():
#     init_session_state()

#     # Sidebar
#     with st.sidebar:
#         st.header("⚙️ Cài đặt")

#         # API Key input
#         api_key = st.text_input(
#             "🔑 Gemini API Key:",
#             type="password",
#             help="Nhập API key của Google Gemini để sử dụng chatbot"
#         )

#         # Clear chat history button
#         if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
#             st.session_state.chat_history = []
#             st.rerun()

#         # Status
#         st.header("📊 Trạng thái")
#         if st.session_state.pdf_processed:
#             st.success("✅ PDF đã được xử lý")
#             st.success("✅ Chatbot sẵn sàng")
#         else:
#             st.info("⏳ Chưa tải PDF")

#     # Main content
#     st.title("🤖 RAG Chatbot - Hỏi đáp tài liệu PDF")
#     st.markdown("---")

#     # Tabs
#     tab1, tab2 = st.tabs(["📂 Upload tài liệu", "💬 Chatbot"])

#     # Tab 1: Upload
#     with tab1:
#         st.header("📁 Tải lên tài liệu PDF")

#         # File uploader
#         uploaded_file = st.file_uploader(
#             "Chọn file PDF",
#             type=["pdf"],
#             help="Chọn file PDF để tạo chatbot hỏi đáp"
#         )

#         if uploaded_file and api_key:
#             if not st.session_state.processing:
#                 if st.button("🚀 Xử lý tài liệu", type="primary", use_container_width=True):
#                     st.session_state.processing = True

#                     try:
#                         # Save uploaded file
#                         filename = secure_filename(uploaded_file.name)
#                         pdf_path = os.path.join(UPLOAD_FOLDER, filename)

#                         with open(pdf_path, "wb") as f:
#                             f.write(uploaded_file.read())

#                         # Process with progress bar
#                         progress_bar = st.progress(0)
#                         status_text = st.empty()

#                         status_text.text("🔄 Đang khởi tạo chatbot...")
#                         progress_bar.progress(20)

#                         # Load chatbot
#                         chatbot = load_chatbot(pdf_path, api_key)
#                         progress_bar.progress(100)

#                         if chatbot:
#                             st.session_state.chatbot = chatbot
#                             st.session_state.pdf_processed = True
#                             st.session_state.chat_history = []
#                             status_text.empty()
#                             progress_bar.empty()
#                             st.success(f"✅ File {filename} đã được xử lý thành công!")
#                             st.balloons()
#                         else:
#                             status_text.empty()
#                             progress_bar.empty()
#                             st.error("❌ Không thể xử lý file PDF")

#                     except Exception as e:
#                         st.error(f"❌ Lỗi: {str(e)}")
#                         st.code(traceback.format_exc())

#                     finally:
#                         st.session_state.processing = False

#         elif not api_key:
#             st.warning("⚠️ Vui lòng nhập API Key trước")
#         elif not uploaded_file:
#             st.info("📄 Chọn file PDF để bắt đầu")

#     # Tab 2: Chat
#     with tab2:
#         st.header("💬 Trò chuyện với tài liệu")

#         if st.session_state.chatbot and st.session_state.pdf_processed:
#             # Chat interface
#             with st.container():
#                 # Display chat history
#                 if st.session_state.chat_history:
#                     st.subheader("📋 Lịch sử hội thoại")

#                     for i, (question, answer) in enumerate(st.session_state.chat_history):
#                         with st.container():
#                             st.markdown(f"""
#                             <div class="question-box">
#                                 <strong>🙋 Câu hỏi {i + 1}:</strong> {question}
#                             </div>
#                             """, unsafe_allow_html=True)

#                             st.markdown(f"""
#                             <div class="answer-box">
#                                 <strong>🤖 Trả lời:</strong> {answer}
#                             </div>
#                             """, unsafe_allow_html=True)

#                     st.markdown("---")

#                 # Input section
#                 st.subheader("❓ Đặt câu hỏi mới")

#                 with st.form("question_form", clear_on_submit=True):
#                     query = st.text_area(
#                         "Nhập câu hỏi của bạn:",
#                         height=100,
#                         placeholder="Ví dụ: Tài liệu này nói về điều gì?",
#                         help="Hãy đặt câu hỏi cụ thể về nội dung tài liệu"
#                     )

#                     col1, col2 = st.columns([1, 4])

#                     with col1:
#                         submit_button = st.form_submit_button("🚀 Gửi", type="primary", use_container_width=True)

#                     if submit_button and query.strip():
#                         with st.spinner("🤔 Đang tìm kiếm và phân tích..."):
#                             try:
#                                 answer = st.session_state.chatbot.ask(query)

#                                 # Add to chat history
#                                 st.session_state.chat_history.append((query, answer))

#                                 # Display new answer immediately
#                                 st.success("✅ Đã có câu trả lời!")

#                                 with st.container():
#                                     st.markdown(f"""
#                                     <div class="question-box">
#                                         <strong>🙋 Câu hỏi:</strong> {query}
#                                     </div>
#                                     """, unsafe_allow_html=True)

#                                     st.markdown(f"""
#                                     <div class="answer-box">
#                                         <strong>🤖 Trả lời:</strong> {answer}
#                                     </div>
#                                     """, unsafe_allow_html=True)

#                             except Exception as e:
#                                 st.error(f"❌ Lỗi khi xử lý câu hỏi: {str(e)}")

#                     elif submit_button and not query.strip():
#                         st.warning("⚠️ Vui lòng nhập câu hỏi trước khi gửi")

#                 # Example questions
#                 with st.expander("💡 Gợi ý câu hỏi"):
#                     st.markdown("""
#                     **Câu hỏi tổng quan:**
#                     - Tài liệu này nói về chủ đề gì?
#                     - Tóm tắt nội dung chính của tài liệu
#                     - Những điểm quan trọng nhất là gì?

#                     **Câu hỏi chi tiết:**
#                     - Giải thích về [khái niệm cụ thể]
#                     - Có những phương pháp nào được đề cập?
#                     - Kết luận của tác giả là gì?

#                     **Câu hỏi phân tích:**
#                     - So sánh giữa A và B trong tài liệu
#                     - Ưu điểm và nhược điểm của phương pháp X là gì?
#                     - Tác giả đưa ra bằng chứng gì để hỗ trợ quan điểm?
#                     """)

#         else:
#             st.info("⬆️ Vui lòng tải lên và xử lý file PDF ở tab 'Upload tài liệu' trước.")

#             # Tips for users
#             with st.expander("📚 Hướng dẫn sử dụng"):
#                 st.markdown("""
#                 **Bước 1:** Chuẩn bị API Key
#                 - Truy cập Google AI Studio để lấy API key
#                 - Dán API key vào ô bên sidebar

#                 **Bước 2:** Upload tài liệu
#                 - Chọn file PDF trong tab "Upload tài liệu"
#                 - Nhấn "Xử lý tài liệu" và đợi hoàn thành

#                 **Bước 3:** Đặt câu hỏi
#                 - Chuyển sang tab "Chatbot"
#                 - Nhập câu hỏi và nhận câu trả lời từ AI

#                 **Lưu ý:**
#                 - Hỗ trợ file PDF tiếng Việt và tiếng Anh
#                 - Câu trả lời dựa trên nội dung tài liệu
#                 - Có thể hỏi nhiều câu liên tiếp
#                 """)


# if __name__ == "__main__":
#     main()




