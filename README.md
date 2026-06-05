# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Đào Duy Quyền
**Nhóm:** Top 1 Zone D 
**Ngày:** 05/06/2026 

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> High cosine similarity biểu thị hai vector biểu diễn văn bản hướng về cùng một phía trong không gian đa chiều. Điều này có nghĩa là hai đoạn văn bản đó có độ tương đồng ngữ nghĩa rất cao, bất kể độ dài ngắn của chúng có khác nhau.

**Ví dụ HIGH similarity:**
- Sentence A: Cách hầm xương bò giúp nước dùng trong và ngọt tự nhiên.
- Sentence B: Mẹo nấu nước dùng xương bò thơm ngon, ngọt thanh và không đục.
- Tại sao tương đồng: Cả hai câu đều chia sẻ chung một mục đích hướng dẫn hầm xương bò nấu nước dùng ngon ngọt và trong trẻo, sử dụng nhiều từ đồng nghĩa.

**Ví dụ LOW similarity:**
- Sentence A: Cách làm bánh flan sữa tươi mềm mịn không bị rỗ.
- Sentence B: Cách chần xương bò để nấu nước dùng phở bò ngọt thanh.
- Tại sao khác: Hai câu nói về hai món ăn và quy trình hoàn toàn khác biệt (bánh ngọt flan vs chần xương bò cho món phở mặn), không có từ ngữ hay mối liên hệ ngữ nghĩa nào.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Vì cosine similarity chỉ đo góc giữa hai vector mà không phụ thuộc vào độ lớn (độ dài) của vector đó. Trong văn bản, tài liệu dài hơn sẽ có độ lớn vector lớn hơn nhiều tài liệu ngắn mặc dù cùng chung một chủ đề, do đó Euclidean distance sẽ cho khoảng cách lớn (coi là ít tương quan) trong khi Cosine similarity vẫn nhận diện chính xác.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* `num_chunks = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23`
> *Đáp án:* 23 chunks.

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> *Phép tính:* `num_chunks = ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25` chunks.
> *Ý nghĩa:* Số lượng chunk tăng từ 23 lên 25. Muốn tăng overlap nhiều hơn nhằm giữ được tính toàn vẹn ngữ nghĩa ở ranh giới giữa các chunk, đảm bảo thông tin quan trọng ở khu vực chuyển tiếp không bị đứt đoạn hoặc mất mát khi truy vấn.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Công thức nấu ăn và mẹo vặt ẩm thực Việt Nam (Vietnamese Culinary Recipes & Cooking Tips).

**Tại sao nhóm chọn domain này?**
> Nhóm chọn ẩm thực Việt Nam vì đây là chủ đề rất quen thuộc, phong phú, các tài liệu công thức nấu ăn có cấu trúc phân tầng rõ ràng (Nguyên liệu, Các bước làm, Lưu ý) giúp dễ kiểm nghiệm và so sánh hiệu quả của các giải pháp chunking. Ngoài ra, việc thiết kế metadata cho các món ăn (độ khó, bữa ăn, nguyên liệu) rất trực quan và thực tế.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | `pho_bo.md` | self_written | 996 | `title`, `category`, `cuisine`, `difficulty`, `meal_type`, `language`, `source` |
| 2 | `bun_rieu.md` | self_written | 981 | `title`, `category`, `cuisine`, `difficulty`, `meal_type`, `language`, `source` |
| 3 | `canh_chua_ca.md` | self_written | 920 | `title`, `category`, `cuisine`, `difficulty`, `meal_type`, `language`, `source` |
| 4 | `ga_chien_nuoc_mam.md` | self_written | 892 | `title`, `category`, `cuisine`, `difficulty`, `meal_type`, `language`, `source` |
| 5 | `rau_muong_xao_toi.md` | self_written | 839 | `title`, `category`, `cuisine`, `difficulty`, `meal_type`, `language`, `source` |
| 6 | `che_dau_xanh.md` | self_written | 894 | `title`, `category`, `cuisine`, `difficulty`, `meal_type`, `language`, `source` |
| 7 | `banh_flan.md` | self_written | 885 | `title`, `category`, `cuisine`, `difficulty`, `meal_type`, `language`, `source` |
| 8 | `meo_nau_nuoc_dung.md` | self_written | 943 | `title`, `category`, `cuisine`, `difficulty`, `meal_type`, `language`, `source` |
| 9 | `cach_so_che_nguyen_lieu.md` | self_written | 959 | `title`, `category`, `cuisine`, `difficulty`, `meal_type`, `language`, `source` |
| 10| `dinh_luong_gia_vi_co_ban.md`| self_written | 1043| `title`, `category`, `cuisine`, `difficulty`, `meal_type`, `language`, `source` |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| `category` | string | `"soup"`, `"dessert"`, `"cooking_tip"` | Phân loại loại bài viết để người dùng chỉ tìm trong công thức món súp hoặc mẹo vặt. |
| `difficulty` | string | `"easy"`, `"medium"` | Giúp lọc những món ăn dễ làm cho những người mới bắt đầu học nấu ăn. |
| `meal_type` | string | `"breakfast"`, `"lunch"`, `"dinner"` | Giúp người dùng lọc nhanh các món ăn phù hợp với từng bữa trong ngày. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên các tài liệu ẩm thực:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| Các tài liệu ẩm thực (.md) | FixedSizeChunker (`fixed_size`) | 39 | 262.1 | Trung bình (cắt chữ ở khoảng trắng nên câu bị đứt đoạn giữa chừng) |
| Các tài liệu ẩm thực (.md) | SentenceChunker (`by_sentences`) | 66 | 140.6 | Khá tốt (ngắt theo câu trọn vẹn, nhưng chunk hơi ngắn) |
| Các tài liệu ẩm thực (.md) | RecursiveChunker (`recursive`) | 35 | 265.8 | Tốt nhất (giữ nguyên cấu trúc các mục, đoạn văn liên mạch) |

### Strategy Của Tôi

**Loại:** `RecursiveChunker` (Chiến lược phân cắt đệ quy phân cấp)

**Mô tả cách hoạt động:**
> Chiến lược này duyệt qua một danh sách các ký tự phân tách theo độ ưu tiên giảm dần: `\n\n` (đoạn văn lớn), `\n` (dòng), `. ` (ranh giới câu), ` ` (khoảng trắng từ), `""` (ký tự đơn). Nếu khối văn bản dài vượt quá `chunk_size=400`, nó sẽ chia nhỏ theo separator phù hợp và đệ quy xuống các tầng dưới. Sau đó, nó gộp thông minh các phần liền kề để tạo thành chunk tiệm cận `chunk_size` mà không phá vỡ tính liên kết ngữ nghĩa.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Vì tài liệu công thức nấu ăn được viết theo cấu trúc khối rất chặt chẽ: danh sách các nguyên liệu cần chuẩn bị, hoặc các bước thực hiện tuần tự. Sử dụng `RecursiveChunker` đảm bảo một bước làm hoặc toàn bộ danh sách nguyên liệu không bị cắt đôi sang hai chunk khác nhau, giúp mô hình RAG lấy được thông tin đầy đủ nhất.

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| Các tài liệu ẩm thực | best baseline (SentenceChunker) | 66 | 140.6 | Khá vụn, đôi khi tìm ra câu hướng dẫn nhưng mất danh sách nguyên liệu bổ trợ |
| Các tài liệu ẩm thực | **của tôi (RecursiveChunker)** | 35 | 265.8 | Rất tốt, lấy được toàn bộ khối thông tin liền mạch, đầy đủ ngữ cảnh |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | Recursive Chunker (`chunk_size=400`) | 9/10 | Giữ nguyên vẹn cấu trúc các phần nấu ăn | Chunk có thể hơi dài nếu văn bản ít xuống dòng |
| Nguyễn Quang Khánh An | Fixed Size Chunker (`chunk_size=300`) | 7/10 | Số lượng chunk ổn định, dễ cấu hình | Các bước làm thường bị cắt làm đôi ở biên |
| Đào Duy Quyền | Sentence Chunker (`max_sentences=3`) | 8/10 | Giữ được câu hoàn chỉnh, tránh đứt từ | Thông tin bị chia vụn, khó gộp các nguyên liệu liên quan |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> `RecursiveChunker` là tốt nhất cho domain nấu ăn. Lý do là các bước nấu ăn và danh sách nguyên liệu cần được giữ nguyên vẹn cùng nhau để LLM có đủ ngữ cảnh trả lời chính xác, tránh việc nguyên liệu nằm ở chunk này nhưng định lượng lại nằm ở chunk khác.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Sử dụng biểu thức chính quy (regex) `r'(\. |\! |\? |\.\n)'` để chia văn bản thành các câu riêng biệt mà vẫn giữ nguyên các ký tự phân tách câu. Sau đó, tiến hành gộp tối đa `max_sentences_per_chunk` câu liền kề thành một chunk, loại bỏ các ký tự khoảng trắng thừa bằng phương thức `.strip()`.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Thuật toán đệ quy duyệt qua các ký tự phân tách theo thứ tự ưu tiên giảm dần. Base case là khi độ dài chuỗi nhỏ hơn `chunk_size` (trả về chính nó) hoặc khi hết ký tự phân tách thì chia theo độ dài ký tự cố định. Với mỗi separator được tìm thấy, văn bản được split và đệ quy xử lý các phần con quá lớn, sau đó gộp thông minh các phần nhỏ liền kề để không vượt quá kích thước quy định.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Đối với cơ chế in-memory, lưu trữ các dictionary chứa nội dung, metadata và vector biểu diễn (được sinh bởi `embedding_fn`). Đối với ChromaDB, lưu qua phương thức `add()` của collection. Khi tìm kiếm (`search`), truy vấn lấy ra các kết quả khớp nhất dựa trên độ tương đồng Cosine giữa vector của câu hỏi (query) và các vector được lưu trữ (bằng cách gọi helper `compute_similarity` hoặc ChromaDB's search query).

**`search_with_filter` + `delete_document`** — approach:
> Hỗ trợ lọc (filter) trước khi tính toán độ tương đồng (pre-filtering). Đối với in-memory, lọc các record có metadata khớp hoàn toàn với `metadata_filter` trước khi tính similarity. Đối với ChromaDB, truyền tham số `where` trực tiếp vào lệnh query. Phương thức `delete_document` thực hiện lọc bỏ phần tử in-memory dựa trên `doc_id` hoặc gọi `collection.delete(where={"doc_id": doc_id})` trên ChromaDB.

### KnowledgeBaseAgent

**`answer`** — approach:
> Tìm kiếm `top_k` chunk tương quan nhất từ knowledge base thông qua `EmbeddingStore.search()`. Sau đó, trích xuất nội dung của các chunk này, nối lại bằng ký tự xuống dòng để tạo nên một đoạn `context` thống nhất và nhúng trực tiếp đoạn context này cùng câu hỏi của người dùng vào cấu trúc prompt để gọi LLM sinh câu trả lời.

### Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.0.3, pluggy-1.6.0 -- C:\Python313\python.exe
cachedir: .pytest_cache
rootdir: D:\VinUni-AI20K\Day-07-Lab-Data-Foundations
plugins: anyio-4.11.0, langsmith-0.8.8
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 1.33s ==============================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Cách chần xương bò để nấu nước dùng phở bò ngọt thanh. | Mẹo hầm xương bò giúp nước dùng trong và ngọt tự nhiên. | high | 0.6549 | Đúng |
| 2 | Cách làm bánh flan sữa tươi mềm mịn không bị rỗ. | Công thức làm caramen (bánh flan) ngon tuyệt tại nhà. | high | 0.6348 | Đúng |
| 3 | Cách làm bánh flan sữa tươi mềm mịn không bị rỗ. | Cách chần xương bò để nấu nước dùng phở bò ngọt thanh. | low | 0.4615 | Đúng |
| 4 | Rửa sạch rau muống, nhặt bỏ lá úa và để ráo nước. | Nhặt rau muống, rửa nhiều lần với nước sạch rồi vớt ra. | high | 0.7382 | Đúng |
| 5 | Mẹo hầm xương bò giúp nước dùng trong và ngọt tự nhiên. | Hầm xương trong nồi áp suất giúp tiết kiệm nhiều thời gian. | high | 0.6390 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> So với mô hình cục bộ `all-MiniLM-L6-v2` (trong đó Cặp 3 bị đánh giá sai với điểm số khá cao `0.5768`), mô hình `openai/text-embedding-3-small` đã cải thiện rõ rệt và cho kết quả rất hợp lý. Cặp 3 (bánh flan và chần xương bò) giờ đây có điểm tương đồng thấp hẳn (`0.4615`) so với các cặp có cùng chủ đề như Cặp 2 (`0.6348`) và Cặp 1 (`0.6549`).
>
> Điều này cho thấy các mô hình nhúng tiên tiến hơn (như của OpenAI) có khả năng biểu diễn ngữ nghĩa vượt trội. Chúng không dễ bị đánh lừa bởi các yếu tố cấu trúc cú pháp bề mặt (như cấu trúc câu dạng công thức "Cách làm... không bị...", "Cách chần... để...") mà tập trung biểu diễn chiều sâu ngữ nghĩa của các thực thể cốt lõi trong câu (nguyên liệu món ăn, bối cảnh chế biến khác biệt giữa món ngọt và món mặn).


---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Cách làm phở bò truyền thống cần những nguyên liệu gì? | Bánh phở, thịt bò (tái/chín), xương bò hầm, hành tây, hành tím, gừng, gia vị (thảo quả, hoa hồi, quế). |
| 2 | Làm thế nào để nước dùng trong và không bị đục? | Chần xương, rửa sạch xương sau chần, hầm lửa nhỏ, vớt bọt liên tục và không đậy nắp vung khi hầm xương. |
| 3 | Cách nấu chè đậu xanh nước cốt dừa thơm ngon | Đậu xanh bóc vỏ, đường (cát/phèn), nước cốt dừa, bột năng, muối. Ninh mềm đậu, thêm đường và bột năng tạo sánh, rưới cốt dừa lên. |
| 4 | Lọc riêng thịt và xương heo như thế nào cho đúng cách? | Cần sơ chế sạch thịt heo dưới vòi nước chảy, ngâm chần qua nước sôi để loại bỏ cặn bẩn, dùng dao sắc tách dọc theo thớ và khớp xương. |
| 5 | Món canh (soup) nào có độ khó dễ (easy) cho bữa trưa (lunch)? | Món Canh chua cá (chuẩn bị me chua, cá tươi, dứa, cà chua, giá đỗ, dọc mùng). |

### Kết Quả Của Tôi

Dưới đây là kết quả chạy thực tế với chiến lược **RECURSIVE** (chọn của tôi làm chiến lược chính):

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Cách làm phở bò truyền thống cần những nguyên liệu gì? | ## Nguyên liệu - Bánh phở - Thịt bò - Xương bò... (từ `pho_bo_chunk_1.md`) | 0.636 | Có | Trả lời tự động dựa trên ngữ cảnh công thức phở bò |
| 2 | Làm thế nào để nước dùng trong và không bị đục? | ## Lưu ý - Không đậy nắp quá kín khi hầm nước dùng... (từ `meo_nau_nuoc_dung_chunk_2.md`) | 0.623 | Có | Trả lời tự động dựa trên mẹo hầm xương trong |
| 3 | Cách nấu chè đậu xanh nước cốt dừa thơm ngon | --- title: "Chè đậu xanh" category: "dessert"... (từ `che_dau_xanh_chunk_0.md`) | 0.649 | Có | Trả lời tự động dựa trên công thức nấu chè đậu xanh |
| 4 | Lọc riêng thịt và xương heo như thế nào cho đúng cách? | ## Nguyên liệu - Xương heo hoặc xương bò... (từ `meo_nau_nuoc_dung_chunk_1.md`) | 0.635 | Có | Trả lời tự động dựa trên hướng dẫn sơ chế nguyên liệu |
| 5 | Món canh (soup) nào có độ khó dễ (easy) cho bữa trưa (lunch)? | --- title: "Canh chua cá" category: "soup" cuisine: "vietnamese"... (từ `canh_chua_ca_chunk_0.md`) | 0.583 | Có | Trả lời tự động dựa trên ngữ cảnh canh chua cá |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Tôi học được tầm quan trọng của việc tối ưu hóa kích thước `overlap`. Một thành viên trong nhóm nhận ra rằng nếu đặt overlap quá nhỏ, các bước thực hiện công thức nấu ăn dài sẽ bị đứt mạch thông tin ở biên, ảnh hưởng lớn đến chất lượng trả lời của Agent.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Nhóm khác đã sử dụng metadata phong phú hơn (như gán thêm `main_ingredients` dưới dạng mảng). Điều này giúp họ thực hiện được các bộ lọc nâng cao như tìm món ăn theo nguyên liệu sẵn có trong tủ lạnh, giúp nâng cao tính thực tế của ứng dụng.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ thiết kế thêm một tầng phân tích ngữ pháp để chunking theo từng "Section" thay vì chỉ dựa vào độ dài ký tự của `RecursiveChunker`. Cách này sẽ giúp giữ nguyên vẹn toàn bộ công thức của một món ăn trong cùng một ngữ cảnh tìm kiếm.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân |  5 / 5 |
| Document selection | Nhóm | 9 / 10 |
| Chunking strategy | Nhóm | 13 / 15 |
| My approach | Cá nhân | 8 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 8 / 10 |
| Core implementation (tests) | Cá nhân | 27 / 30 |
| Demo | Nhóm | 4 / 5 |
| **Tổng** | | **89 / 100** |