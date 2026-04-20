# Kế hoạch Hoàn thiện Lab 13 Observability - Phân công 6 Thành viên

> **Mục tiêu:** Hoàn thành xuất sắc Lab 13, đạt điểm tối đa (100/100 từ script + thuyết trình tốt), với sự tập trung đặc biệt vào **Langfuse Tracing** và **Dashboard** để trực quan hóa dữ liệu (UI). Hệ thống cần đạt tiêu chí "trong suốt" (100% Observable).

## Chiến lược Đạt Điểm Cao

Ban giám khảo sẽ cực kỳ ấn tượng nếu phần UI/Dashboard và Tracing của nhóm rõ ràng. Do đó:
- **Tracing (Member B)** phải tổ chức trace theo dạng cây (Hierarchy), phân tách rõ ràng LLM call và Retrieval.
- **Dashboard (Member E)** không chỉ dựng đủ 6 panel, mà cần thể hiện được Business Value (User nào đang tốn nhiều tiền nhất? Feature nào hay bị RAG fail nhất?).
- **Demo (Member F)** phải tạo ra kịch bản demo (storytelling) gắn liền với phần UI để giải thích tại sao Observability lại quan trọng.

---

## Phân công Nhiệm vụ Chi tiết (6 Thành viên)

### 👨‍💻 Member A: Nền tảng Log & Bảo mật (Logging & PII)

**Nhiệm vụ:** Đảm bảo mọi request đều có ID, log có đủ context và không lộ dữ liệu người dùng.

- [ ] **Task A.1**: Hoàn thiện `app/middleware.py`.
    - Sinh `correlation_id` (format: `req-<id>`).
    - Gọi `bind_contextvars(correlation_id=...)`.
    - Add `x-request-id` header vào response.
- [ ] **Task A.2**: Hoàn thiện Log Enrichment (`app/main.py`).
    - Trong hàm `/chat`, `bind_contextvars` các field: `user_id_hash`, `session_id`, `feature`, `model`, `env`.
- [ ] **Task A.3**: Kích hoạt bộ lọc PII (`app/logging_config.py`).
    - Đưa hàm `scrub_event` vào `processors` của Structlog.
- [ ] **Task A.4**: Cập nhật `app/pii.py`.
    - Viết thêm regex vào `PII_PATTERNS` để bắt thêm IP Address, Passport hoặc địa chỉ (nếu cần gây ấn tượng).

---

### 🕵️ Member B: Mắt Thần - Tracing & Quality Tags (Điểm nhấn UI)

**Nhiệm vụ:** Thiết lập Langfuse Tracing để mọi request đều vẽ ra một cây (Tree) trên UI của Langfuse, cho thấy chính xác bot làm gì, ở đâu, tốn bao nhiêu thời gian.

- [ ] **Task B.1**: Xác minh cấu hình API Key.
    - Cài đặt `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` vào `.env`.
- [ ] **Task B.2**: Hoàn thiện Tracing Framework (`app/agent.py`).
    - Phân tích hàm `run()`. Hiện tại nó có `@observe()`.
    - Cập nhật UI Trace: Dùng `langfuse_context.update_current_trace` để gắn Tag (Feature, Model) => Cực kỳ quan trọng để filter trên Langfuse Dashboard.
- [ ] **Task B.3**: Trace các bước nhỏ (Child Spans).
    - Mở file `app/mock_rag.py` và `app/mock_llm.py` (nếu lab cho phép sửa). Thêm `@observe(as_type="generation")` vào LLM call và `@observe(as_type="span")` vào RAG retrieve. *Điều này giúp UI trên Langfuse hiện ra mô hình cây đẹp mắt thay vì 1 thanh ngang.*
- [ ] **Task B.4**: Log Feedback & Quality.
    - Sử dụng `langfuse_context.score()` để gửi `quality_score` (tính toán trong agent) lên UI của Langfuse.

---

### 🚨 Member C: Cảnh giới - SLOs & Alerts

**Nhiệm vụ:** Làm người "gác đền", đảm bảo hệ thống không vượt quá giới hạn bằng các SLO và cơ chế Alert.

- [ ] **Task C.1**: Khảo sát & Tính toán SLO.
    - Đánh giá file `config/slo.yaml` (starter SLOs). Đề xuất cấu hình lại dựa trên test thực tế (VD: P99 Latency < 1.5s, Error Budget).
- [ ] **Task C.2**: Viết Alert Rules.
    - Sửa `config/alert_rules.yaml`. Cấu hình ít nhất 3 rule có giá trị:
        - *Chi phí tăng đột biến* (Cost spike).
        - *Latency vượt ngưỡng* (Degraded P95).
        - *Điểm chất lượng giảm* (Low Quality Score alert).
- [ ] **Task C.3**: Hoàn thiện `docs/alerts.md`.
    - Viết Runbook: "Khi có alert X, tôi cần nhìn vào panel Y trên Dashboard, và chạy script Z".

---

### 💥 Member D: Chuyên gia Khủng hoảng - Load Test & Chaos

**Nhiệm vụ:** Phá hoại hệ thống một cách có chủ đích (Chaos Engineering) để cung cấp dữ liệu thật cho UI và kiểm tra Alert.

- [ ] **Task D.1**: Generate Traffic có ý nghĩa.
    - Xem file `data/sample_queries.jsonl`. Viết thêm các query dài ngoằng, RAG fail, hoặc Prompt Injection.
    - Cắm script chạy liên tục (VD: Terminal chia 2 nửa, 1 nửa chạy `python scripts/load_test.py --concurrency 5`).
- [ ] **Task D.2**: Kích hoạt Incidents.
    - Gọi API `/incidents/rag_slow/enable` hoặc dùng script `python scripts/inject_incident.py` để tạo ra "vết thương" hệ thống.
- [ ] **Task D.3**: Báo cáo sự thay đổi.
    - Chụp lại màn hình/log terminal vào thời khắc kích hoạt sự cố và ghi chú timestamp đưa cho Member E & F.

---

### 📈 Member E: Trực quan hóa - Dashboard & Metrics (Quyết định điểm UI)

**Nhiệm vụ:** Chịu trách nhiệm render ra các Dashboard đẹp nhất, nhìn vào thấy ngay vấn đề do Member D tạo ra.

- [ ] **Task E.1**: Xác minh Endpoint Metrics.
    - Kiểm tra `app/metrics.py` và `/metrics` endpoint xem trả về dữ liệu đúng chưa (Traffic, Latency p95, Error breakdown).
- [ ] **Task E.2**: Xây dựng 6-Panel Dashboard (Dùng Langfuse Analytics hoặc external tuỳ lab).
    - **Panel 1**: Traffic Volume (Requests/min).
    - **Panel 2**: Latency Histogram (P50, P95, P99).
    - **Panel 3**: Error Volume by Type (Pie chart).
    - **Panel 4**: Cost Accumulation ($) - *Quan trọng cho Business.*
    - **Panel 5**: Token Usage (In/Out).
    - **Panel 6**: Average Quality Score (Heuristic).
- [ ] **Task E.3**: Tạo "Truy tìm thủ phạm".
    - Nhận Timestamp có sự cố từ Member D. Chụp hình UI Dashboard hiển thị "ĐỈNH ĐỒI" (Spike) hư hỏng tại đúng thời điểm đó. Đưa hình cho Member F.
- [ ] **Task E.4**: Tập hợp bằng chứng (Evidence).
    - Điền đầy đủ vào `docs/grading-evidence.md` kèm theo hình ảnh Dashboard rõ nét.

---

### 🎙️ Member F: Thuyết trình & Blueprint (Demo Lead)

**Nhiệm vụ:** Viết báo cáo cuối cùng và "kể câu chuyện" cho ban giám khảo.

- [ ] **Task F.1**: Chạy Validation.
    - Chạy `python scripts/validate_logs.py` và lấy bằng chứng đạt 100/100 điểm kỹ thuật.
- [ ] **Task F.2**: Hoàn thiện Blueprint.
    - Viết `docs/blueprint-template.md`. Đặt các Root Cause Analysis (phân tích lỗi từ Member D do Member E chụp màn hình) vào đây.
- [ ] **Task F.3**: Demo kịch bản 3 hồi.
    - **Hồi 1 ( Bình thường )**: Mở Log/Langfuse lên, cho thấy hệ thống đang log rất rõ (ẩn PII, có Trace), Cost đang ổn.
    - **Hồi 2 ( Khủng hoảng )**: Bất ngờ kích hoạt `rag_slow` incident. Dashboard của E đỏ chót! Alert C reng lên!
    - **Hồi 3 ( Phân tích )**: Từ cái gai nhọn (Spike) trên Dashboard P95 Latency, Mở tab Langfuse Trace (của B) -> Click vào Trace lúc đó -> Thấy RAG node dài thoòng -> Kết luận Root Cause là RAG.

---

## 🚦 Quy trình Phối hợp Nhóm (Quy tắc chung)

1. Mọi người đều phải `git pull` bản mới nhất mỗi 30 phút.
2. Code xong task, chạy `python scripts/validate_logs.py` cục bộ trước khi push.
3. Member D (Khủng hoảng) chỉ được bấm nút khi Member B (Tracing) và E (Dashboard) đã sẵn sàng.
