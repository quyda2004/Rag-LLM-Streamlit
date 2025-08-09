import os
import re
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
# from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI
from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings
from langchain.prompts import PromptTemplate


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

    def read_pdf(self):
        """Đọc nội dung từ file PDF"""
        with open(self.pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            print(f"Tổng số trang: {num_pages}")

            text = ""
            for i in range(num_pages):
                page = reader.pages[i]
                text += page.extract_text() + "\n"

            self.text = text
            print("Đọc PDF xong!")

    def clean_text(self):
        """Làm sạch nội dung văn bản"""
        text = self.text.replace("\n", " ")
        text = re.sub(r'\s+', ' ', text)
        text = text.lower().strip()
        self.cleaned_text = text
        print("Làm sạch văn bản xong!")

    def split_text(self, chunk_size=500, chunk_overlap=80):
        """Chia văn bản thành nhiều đoạn nhỏ"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.chunks = splitter.split_text(self.cleaned_text)
        print(f"Số đoạn sau khi chia: {len(self.chunks)}")

    def create_vectorstore(self):
        """Tạo FAISS vector store từ các chunk"""
        embeddings = self.SentenceTransformerEmbeddings(model_name=self.embedding_model)
        self.vectorstore = FAISS.from_texts(self.chunks, embeddings)
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        print("Tạo vector store bằng FAISS thành công!")

    def init_llm(self):
        """Khởi tạo LLM Gemini"""
        os.environ["GOOGLE_API_KEY"] = self.google_api_key
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.2,
            convert_system_message_to_human=True
        )
        print("Khởi tạo LLM Gemini thành công!")

    def set_prompt(self):
        """Định nghĩa prompt template"""
        template = """
        Bạn là một trợ lý AI thông minh. Hãy trả lời câu hỏi dựa trên ngữ cảnh dưới đây:

        Ngữ cảnh:
        {context}

        Câu hỏi:
        {question}

        Yêu cầu:
        - Trả lời rõ ràng, dễ hiểu, súc tích.
        - Nếu không có thông tin trong ngữ cảnh, trả lời: 'Xin lỗi, tôi không tìm thấy thông tin.'
        """
        self.prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        print("Prompt template đã được thiết lập!")

    def build_qa_chain(self):
        """Tạo RetrievalQA chain với Prompt"""
        if not self.llm or not self.retriever or not self.prompt:
            raise ValueError("Cần khởi tạo LLM, Retriever và Prompt trước.")

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.retriever,
            chain_type="stuff",
            chain_type_kwargs={"prompt": self.prompt}
        )
        print("Tạo QA chain với prompt xong!")

    def ask(self, query):
        """Đặt câu hỏi và trả về câu trả lời"""
        if not self.qa_chain:
            raise ValueError("QA Chain chưa được khởi tạo.")
        return self.qa_chain.run(query)

    def reset(self, pdf_path, google_api_key):
        """Tạo lại pipeline khi upload file mới hoặc đổi API Key"""
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

        self.read_pdf()
        self.clean_text()
        self.split_text()
        self.create_vectorstore()
        self.init_llm()
        self.set_prompt()
        self.build_qa_chain()
