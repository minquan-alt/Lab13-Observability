# Alert Rules & Runbooks

> **Cách dùng**: Khi một alert bắn lên, tìm mục tương ứng bên dưới,
> làm lần lượt các bước **First Checks** rồi áp dụng **Mitigation**.

---

## 1. High Latency P95

| Field | Value |
|---|---|
| **Rule name** | `high_latency_p95` |
| **Severity** | P2 |
| **Trigger** | `latency_p95_ms > 1 500` kéo dài **10 phút** |
| **SLO liên quan** | `latency_p95_ms` – objective 1 500 ms, target 99.5 % |
| **Owner** | team-oncall |

### Tại sao quan trọng?
Khi P95 vượt ngưỡng, 1/20 người dùng trải nghiệm độ trễ cao – ảnh hưởng trực tiếp đến UX và có thể dẫn đến time-out cascade.

### First Checks

1. **Panel cần nhìn**: Mở Dashboard → **Panel 2 – Latency Histogram**.
   Xem P50, P95, P99 – nếu P95 cao nhưng P50 bình thường, đây là tail issue.
2. **Chạy script xác nhận**:
   ```bash
   python scripts/validate_logs.py | grep latency_p95
   ```
3. **Kiểm tra Langfuse Trace**:
   - Vào tab **Traces** → lọc theo thời điểm spike.
   - Click trace bất kỳ → xem **RAG span** vs **LLM span**.
   - Nếu RAG span > 80 % tổng thời gian → nguyên nhân là RAG.
4. **Kiểm tra incident toggle**:
   ```bash
   curl http://localhost:8000/incidents
   ```
   Nếu `rag_slow` = `enabled` → tắt ngay:
   ```bash
   curl -X POST http://localhost:8000/incidents/rag_slow/disable
   ```

### Mitigation

- Tắt `rag_slow` incident nếu đang bật.
- Giảm `max_tokens` trong prompt để rút ngắn LLM time.
- Kích hoạt fallback retrieval source (giảm số chunk từ 5 → 2).
- Nếu vẫn kéo dài: rollback commit gần nhất liên quan đến `mock_rag.py`.

---

## 2. Cost Budget Spike

| Field | Value |
|---|---|
| **Rule name** | `cost_budget_spike` |
| **Severity** | P2 |
| **Trigger** | `hourly_cost_usd > 2×` baseline kéo dài **15 phút** |
| **SLO liên quan** | `daily_cost_usd` – objective $2.50/day |
| **Owner** | finops-owner |

### Tại sao quan trọng?
Chi phí tăng đột biến, nếu không xử lý, sẽ vượt budget hàng ngày. Việc phát hiện sớm (trong vòng 15 phút) giúp tránh mất tiền không cần thiết.

### First Checks

1. **Panel cần nhìn**: Dashboard → **Panel 4 – Cost Accumulation** (đường tích lũy).
   So sánh đường thực tế với đường SLO budget.
2. **Chạy script xác nhận**:
   ```bash
   python scripts/validate_logs.py | grep cost
   curl http://localhost:8000/metrics | grep total_cost
   ```
3. **Phân tích trên Langfuse**:
   - Vào **Analytics** → filter theo `feature` và `model`.
   - Tìm feature có `tokens_in + tokens_out` cao nhất.
   - Xem `cost_usd` per trace để xác định request đắt tiền nhất.
4. **Kiểm tra incident cost_spike**:
   ```bash
   curl http://localhost:8000/incidents
   ```
   Nếu `cost_spike` = `enabled`:
   ```bash
   curl -X POST http://localhost:8000/incidents/cost_spike/disable
   ```

### Mitigation

- Tắt incident `cost_spike` nếu đang bật.
- Rút ngắn system prompt (xóa bớt ví dụ few-shot).
- Route các request đơn giản sang model rẻ hơn (`gpt-3.5-turbo` hoặc local `mock_llm`).
- Bật prompt cache nếu có cấu hình sẵn.
- Tạm thời giảm `concurrency` của load test xuống 1.

---

## 3. Low Quality Score

| Field | Value |
|---|---|
| **Rule name** | `low_quality_score` |
| **Severity** | P3 |
| **Trigger** | `quality_score_avg < 0.70` kéo dài **15 phút** |
| **SLO liên quan** | `quality_score_avg` – objective 0.75, target 95 % |
| **Owner** | team-oncall |

### Tại sao quan trọng?
Score thấp có nghĩa là bot đang trả lời sai, không liên quan, hoặc RAG đang lấy chunks không phù hợp. Đây là dấu hiệu sớm nhất của sự degradation về chất lượng – trước khi người dùng phàn nàn.

### First Checks

1. **Panel cần nhìn**: Dashboard → **Panel 6 – Average Quality Score**.
   Xem đường trend – nếu giảm dần thì là structural issue, nếu cắm đột ngột thì là incident.
2. **Chạy script xác nhận**:
   ```bash
   python scripts/validate_logs.py | grep quality
   curl http://localhost:8000/metrics | grep quality_avg
   ```
3. **Phân tích Langfuse**:
   - Vào **Scores** tab → lọc `score_name = quality_score`.
   - Tìm traces có score < 0.60 → click vào xem RAG span.
   - Nếu RAG span trả về `docs: []` (empty) → RAG fail.
4. **Phân tích log**:
   ```bash
   grep "quality_score" logs/app.jsonl | python -m json.tool | grep -E "score|feature|session"
   ```

### Mitigation

- Kiểm tra `mock_rag.py` – đảm bảo hàm `retrieve()` không bị incident override.
- Tăng `top_k` chunk từ 3 → 5 để RAG có nhiều context hơn.
- Nếu LLM trả về hallucination: thêm explicit instruction vào system prompt.
- Nếu không cải thiện sau 30 phút: escalate lên P2 và ping team tracing (Member B).

---

## 4. High Error Rate

| Field | Value |
|---|---|
| **Rule name** | `high_error_rate` |
| **Severity** | P1 |
| **Trigger** | `error_rate_pct > 5` kéo dài **5 phút** |
| **SLO liên quan** | `error_rate_pct` – objective 2 %, target 99.0 % |
| **Owner** | team-oncall |

### Tại sao quan trọng?
P1 – người dùng nhận lỗi trực tiếp. Phải xử lý trong vòng 15 phút.

### First Checks

1. **Panel cần nhìn**: Dashboard → **Panel 3 – Error Volume by Type**.
2. **Lệnh xác nhận ngay**:
   ```bash
   curl http://localhost:8000/metrics | grep error
   grep "error" logs/app.jsonl | tail -20 | python -m json.tool
   ```
3. **Phân loại lỗi**:
   - `llm_error` → lỗi từ model (timeout, rate limit, schema).
   - `rag_error` → lỗi từ retrieval pipeline.
   - `validation_error` → schema request/response sai.
4. **Trace lỗi trên Langfuse**:
   - Filter traces by `status = error`.
   - Xem exception message trong span bị đỏ.

### Mitigation

- **llm_error**: Rollback thay đổi prompt gần nhất; thử fallback model.
- **rag_error**: Tắt incident `rag_slow`; kiểm tra `mock_rag.py`.
- **validation_error**: Xem `app/schemas.py` – có thể field mới bị thiếu default.
- Nếu không rõ nguyên nhân sau 5 phút: restart service và theo dõi.

---

## Tóm tắt Nhanh (Quick Reference)

| Alert | Panel Dashboard | Script kiểm tra | Hành động đầu tiên |
|---|---|---|---|
| `high_latency_p95` | Panel 2 (Latency) | `validate_logs.py \| grep latency` | Kiểm tra incident `rag_slow` |
| `cost_budget_spike` | Panel 4 (Cost) | `validate_logs.py \| grep cost` | Tắt incident `cost_spike` |
| `low_quality_score` | Panel 6 (Quality) | `validate_logs.py \| grep quality` | Kiểm tra RAG trả về rỗng |
| `high_error_rate` | Panel 3 (Errors) | `validate_logs.py \| grep error` | Xem exception trong Langfuse |
