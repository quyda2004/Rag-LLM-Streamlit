import os
import tempfile
from typing import Optional, List
import logging

# PDF processing
import PyPDF2
import fitz  # PyMuPDF as fallback

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.schema import Document

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Chatbot:
    def __init__(self, pdf_path: str, google_api_key: str):
        """
        Initialize RAG chatbot with FAISS vector store
        
        Args:
            pdf_path: Path to PDF file
            google_api_key: Google Gemini API key
        """
        self.pdf_path = pdf_path
        self.google_api_key = google_api_key
        self.vectorstore = None
        self.qa_chain = None
        self.documents = []
        
        # Configure Google API
        os.environ["GOOGLE_API_KEY"] = google_api_key
        
        # Initialize components
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=google_api_key
        )
        
        # Use Gemini 1.5 Flash as requested
        self.llm = GoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=google_api_key,
            temperature=0.1
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", "! ", "? ", " "]
        )

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF using multiple methods for better compatibility
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        text_content = ""
        
        # Method 1: Try PyPDF2 first
        try:
            logger.info("Trying PyPDF2 for text extraction...")
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                logger.info(f"Total pages: {len(pdf_reader.pages)}")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_content += f"\n--- Page {page_num + 1} ---\n"
                            text_content += page_text + "\n"
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num + 1}: {e}")
                        continue
                        
            if text_content.strip():
                logger.info("Successfully extracted text using PyPDF2")
                return text_content
                
        except Exception as e:
            logger.warning(f"PyPDF2 failed: {e}")

        # Method 2: Try PyMuPDF as fallback
        try:
            logger.info("Trying PyMuPDF for text extraction...")
            doc = fitz.open(pdf_path)
            
            for page_num in range(doc.page_count):
                try:
                    page = doc[page_num]
                    page_text = page.get_text()
                    if page_text.strip():
                        text_content += f"\n--- Page {page_num + 1} ---\n"
                        text_content += page_text + "\n"
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num + 1} with PyMuPDF: {e}")
                    continue
                    
            doc.close()
            
            if text_content.strip():
                logger.info("Successfully extracted text using PyMuPDF")
                return text_content
                
        except Exception as e:
            logger.warning(f"PyMuPDF failed: {e}")

        # If both methods fail
        if not text_content.strip():
            raise Exception("Cannot extract text from PDF using any available method")
            
        return text_content

    def process_documents(self) -> bool:
        """
        Process PDF and create vector store
        
        Returns:
            Success status
        """
        try:
            logger.info("Starting document processing...")
            
            # Step 1: Extract text from PDF
            logger.info("Step 1: Extracting text from PDF...")
            text_content = self.extract_text_from_pdf(self.pdf_path)
            
            if not text_content.strip():
                raise Exception("No text content extracted from PDF")
                
            logger.info(f"Extracted {len(text_content)} characters")
            
            # Step 2: Split text into chunks
            logger.info("Step 2: Splitting text into chunks...")
            text_chunks = self.text_splitter.split_text(text_content)
            
            if not text_chunks:
                raise Exception("No text chunks created")
                
            logger.info(f"Created {len(text_chunks)} text chunks")
            
            # Convert to Document objects
            self.documents = [
                Document(
                    page_content=chunk,
                    metadata={"source": os.path.basename(self.pdf_path), "chunk_id": i}
                )
                for i, chunk in enumerate(text_chunks)
            ]
            
            # Step 3: Create vector store with FAISS
            logger.info("Step 3: Creating vector store with FAISS...")
            self.vectorstore = FAISS.from_documents(
                documents=self.documents,
                embedding=self.embeddings
            )
            
            logger.info("Vector store created successfully")
            
            # Step 4: Create QA chain
            logger.info("Step 4: Creating QA chain...")
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 4}
                ),
                return_source_documents=True,
                verbose=False
            )
            
            logger.info("QA chain created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in document processing: {e}")
            return False

    def reset(self, pdf_path: str, google_api_key: str) -> bool:
        """
        Reset chatbot with new PDF file
        
        Args:
            pdf_path: Path to new PDF file
            google_api_key: Google API key
            
        Returns:
            Success status
        """
        try:
            self.pdf_path = pdf_path
            self.google_api_key = google_api_key
            
            # Update API key
            os.environ["GOOGLE_API_KEY"] = google_api_key
            
            # Reinitialize components with new API key
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=google_api_key
            )
            
            # Use Gemini 1.5 Flash
            self.llm = GoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=google_api_key,
                temperature=0.1
            )
            
            # Process new document
            success = self.process_documents()
            
            if success:
                logger.info("Chatbot reset successfully")
            else:
                logger.error("Failed to reset chatbot")
                
            return success
            
        except Exception as e:
            logger.error(f"Error resetting chatbot: {e}")
            return False

    def ask(self, question: str) -> str:
        """
        Ask question to the chatbot
        
        Args:
            question: User question
            
        Returns:
            Answer from the chatbot
        """
        try:
            if not self.qa_chain:
                return "❌ Chatbot chưa được khởi tạo. Vui lòng tải PDF trước."
                
            if not question.strip():
                return "❓ Vui lòng nhập câu hỏi."
                
            logger.info(f"Processing question: {question[:100]}...")
            
            # Enhanced prompt for better Vietnamese responses
            enhanced_question = f"""
            Dựa trên nội dung tài liệu được cung cấp, hãy trả lời câu hỏi sau một cách chi tiết và chính xác:

            Câu hỏi: {question}

            Hướng dẫn trả lời:
            1. Chỉ sử dụng thông tin có trong tài liệu
            2. Trả lời bằng tiếng Việt
            3. Nếu không tìm thấy thông tin, hãy nói rõ
            4. Trích dẫn cụ thể nếu có thể
            5. Trình bày một cách logic và dễ hiểu

            Trả lời:
            """
            
            # Get response from QA chain
            result = self.qa_chain.invoke({"query": enhanced_question})
            
            answer = result.get("result", "Không thể tạo câu trả lời.")
            
            # Clean up the answer
            if "Trả lời:" in answer:
                answer = answer.split("Trả lời:")[-1].strip()
                
            logger.info("Question processed successfully")
            return answer
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing question: {error_msg}")
            
            # Return user-friendly error message
            if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                return "❌ Đã vượt quá giới hạn API. Vui lòng thử lại sau hoặc kiểm tra quota API key."
            elif "permission" in error_msg.lower() or "forbidden" in error_msg.lower():
                return "❌ Lỗi quyền truy cập API. Vui lòng kiểm tra API key."
            elif "not found" in error_msg.lower() or "404" in error_msg.lower():
                return "❌ Model không được hỗ trợ. Vui lòng cập nhật code với model mới."
            else:
                return f"❌ Lỗi xử lý câu hỏi: {error_msg}"

    def get_document_info(self) -> dict:
        """
        Get information about processed document
        
        Returns:
            Document information
        """
        if not self.documents:
            return {"status": "No document processed"}
            
        return {
            "total_chunks": len(self.documents),
            "pdf_path": os.path.basename(self.pdf_path),
            "has_vectorstore": self.vectorstore is not None,
            "has_qa_chain": self.qa_chain is not None
        }


# Test function
def test_chatbot():
    """Test function for the chatbot"""
    try:
        # This would be used for testing
        print("Chatbot module loaded successfully")
        return True
    except Exception as e:
        print(f"Error testing chatbot: {e}")
        return False


if __name__ == "__main__":
    test_chatbot()
