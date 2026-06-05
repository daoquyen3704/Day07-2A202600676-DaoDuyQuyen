# Recipe Vector Dataset

Bộ dữ liệu mẫu cho vector store DB / RAG benchmark về công thức nấu ăn tiếng Việt.

## Cấu trúc

- `data/*.md`: mỗi file là một công thức hoặc tài liệu quy tắc/mẹo nấu ăn.
- `metadata.json`: metadata tổng hợp cho toàn bộ file.

## Format mỗi file

Mỗi file có frontmatter metadata:

```yaml
---
title: "Tên tài liệu"
category: "soup | fried | stir_fry | dessert | cooking_tip | measurement"
cuisine: "vietnamese | general | western_vietnamese"
difficulty: "easy | medium | hard"
meal_type: "breakfast | lunch | dinner | snack | general"
language: "vi"
source: "self_written"
main_ingredients: [...]
---
```

Sau đó là nội dung cố định:

```md
# Tên món

## Mô tả

## Nguyên liệu

## Cách làm

## Lưu ý
```

## Câu hỏi benchmark gợi ý

- Món nào dùng gừng?
- Món nào là món tráng miệng?
- Món nào có độ khó easy?
- Cần bao nhiêu bước để làm Phở bò?
- Món nào dùng nước cốt dừa?
- Tài liệu nào thuộc category cooking_tip?
- Món nào phù hợp cho bữa sáng?
- Món nào có nguyên liệu chính là cá?
