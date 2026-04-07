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
    A[PDF đầu vào] --> P2I[01_pdf_to_images.py\nPDF → PNG 300DPI]
    P2I --> RAW[Ảnh thô theo trang]

    %% VÒNG LẶP 1: PHÂN LOẠI TOÀN BỘ ẢNH THÔ
    RAW --> CNN1[02_page_intelligence - CNN\n03_eval_128_detect.ipynb\nPhân loại: 0/1/2/3/4]
    CNN1 --> BR1{Tách nhánh theo nhãn - vòng 1}

    BR1 -->|1| OK1[OK loại 1\nTrang đơn đúng hướng]

    %% Nhánh 2/3/4: lọc thủ công -> xoay
    BR1 -->|2/3/4| M234[Manual QA\nKiểm tra/sửa nhãn\nnhánh 2/3/4]
    M234 --> ROT1[04_rotated_images.py\nXoay 90/180/270 theo nhãn]
    ROT1 --> OK234[OK loại 2/3/4\nSau xoay lần 1]

    %% Nhánh 0: lật + cắt trước, rồi mới detect lại
    BR1 -->|0| Z0_RAW[Nhánh 0\nTrang đôi / cần tách]
    Z0_RAW --> M0A[Manual QA\nXác nhận nhánh 0\ntrước khi tách]
    M0A --> FLIP0[Pre-step\nLật ngang ảnh\nbắt buộc trước khi cắt]
    FLIP0 --> SPLIT[05_split_images.py\nCắt dọc giữa\nTách 2 trang]
    SPLIT --> Z0_NEW[Ảnh mới sau tách\n2 trang]

    %% Sau tách mới chạy CNN để detect hướng / nhãn
    Z0_NEW --> CNN2[02_page_intelligence - CNN\nDetect lại ảnh sau tách\nRa nhãn: 1/2/3/4]
    CNN2 --> BR2{Tách nhánh sau tách}

    BR2 -->|1| OK1_FROM0[OK loại 1\nTừ nhánh 0]

    BR2 -->|2/3/4| M0B[Manual QA\nKiểm tra/sửa nhãn\nnhánh 2/3/4 sau tách]
    M0B --> ROT2[04_rotated_images.py\nXoay lại nếu cần]
    ROT2 --> OK234_FROM0[OK loại 2/3/4\nTừ nhánh 0]

    %% GOM CUỐI
    OK1 --> COMB[06_combine_images_one_folder.py\nGom vào final_combined_all]
    OK234 --> COMB
    OK1_FROM0 --> COMB
    OK234_FROM0 --> COMB

    COMB --> OCR[03_ocr_and_text\nOCR và tổng hợp text]
    OCR --> OCR1[07_DEEPSEEKOCR.ipynb\nThực hiện OCR]
    OCR1 --> OCR2[08_tong_hop_tat_ca_text.ipynb\nTổng hợp text]

    OCR2 --> LLM[04_data_extraction\nTrích xuất dữ liệu bằng LLM]
    LLM --> HAIKU[09_get_data_haiku45.ipynb\nClaude Haiku]
    LLM --> GPT[10_get_data_gpt5.ipynb\nGPT-5]
    HAIKU --> MERGE[11_extract_data_from_2_file.ipynb\nTổng hợp nhiều nguồn]
    GPT --> MERGE
    MERGE --> FILL[12_get_data_personal_and_fill.ipynb\nXử lý dữ liệu cá nhân\nvà điền form]
    FILL --> OUT[Dữ liệu cấu trúc cuối cùng]

    EVAL[05_eval_data] --> SZIP[13_get_data_random_full_process.py\nLấy mẫu PDF từ ZIP]
    EVAL --> SLLM[14_get_data_random_LLM.py\nTạo PDF mẫu từ nội dung LLM]
```
