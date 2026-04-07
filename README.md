LINK CỦA DỰ ÁN: [Link](https://rag-llm-app-6ot7kxx9onfu9p5hizqmab.streamlit.app/)

#  RAG Chatbot - PDF Q&A

**Mô tả ngắn:**  
Ứng dụng web đơn giản bằng **Streamlit** cho phép người dùng **tải lên file PDF**, hệ thống sẽ **trích xuất văn bản**, **tạo vector database (FAISS)** bằng embedding của Google Generative AI, và dùng **RAG (Retrieval-Augmented Generation)** để trả lời câu hỏi dựa trên nội dung PDF.

---

##  Mục tiêu dự án
- Cho phép người dùng nhanh chóng biến một tài liệu PDF thành một **chatbot Q&A**.
- Trả lời trực tiếp **dựa trên nội dung trong file** (không suy đoán ngoài tài liệu).
- Hỗ trợ tiếng Việt (prompt đã tối ưu cho tiếng Việt).
- Dễ deploy (Streamlit) và dễ mở rộng.

---

##  Tính năng chính
- Upload file PDF từ giao diện web.
- Trích xuất văn bản dùng **PyPDF2**.
- Chia nhỏ văn bản (chunking) bằng **RecursiveCharacterTextSplitter**.
- Tạo embedding với **GoogleGenerativeAIEmbeddings**.
- Lưu vector bằng **FAISS** và truy vấn bằng **RetrievalQA** (LangChain).
- Sinh trả lời bằng **Google Gemini (gemini-1.5-flash)**.
- Giao diện Streamlit: upload, tiến trình, hiển thị lịch sử chat, xử lý lỗi.


```mermaid
flowchart TD
    A[Dữ liệu PDF đầu vào]

    subgraph P["01_image_pipeline & 02_page_intelligence: PDF → Ảnh chuẩn hóa"]
        direction TD

        A --> D1[01_pdf_to_images.py\nPDF sang ảnh PNG 300DPI]

        D1 --> C1[02_page_intelligence\nCNN phân loại trang]
        C1 --> C1N[03_eval_128_detect.ipynb\nPhân loại 0/1/2/3/4]

        C1N --> M1[Thủ công: kiểm tra và sửa nhãn\nlọc 0,2,3,4]
        M1 --> R1[04_rotated_images.py\nXoay ảnh 90/180/270 độ]

        R1 --> S{Tách theo nhãn sau vòng 1}
        S -->|Nhãn 1| F1[Ảnh OK loại 1\ntrang đơn đúng hướng]
        S -->|Nhãn 2/3/4| F234[Ảnh OK loại 2/3/4\nđã xoay xong]
        S -->|Nhãn 0| Z0[Nhánh loại 0\ntrang đôi / cần tách]

        Z0 --> C2[02_page_intelligence\nCNN phân loại lại ảnh loại 0]
        C2 --> M2[Thủ công: kiểm tra lại\ntrước khi tách]

        M2 --> FLIP[Tiền xử lý: lật ngang ảnh\nyêu cầu trước khi cắt]
        FLIP --> SP[05_split_images.py\nChia đôi ảnh theo chiều dọc]
        SP --> Z0OUT[Ảnh sau tách từ nhánh 0]

        Z0OUT --> M3[Thủ công: lọc lại ảnh sau tách\ngán nhãn 1/2/3/4]
        M3 --> R2[04_rotated_images.py\nXoay lại nếu cần]
        R2 --> F0OK[Ảnh OK sau xử lý nhánh 0]

        F1 --> D5[06_combine_images_one_folder.py\nGom tất cả ảnh đã xử lý]
        F234 --> D5
        F0OK --> D5
    end

    D5 --> E[03_ocr_and_text\nOCR và Tổng hợp Text]
    E --> E1[07_DEEPSEEKOCR.ipynb\nThực hiện OCR]
    E1 --> E2[08_tong_hop_tat_ca_text.ipynb\nTổng hợp text]

    E2 --> F2[04_data_extraction\nTrích xuất dữ liệu bằng LLM]
    F2 --> FHaiku[09_get_data_haiku45.ipynb\nTrích xuất bằng Claude Haiku]
    F2 --> FGPT[10_get_data_gpt5.ipynb\nTrích xuất bằng GPT-5]
    FHaiku --> FMerge[11_extract_data_from_2_file.ipynb\nTổng hợp từ nhiều nguồn]
    FGPT --> FMerge
    FMerge --> FFill[12_get_data_personal_and_fill.ipynb\nXử lý dữ liệu cá nhân và điền form]
    FFill --> G[Dữ liệu cấu trúc cuối cùng]

    H[05_eval_data] --> B1[13_get_data_random_full_process.py\nLấy mẫu PDF gốc từ ZIP]
    H --> B2[14_get_data_random_LLM.py\nTạo PDF mẫu từ nội dung LLM]
```
