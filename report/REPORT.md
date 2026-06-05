# Bao Cao Lab 7: Embedding & Vector Store

**Ho ten:** Dao Duy Quyen
**Nhom:** Nhom
**Ngay:** 05/06/2026

---

## 1. Warm-up (5 diem)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghia la gi?**

Hai vector co high cosine similarity khi chung cung huong hoac gan cung huong trong khong gian embedding. Voi text, dieu do thuong nghia la hai cau co noi dung hoac ngu nghia gan nhau.

**Vi du HIGH similarity:**
- Sentence A: `Python is a popular programming language.`
- Sentence B: `Python is a widely used programming language.`
- Tai sao tuong dong: Ca hai cung noi ve Python va deu mo ta no la ngon ngu lap trinh pho bien.

**Vi du LOW similarity:**
- Sentence A: `The server is down again.`
- Sentence B: `I like to eat banana pancakes.`
- Tai sao khac: Hai cau noi ve hai chu de hoan toan khong lien quan.

**Tai sao cosine similarity duoc uu tien hon Euclidean distance cho text embeddings?**

Cosine similarity tap trung vao huong cua vector, nen phu hop hon cho embedding text noi y nghia quan trong hon do lon. Euclidean distance de bi anh huong boi do dai vector, trong khi cosine thuong phan anh muc do giong nhau ve ngu nghia tot hon.

### Chunking Math (Ex 1.2)

**Document 10,000 ky tu, `chunk_size=500`, `overlap=50`. Bao nhieu chunks?**

Theo cong thuc:

`num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap))`

Thay so:

`ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23`

**Dap an:** 23 chunks

**Neu overlap tang len 100, chunk count thay doi the nao? Tai sao muon overlap nhieu hon?**

Khi overlap tang len 100:

`ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25`

So chunk tang len. Overlap nhieu hon giup giu ngu canh giua cac chunk lien tiep tot hon, tranh viec y bi cat mat o bien chunk.

---

## 2. Document Selection - Nhom (10 diem)

### Domain & Ly Do Chon

**Domain:** Cong thuc nau an

**Tai sao nhom chon domain nay?**

Nhom chon chu de cong thuc nau an vi tai lieu co cau truc ro rang, de chia thanh cac phan nhu nguyen lieu, cach lam va luu y. Domain nay cung de tao benchmark queries thuc te nhu tim mon an theo loai, do kho hoac nguyen lieu.

### Data Inventory

| # | Ten tai lieu | Nguon | So ky tu | Metadata da gan |
|---|--------------|-------|----------|-----------------|
| 1 | `pho_bo.md` | Tu viet lai tu tai lieu cong khai | ~1800 | `category=main_dish`, `cuisine=vietnamese`, `difficulty=medium`, `language=vi`, `source=self_written` |
| 2 | `bun_rieu.md` | Tu viet lai tu tai lieu cong khai | ~1600 | `category=soup`, `cuisine=vietnamese`, `difficulty=medium`, `language=vi`, `source=self_written` |
| 3 | `ga_chien_nuoc_mam.md` | Tu viet lai tu tai lieu cong khai | ~1400 | `category=main_dish`, `cuisine=vietnamese`, `difficulty=easy`, `language=vi`, `source=self_written` |
| 4 | `canh_chua_ca.md` | Tu viet lai tu tai lieu cong khai | ~1500 | `category=soup`, `cuisine=vietnamese`, `difficulty=easy`, `language=vi`, `source=self_written` |
| 5 | `che_dau_xanh.md` | Tu viet lai tu tai lieu cong khai | ~1300 | `category=dessert`, `cuisine=vietnamese`, `difficulty=easy`, `language=vi`, `source=self_written` |
| 6 | `banh_flan.md` | Tu viet lai tu tai lieu cong khai | ~1200 | `category=dessert`, `cuisine=western`, `difficulty=easy`, `language=vi`, `source=self_written` |
| 7 | `meo_nau_nuoc_dung.md` | Tu viet lai tu tai lieu cong khai | ~1100 | `category=cooking_tips`, `cuisine=vietnamese`, `difficulty=medium`, `language=vi`, `source=self_written` |
| 8 | `so_che_nguyen_lieu.md` | Tu viet lai tu tai lieu cong khai | ~1000 | `category=cooking_tips`, `cuisine=vietnamese`, `difficulty=easy`, `language=vi`, `source=self_written` |

### Metadata Schema

| Truong metadata | Kieu | Vi du gia tri | Tai sao huu ich cho retrieval? |
|----------------|------|---------------|-------------------------------|
| `category` | string | `dessert` | Giup loc theo loai mon khi nguoi dung hoi mon trang mieng, mon chinh hoac meo nau an. |
| `cuisine` | string | `vietnamese` | Giup phan biet mon Viet voi mon Tay hoac mon chau A khac. |
| `difficulty` | string | `easy` | Giup loc mon de hoac nang cao theo nhu cau nguoi dung. |
| `language` | string | `vi` | Giup loai bo tai lieu sai ngon ngu khi benchmark hoac khi query tieng Viet. |
| `source` | string | `self_written` | Giup biet tai lieu lay tu dau va de quan ly chat luong nguon. |

---

## 3. Chunking Strategy - Ca nhan chon, nhom so sanh (15 diem)

### Baseline Analysis

Toi dung `ChunkingStrategyComparator().compare()` tren mot tai lieu mau de so sanh 3 cach chunking:

| Tai lieu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|----------|----------|-------------|------------|-------------------|
| Pho bo | FixedSizeChunker (`fixed_size`) | 2 | 347.0 | Khong tot bang vi co the cat giua y |
| Pho bo | SentenceChunker (`by_sentences`) | 5 | 129.6 | Tot hon cho cau ngan, nhung chunk co the manh |
| Pho bo | RecursiveChunker (`recursive`) | 3 | 216.0 | Tot nhat trong 3 cach vi uu tien cat theo cau truc |

### Strategy Cua Toi

**Loai:** `RecursiveChunker`

**Mo ta cach hoat dong:**
Toi chon `RecursiveChunker` cho bo du lieu cong thuc nau an vi tai lieu nay co cau truc ro rang theo tung phan nhu mo ta, nguyen lieu, cach lam va luu y. Strategy se uu tien tach theo doan va xuong dong truoc, sau do moi tach nho hon neu can. Nhu vay cac chunk van giu duoc ngu canh va de retrieve hon.

**Tai sao toi chon strategy nay cho domain nhom?**
Cong thuc nau an thuong co tieu de ro, moi mon co cac phan lap lai nhu `Nguyen lieu` va `Cach lam`. Recursive chunking giup giu duoc y tron ven hon so voi fixed-size, dong thoi khong qua manh nhu sentence chunking.

**Code snippet (neu custom):**
```python
# Using the built-in RecursiveChunker from src/chunking.py
chunker = RecursiveChunker(chunk_size=400)
```

### So Sanh: Strategy Cua Toi vs Baseline

| Tai lieu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|----------|----------|-------------|------------|--------------------|
| Pho bo | best baseline: FixedSizeChunker | 2 | 347.0 | On, nhung co the cat giua y |
| Pho bo | **cua toi: RecursiveChunker** | 3 | 216.0 | Tot hon vi chunk gon hon va giu cau truc |

### So Sanh Voi Thanh Vien Khac

| Thanh vien | Strategy | Retrieval Score (/10) | Diem manh | Diem yeu |
|-----------|----------|----------------------|-----------|----------|
| Toi | RecursiveChunker | 8 | Giu cau truc tai lieu tot | Can metadata filter de tang precision |
| Ban A | SentenceChunker | 6 | Chunk trong, de doc | De bi manh khi document dai |
| Ban B | FixedSizeChunker | 5 | Don gian, de implement | Cat mat y, retrieve kem hon |

**Strategy nao tot nhat cho domain nay? Tai sao?**
RecursiveChunker la tot nhat cho dataset cong thuc nau an nay vi no giu duoc cau truc tu nhien cua tai lieu va van tranh chunk qua dai. Khi ket hop voi metadata filter, no cho ket qua retrieve on dinh hon cac cach con lai.

---

## 4. My Approach - Ca nhan (10 diem)

### `SentenceChunker.chunk`

Toi tach van ban thanh cac cau bang regex dua tren dau ket thuc cau nhu `.`, `!`, `?`, roi gom tung nhom toi da `max_sentences_per_chunk` cau thanh mot chunk. Cach nay giu cho moi chunk co ranh gioi ngu nghia tu nhien hon so voi cat theo ky tu.

### `RecursiveChunker.chunk` / `_split`

Toi trien khai theo kieu de quy: thu tach theo cac separator co do uu tien cao truoc nhu doan moi, xuong dong, roi moi den khoang trang. Neu van con doan qua dai va khong con separator huu ich, toi fallback ve `FixedSizeChunker` de dam bao luon tra ve chunk hop le.

### `EmbeddingStore`

`add_documents` chuyen moi `Document` thanh mot record chuan hoa gom `id`, `content`, `metadata` va `embedding`, roi luu vao bo nho. `search` embed query mot lan, tinh diem bang dot product voi toan bo embeddings da luu, sau do sort giam dan theo score va tra ve `top_k`.

### `search_with_filter` va `delete_document`

Toi loc truoc theo metadata, roi moi search tren tap da loc de tranh keo nhieu tu document khong dung dieu kien. `delete_document` xoa toan bo record co `metadata["doc_id"]` trung voi `doc_id` can xoa va tra ve `True` neu co thay doi.

### `KnowledgeBaseAgent`

`answer` lay top-k chunk lien quan tu store, ghep chung thanh context, roi tao prompt co cau truc ro rang: question + context + chi dan tra loi. Sau do toi goi `llm_fn(prompt)` de sinh cau tra loi cuoi cung.

### Test Results

```text
python -m pytest tests -v
42 passed, 1 warning in 0.18s
```

**So tests pass:** 42 / 42

---

## 5. Similarity Predictions - Ca nhan (5 diem)

Toi dung `_mock_embed` de tao embedding cho tung cau, sau do goi `compute_similarity()` de lay ket qua that.

| Pair | Sentence A | Sentence B | Du doan | Actual Score | Dung? |
|------|------------|------------|---------|--------------|-------|
| 1 | `Python is a programming language.` | `Python is a popular programming language.` | high | 0.1412 | Dung huong |
| 2 | `The cat sits on the mat.` | `A cat is resting on the rug.` | high | 0.1987 | Dung huong |
| 3 | `The server is down again.` | `I like to eat banana pancakes.` | low | -0.0178 | Dung huong |
| 4 | `Machine learning uses data.` | `Data helps machine learning models improve.` | high | 0.1683 | Dung huong |
| 5 | `Open the door.` | `Please close the window.` | low | -0.0465 | Dung huong |

**Ket qua bat ngo nhat? Dieu nay noi gi ve embeddings?**

Dieu bat ngo la cac cau co ve cung chu de van khong cho diem that su cao. Ly do la `_mock_embed` chi la embedding mo phong, khong hieu ngu nghia that nhu model embedding thuc te. Vi vay diem similarity o day chi dung de kiem thu pipeline va cong thuc, khong phai de danh gia chat luong semantic that.

---

## 6. Results - Ca nhan (10 diem)

### Benchmark Queries & Gold Answers

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Mon nao la mon trang mieng va dung dau xanh? | Che dau xanh |
| 2 | Can bao nhieu buoc de lam Pho bo? | 7 buoc |
| 3 | Mon nao co nguyen lieu chinh la ca? | Canh chua ca |
| 4 | Tai lieu nao thuoc category cooking_tip? | Meo nau nuoc dung; Cach so che nguyen lieu |
| 5 | Mon nao phu hop cho bua sang? | Pho bo |

### Ket Qua Cua Toi

| # | Query | Top-1 Retrieved Chunk (tom tat) | Score | Relevant? | Agent Answer (tom tat) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Mon nao la mon trang mieng va dung dau xanh? | Che dau xanh | 0.2033 | Co | Che dau xanh |
| 2 | Can bao nhieu buoc de lam Pho bo? | Pho bo | 0.1384 | Co | Pho bo |
| 3 | Mon nao co nguyen lieu chinh la ca? | Canh chua ca | 0.2463 | Co | Canh chua ca |
| 4 | Tai lieu nao thuoc category cooking_tip? | Meo nau nuoc dung | -0.0558 | Co khi dung filter | Meo nau nuoc dung; Cach so che nguyen lieu |
| 5 | Mon nao phu hop cho bua sang? | Meo nau nuoc dung | 0.2548 | Khong trong top-3 | Pho bo neu loc theo `meal_type=breakfast` |

**Bao nhieu queries tra ve chunk relevant trong top-3?** 4 / 5

**Ghi chu ngan:**
- Query 4 cho thay metadata filter giup precision tot hon ro rang.
- Query 5 la failure case cua unfiltered search: top-3 khong chua Pho bo du query hoi ve bua sang.

---

## 7. What I Learned (5 diem - Demo)

**Dieu hay nhat toi hoc duoc tu nhom khac trong Phase 2:**
Toi thay cung mot bo tai lieu nhung chi can doi strategy hoac metadata filter la ket qua retrieval da thay doi ro rang. Dieu nay cho thay data strategy quan trong khong kem model.

**Dieu hay nhat toi hoc duoc tu nhom khac (qua demo):**
Toi hoc duoc rang can phan biet giua unfiltered search va metadata-filtered search. Khi query co ngu canh ro nhu bua sang hoac trang mieng, filter giup tranh nhieu chunk khong lien quan.

**Neu lam lai, toi se thay doi gi trong data strategy?**
Toi se dat metadata chi tiet hon cho query theo bua an, nguyen lieu chinh, va tao them benchmark co cau hoi multi-hop de danh gia retrieval chinh xac hon.

---

## Tu Danh Gia

| Tieu chi | Loai | Diem tu danh gia |
|----------|------|-------------------|
| Warm-up | Ca nhan | 5 / 5 |
| Document selection | Nhom | 10 / 10 |
| Chunking strategy | Nhom | Chua lam xong |
| My approach | Ca nhan | 10 / 10 |
| Similarity predictions | Ca nhan | 5 / 5 |
| Results | Ca nhan | 10 / 10 |
| Core implementation (tests) | Ca nhan | 30 / 30 |
| Demo | Nhom | Chua lam xong |
| **Tong** | | **60 / 100** o Phase 1 + mot phan Phase 2 |

