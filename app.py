import streamlit as st
import tempfile
import os
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
    .question-box { 
        background-color: #e3f2fd; 
        padding: 0.8rem; 
        border-radius: 0.5rem; 
        border-left: 4px solid #2196f3; 
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .answer-box { 
        background-color: #f3e5f5; 
        padding: 0.8rem; 
        border-radius: 0.5rem; 
        border-left: 4px solid #9c27b0; 
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .error-box {
        background-color: #ffebee;
        padding: 0.8rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f44336;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #e8f5e8;
        padding: 0.8rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4caf50;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "pdf_processed" not in st.session_state:
        st.session_state.pdf_processed = False
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "current_pdf_name" not in st.session_state:
        st.session_state.current_pdf_name = None


def load_chatbot_from_bytes(pdf_bytes, api_key, pdf_name):
    """Load chatbot from in-memory PDF bytes with improved error handling"""
    temp_file = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            temp_file = tmp.name

        # Initialize chatbot with error handling
        st.info("🔄 Đang khởi tạo chatbot...")
        bot = Chatbot(pdf_path=temp_file, google_api_key=api_key)
        
        st.info("🔄 Đang xử lý tài liệu...")
        success = bot.reset(temp_file, api_key)
        
        if success:
            st.session_state.current_pdf_name = pdf_name
            return bot
        else:
            st.error("❌ Không thể khởi tạo chatbot")
            return None
            
    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ Lỗi khi khởi tạo chatbot: {error_msg}")
        
        # Show detailed error for debugging
        with st.expander("🔍 Chi tiết lỗi (để debug)"):
            st.code(traceback.format_exc())
        
        return None
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass


def display_chat_message(question, answer, index):
    """Display a single chat message with better formatting"""
    st.markdown(f"""
    <div class="question-box">
        <strong>🙋 Câu hỏi {index}:</strong><br>
        {question}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="answer-box">
        <strong>🤖 Trả lời:</strong><br>
        {answer}
    </div>
    """, unsafe_allow_html=True)


def main():
    init_session_state()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Cài đặt")
        
        # API Key input with multiple options
        st.markdown("### 🔑 API Key Configuration")
        
        # Check if API key is in secrets (for deployment)
        api_key_from_secrets = st.secrets.get("GOOGLE_API_KEY", "")
        
        if api_key_from_secrets:
            st.success("✅ API Key đã được cấu hình trong secrets")
            api_key = api_key_from_secrets
            st.info("🔒 Sử dụng API key từ Streamlit secrets")
        else:
            api_key = st.text_input(
                "🔑 Nhập Gemini API Key:", 
                type="password",
                help="Lấy API key từ https://makersuite.google.com/app/apikey",
                placeholder="AIzaSy..."
            )
            
            if api_key:
                st.success("✅ API Key đã nhập")
            else:
                st.warning("⚠️ Cần API Key để sử dụng")
                
                with st.expander("❓ Làm thế nào để lấy API Key?"):
                    st.markdown("""
                    **Bước 1:** Truy cập [Google AI Studio](https://makersuite.google.com/app/apikey)
                    
                    **Bước 2:** Đăng nhập với tài khoản Google
                    
                    **Bước 3:** Nhấn "Create API Key" 
                    
                    **Bước 4:** Copy API key và dán vào ô trên
                    
                    **Lưu ý:** 
                    - API key miễn phí có giới hạn sử dụng
                    - Không chia sẻ API key với người khác
                    - API key bắt đầu bằng "AIzaSy..."
                    """)
        
        # Clear chat history button
        if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

        # Status section
        st.header("📊 Trạng thái")
        if st.session_state.pdf_processed:
            st.success("✅ PDF đã xử lý")
            if st.session_state.current_pdf_name:
                st.info(f"📄 File: {st.session_state.current_pdf_name}")
        else:
            st.info("⏳ Chưa tải PDF")
            
        # Processing indicator
        if st.session_state.processing:
            st.warning("🔄 Đang xử lý...")

    # Main content
    st.title("🤖 RAG Chatbot - PDF Q&A")
    st.markdown("*Hỏi đáp thông minh với tài liệu PDF*")

    # Create tabs
    tab1, tab2 = st.tabs(["📂 Upload tài liệu", "💬 Chatbot"])

    # Tab 1: Upload Document
    with tab1:
        st.header("📁 Tải lên tài liệu PDF")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Chọn file PDF",
            type=["pdf"],
            help="Chọn file PDF để tạo chatbot Q&A"
        )
        
        # Show file info if uploaded
        if uploaded_file:
            st.info(f"📄 File đã chọn: {uploaded_file.name} ({uploaded_file.size:,} bytes)")
        
        # Processing section
        if uploaded_file and api_key:
            if not st.session_state.processing:
                if st.button("🚀 Xử lý tài liệu", type="primary", use_container_width=True):
                    st.session_state.processing = True
                    
                    # Create progress placeholder
                    progress_placeholder = st.empty()
                    
                    try:
                        with progress_placeholder.container():
                            st.info("📖 Đang đọc file PDF...")
                            
                        # Read PDF bytes
                        pdf_bytes = uploaded_file.read()
                        
                        with progress_placeholder.container():
                            st.info("🔧 Đang xử lý và tạo vector database...")
                        
                        # Load chatbot
                        chatbot = load_chatbot_from_bytes(pdf_bytes, api_key, uploaded_file.name)
                        
                        if chatbot:
                            st.session_state.chatbot = chatbot
                            st.session_state.pdf_processed = True
                            st.session_state.chat_history = []
                            
                            # Clear progress and show success
                            progress_placeholder.empty()
                            
                            st.markdown("""
                            <div class="success-box">
                                <strong>✅ Xử lý thành công!</strong><br>
                                Bạn có thể chuyển sang tab "Chatbot" để bắt đầu hỏi đáp.
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.balloons()
                        else:
                            progress_placeholder.empty()
                            st.markdown("""
                            <div class="error-box">
                                <strong>❌ Không thể xử lý file PDF</strong><br>
                                Vui lòng thử lại hoặc chọn file PDF khác.
                            </div>
                            """, unsafe_allow_html=True)

                    except Exception as e:
                        progress_placeholder.empty()
                        st.error(f"❌ Lỗi: {str(e)}")
                        with st.expander("🔍 Chi tiết lỗi"):
                            st.code(traceback.format_exc())

                    finally:
                        st.session_state.processing = False
                        
        elif not api_key:
            st.warning("⚠️ Vui lòng nhập API Key trước")
        elif not uploaded_file:
            st.info("📄 Chọn file PDF để bắt đầu")
            
        # Tips section
        with st.expander("💡 Hướng dẫn sử dụng"):
            st.markdown("""
            **Bước 1: Chuẩn bị API Key**
            - Truy cập [Google AI Studio](https://makersuite.google.com/app/apikey)
            - Tạo và copy API key
            - Dán vào ô "Gemini API Key" bên sidebar

            **Bước 2: Upload tài liệu**
            - Chọn file PDF (hỗ trợ tiếng Việt và tiếng Anh)
            - Nhấn "Xử lý tài liệu" và đợi hoàn thành

            **Bước 3: Chatbot**
            - Chuyển sang tab "Chatbot"
            - Nhập câu hỏi và nhận câu trả lời từ AI

            **Lưu ý:**
            - File PDF nên có văn bản (không phải hình ảnh scan)
            - Quá trình xử lý có thể mất vài phút
            - Câu trả lời dựa hoàn toàn trên nội dung tài liệu
            """)

    # Tab 2: Chatbot
    with tab2:
        if st.session_state.chatbot and st.session_state.pdf_processed:
            # Chat history
            if st.session_state.chat_history:
                st.subheader("📋 Lịch sử hội thoại")
                
                # Display chat messages
                for i, (question, answer) in enumerate(st.session_state.chat_history, 1):
                    display_chat_message(question, answer, i)
                
                st.markdown("---")

            # Question input form
            st.subheader("❓ Đặt câu hỏi mới")
            
            with st.form("question_form", clear_on_submit=True):
                query = st.text_area(
                    "Nhập câu hỏi của bạn:",
                    height=100,
                    placeholder="Ví dụ: Tài liệu này nói về chủ đề gì?",
                    help="Đặt câu hỏi cụ thể về nội dung trong tài liệu PDF"
                )
                
                col1, col2 = st.columns([1, 5])
                
                with col1:
                    submit_button = st.form_submit_button("🚀 Gửi", type="primary", use_container_width=True)
                
                # Handle form submission
                if submit_button and query.strip():
                    with st.spinner("🤔 Đang tìm kiếm và phân tích..."):
                        try:
                            # Get answer from chatbot
                            answer = st.session_state.chatbot.ask(query.strip())
                            
                            # Add to chat history
                            st.session_state.chat_history.append((query.strip(), answer))
                            
                            # Display immediate response
                            st.success("✅ Đã có câu trả lời!")
                            display_chat_message(query.strip(), answer, len(st.session_state.chat_history))

                        except Exception as e:
                            st.error(f"❌ Lỗi khi xử lý câu hỏi: {str(e)}")
                            with st.expander("🔍 Chi tiết lỗi"):
                                st.code(traceback.format_exc())

                elif submit_button and not query.strip():
                    st.warning("⚠️ Vui lòng nhập câu hỏi trước khi gửi")

            # Example questions
            with st.expander("💡 Gợi ý câu hỏi"):
                st.markdown("""
                **Câu hỏi tổng quan:**
                - Tài liệu này nói về chủ đề gì?
                - Tóm tắt nội dung chính của tài liệu
                - Những điểm quan trọng nhất trong tài liệu là gì?

                **Câu hỏi chi tiết:**
                - Giải thích về [khái niệm/thuật ngữ cụ thể]
                - Có những phương pháp nào được đề cập?
                - Kết luận của tác giả về [vấn đề] là gì?

                **Câu hỏi phân tích:**
                - So sánh giữa A và B trong tài liệu
                - Ưu điểm và nhược điểm của phương pháp X?
                - Tác giả đưa ra bằng chứng gì để hỗ trợ quan điểm?
                """)

        else:
            st.info("⬆️ Vui lòng tải lên và xử lý file PDF ở tab 'Upload tài liệu' trước.")
            
            # Getting started guide
            st.markdown("""
            ### 🚀 Bắt đầu sử dụng
            
            1. **Nhập API Key** vào sidebar
            2. **Upload file PDF** ở tab "Upload tài liệu"
            3. **Nhấn "Xử lý tài liệu"** và đợi hoàn thành
            4. **Quay lại tab này** để bắt đầu chat
            
            ---
            
            ### ❓ Câu hỏi thường gặp
            
            **Q: Tại sao cần API Key?**  
            A: Để sử dụng Google Gemini AI cho việc phân tích và trả lời câu hỏi.
            
            **Q: File PDF của tôi có được lưu trữ không?**  
            A: Không, file chỉ xử lý tạm thời và không được lưu trữ lâu dài.
            
            **Q: Chatbot có thể trả lời câu hỏi ngoài tài liệu không?**  
            A: Không, chatbot chỉ trả lời dựa trên nội dung trong tài liệu PDF bạn upload.
            """)


if __name__ == "__main__":
    main()

