import os
import re
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI
from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings
from langchain.prompts import PromptTemplate
import tempfile
import shutil


class Chatbot:
    class SentenceTransformerEmbeddings(Embeddings):
        """Wrapper tích hợp SentenceTransformer vào LangChain"""

        def __init__(self, model_name="all-MiniLM-L6-v2"):
            self.model = SentenceTransformer(model_name)

        def embed_documents(self, texts):
            return self.model.encode(texts).tolist()

        def embed_query(self, text):
            return self.model.encode([text])[0].tolist()

    def __init__(self, pdf_path, google_api_key, embedding_model="all-MiniLM-L6-v2"):
        self.pdf_path = pdf_path
        self.google_api_key = google_api_key
        self.embedding_model = embedding_model
        self.text = ""
        self.cleaned_text = ""
        self.chunks = []
        self.vectorstore = None
        self.retriever = None
        self.llm = None
        self.qa_chain = None
        self.prompt = None
        self.temp_dir = None

    def read_pdf(self):
        """Đọc nội dung từ file PDF với error handling"""
        try:
            with open(self.pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_pages = len(reader.pages)
                print(f"Tổng số trang: {num_pages}")

                text = ""
                for i in range(num_pages):
                    page = reader.pages[i]
                    page_text = page.extract_text()
                    if page_text:  # Check if text was extracted
                        text += page_text + "\n"

                if not text.strip():
                    raise ValueError("Không thể trích xuất văn bản từ PDF")

                self.text = text
                print("Đọc PDF xong!")
                return True
        except Exception as e:
            print(f"Lỗi khi đọc PDF: {str(e)}")
            return False

    def clean_text(self):
        """Làm sạch nội dung văn bản với cải tiến"""
        if not self.text:
            return False

        try:
            # Remove extra whitespace and normalize
            text = self.text.replace("\n", " ")
            text = re.sub(r'\s+', ' ', text)

            # Remove special characters but keep Vietnamese characters
            text = re.sub(r'[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđĐ]', ' ', text)
            text = re.sub(r'\s+', ' ', text)

            # Keep original case for better context
            text = text.strip()
            self.cleaned_text = text
            print("Làm sạch văn bản xong!")
            return True
        except Exception as e:
            print(f"Lỗi khi làm sạch văn bản: {str(e)}")
            return False

    def split_text(self, chunk_size=1000, chunk_overlap=200):
        """Chia văn bản thành nhiều đoạn nhỏ với cải tiến"""
        if not self.cleaned_text:
            return False

        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ".", "!", "?", " ", ""]
            )
            self.chunks = splitter.split_text(self.cleaned_text)

            # Filter out very short chunks
            self.chunks = [chunk for chunk in self.chunks if len(chunk.strip()) > 50]

            print(f"Số đoạn sau khi chia: {len(self.chunks)}")
            return len(self.chunks) > 0
        except Exception as e:
            print(f"Lỗi khi chia văn bản: {str(e)}")
            return False

    def create_vectorstore(self):
        """Tạo Chroma vector store thay thế FAISS"""
        if not self.chunks:
            return False

        try:
            # Create temporary directory for Chroma
            self.temp_dir = tempfile.mkdtemp()

            embeddings = self.SentenceTransformerEmbeddings(model_name=self.embedding_model)

            # Use Chroma instead of FAISS
            self.vectorstore = Chroma.from_texts(
                texts=self.chunks,
                embedding=embeddings,
                persist_directory=self.temp_dir
            )

            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )

            print("Tạo vector store bằng Chroma thành công!")
            return True
        except Exception as e:
            print(f"Lỗi khi tạo vector store: {str(e)}")
            return False

    def init_llm(self):
        """Khởi tạo LLM Gemini với error handling"""
        try:
            if not self.google_api_key or self.google_api_key == "YOUR_DEFAULT_GOOGLE_API_KEY":
                raise ValueError("Cần cung cấp Google API Key hợp lệ")

            os.environ["GOOGLE_API_KEY"] = self.google_api_key
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.3,
                convert_system_message_to_human=True
            )
            print("Khởi tạo LLM Gemini thành công!")
            return True
        except Exception as e:
            print(f"Lỗi khi khởi tạo LLM: {str(e)}")
            return False

    def set_prompt(self):
        """Định nghĩa prompt template cải tiến"""
        template = """
        Bạn là một trợ lý AI thông minh và hữu ích. Hãy phân tích kỹ ngữ cảnh được cung cấp và trả lời câu hỏi một cách chính xác.

        NGỮ CẢNH:
        {context}

        CÂU HỎI: {question}

        HƯỚNG DẪN:
        1. Đọc kỹ ngữ cảnh và tìm thông tin liên quan đến câu hỏi
        2. Trả lời bằng tiếng Việt, rõ ràng và chi tiết
        3. Nếu thông tin không đầy đủ, hãy nói rõ phần nào chưa có thông tin
        4. Trích dẫn thông tin từ ngữ cảnh khi có thể
        5. Nếu không tìm thấy thông tin trong ngữ cảnh, trả lời: "Tôi không tìm thấy thông tin về vấn đề này trong tài liệu được cung cấp."

        TRẢ LỜI:
        """

        self.prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        print("Prompt template đã được thiết lập!")
        return True

    def build_qa_chain(self):
        """Tạo RetrievalQA chain với error handling"""
        if not all([self.llm, self.retriever, self.prompt]):
            print("Thiếu thành phần để tạo QA chain")
            return False

        try:
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                retriever=self.retriever,
                chain_type="stuff",
                chain_type_kwargs={"prompt": self.prompt},
                return_source_documents=False
            )
            print("Tạo QA chain với prompt xong!")
            return True
        except Exception as e:
            print(f"Lỗi khi tạo QA chain: {str(e)}")
            return False

    def ask(self, query):
        """Đặt câu hỏi và trả về câu trả lời với error handling"""
        if not self.qa_chain:
            return "Lỗi: QA Chain chưa được khởi tạo."

        if not query or not query.strip():
            return "Vui lòng nhập câu hỏi."

        try:
            response = self.qa_chain.run(query.strip())
            return response
        except Exception as e:
            print(f"Lỗi khi xử lý câu hỏi: {str(e)}")
            return f"Xin lỗi, đã có lỗi xảy ra khi xử lý câu hỏi: {str(e)}"

    def reset(self, pdf_path, google_api_key):
        """Tạo lại pipeline khi upload file mới hoặc đổi API Key"""
        # Clean up old resources
        self.cleanup()

        # Reset all attributes
        self.pdf_path = pdf_path
        self.google_api_key = google_api_key
        self.text = ""
        self.cleaned_text = ""
        self.chunks = []
        self.vectorstore = None
        self.retriever = None
        self.llm = None
        self.qa_chain = None
        self.prompt = None

        # Execute pipeline
        try:
            steps = [
                ("Đọc PDF", self.read_pdf),
                ("Làm sạch văn bản", self.clean_text),
                ("Chia văn bản", self.split_text),
                ("Tạo vector store", self.create_vectorstore),
                ("Khởi tạo LLM", self.init_llm),
                ("Thiết lập prompt", self.set_prompt),
                ("Tạo QA chain", self.build_qa_chain)
            ]

            for step_name, step_func in steps:
                print(f"Đang thực hiện: {step_name}...")
                if not step_func():
                    raise Exception(f"Thất bại ở bước: {step_name}")

            print("Hoàn thành khởi tạo chatbot!")
            return True

        except Exception as e:
            print(f"Lỗi trong quá trình khởi tạo: {str(e)}")
            self.cleanup()
            return False

    def cleanup(self):
        """Dọn dẹp tài nguyên"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Lỗi khi dọn dẹp thư mục tạm: {str(e)}")

    def __del__(self):
        """Destructor để dọn dẹp tài nguyên"""
        self.cleanup()
