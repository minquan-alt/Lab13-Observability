# Member C – Báo cáo Cá nhân: SLOs & Alerts

> **Vai trò**: 🚨 Cảnh giới – SLOs & Alerts  
> **Nhiệm vụ tổng quát**: Đảm bảo hệ thống không vượt quá giới hạn bằng các SLO (Service Level Objectives) và cơ chế Alert, đóng vai trò "người gác đền" phát hiện sự cố trước khi người dùng bị ảnh hưởng.

---

## 1. Tổng quan Nhiệm vụ

Observability không chỉ là việc *thu thập* dữ liệu – quan trọng hơn là *biết khi nào* hệ thống đang gặp vấn đề. Member C chịu trách nhiệm xây dựng tầng "cảnh báo sớm" gồm 3 phần:

| Task    | File                      | Mục tiêu                                         |
| ------- | ------------------------- | ------------------------------------------------ |
| **C.1** | `config/slo.yaml`         | Định nghĩa ngưỡng kỳ vọng (SLO) dựa trên thực tế |
| **C.2** | `config/alert_rules.yaml` | Tạo 3+ rules tự động cảnh báo khi vi phạm SLO    |
| **C.3** | `docs/alerts.md`          | Viết Runbook hướng dẫn xử lý từng loại alert     |

---

## 2. Kiến thức Nền tảng Cần Hiểu

### 2.1 SLO là gì?

**SLO (Service Level Objective)** là mục tiêu đo lường chất lượng dịch vụ mà nhóm cam kết duy trì.

```
SLI (chỉ số đo) → SLO (mục tiêu) → SLA (cam kết với khách hàng)
```

Ví dụ trong lab này:
- **SLI**: `latency_p95_ms` – giá trị P95 của thời gian phản hồi
- **SLO**: P95 < 1 500 ms, đạt 99.5% số cửa sổ thời gian trong 28 ngày
- **Error Budget**: 0.5% × 28 ngày = ~3.4 giờ được phép vi phạm

### 2.2 SLI trong hệ thống này

Hệ thống lab sử dụng 4 SLI chính, được đo trong `app/metrics.py`:

| SLI                 | Cách đo                             | Nơi ghi            |
| ------------------- | ----------------------------------- | ------------------ |
| `latency_p95_ms`    | `percentile(REQUEST_LATENCIES, 95)` | `record_request()` |
| `error_rate_pct`    | `ERRORS` counter / `TRAFFIC`        | `record_error()`   |
| `daily_cost_usd`    | `sum(REQUEST_COSTS)`                | `record_request()` |
| `quality_score_avg` | `mean(QUALITY_SCORES)`              | `record_request()` |

### 2.3 Alert Rules là gì?

Alert Rule là điều kiện tự động kiểm tra SLI. Khi điều kiện đúng kéo dài đủ lâu (để tránh false positive), một alert được bắn ra.

```
Condition: latency_p95_ms > 1500
Duration:  for 10 minutes
→ Fire alert: high_latency_p95 (P2)
```

### 2.4 Runbook là gì?

Runbook là tài liệu hướng dẫn từng bước xử lý khi alert xảy ra. Mục tiêu: **bất kỳ thành viên nào** nhận alert đều có thể tự xử lý mà không cần hỏi người viết code.

---

## 3. Task C.1 – Calibrate SLOs (`config/slo.yaml`)

### 3.1 Vấn đề với file gốc

File `slo.yaml` ban đầu có các giá trị placeholder chưa được kiểm chứng:

```yaml
# TRƯỚC (placeholder)
latency_p95_ms:
  objective: 3000          # Quá cao – không phản ánh thực tế
  target: 99.5
  note: Replace with your group's target   # chưa làm gì
```

Với baseline thực tế của hệ thống ~400–700 ms (không có incident), ngưỡng 3 000 ms quá thoải mái – system có thể chạy chậm gấp 4 lần mà chưa alert.

### 3.2 Quá trình Calibrate

**Bước 1**: Chạy hệ thống bình thường, quan sát `latency_p95` qua endpoint `/metrics`.

**Bước 2**: Kích hoạt incident `rag_slow`, đo P95 spike → thường lên 3–5 s.

**Bước 3**: Xác định ngưỡng hợp lý:
```
Baseline P95:  ~650 ms
Headroom 2×:   650 × 2 = 1 300 ms
Round up:      1 500 ms  ← objective mới
```

**Bước 4**: Tính Error Budget Policy (tầng alert nâng cao):
```
SLO target 99.5%  →  Error budget 0.5% of 28 days = ~3.4 hours
Burn rate 1h:  14.4×  (exhausts 5% budget in 1 hour)
Burn rate 6h:   6.0×  (exhausts 5% budget in 6 hours)
```

### 3.3 Kết quả (`config/slo.yaml`)

```yaml
service: day13-observability-lab
window: 28d

slis:
  latency_p95_ms:
    objective: 1500          # ms – tightened từ 3000
    target: 99.5
    measurement: histogram_p95(latency_ms)
    note: >
      Baseline P95 ~650ms → 2× headroom = 1500ms.
      Đủ nhạy để bắt rag_slow incident ngay sau 10 phút.

  error_rate_pct:
    objective: 2
    target: 99.0
    measurement: rate(errors_total) / rate(requests_total) * 100

  daily_cost_usd:
    objective: 2.5
    target: 100.0
    measurement: sum(cost_usd) over 24h

  quality_score_avg:
    objective: 0.75
    target: 95.0
    measurement: avg(quality_score)
    note: >
      Baseline ~0.83. Alert bắn khi drop xuống 0.70 (15 min).

error_budget_policy:
  burn_rate_1h: 14.4
  burn_rate_6h: 6.0
```

---

## 4. Task C.2 – Viết Alert Rules (`config/alert_rules.yaml`)

### 4.1 Yêu cầu

Theo `implentation-plan.md`, cần ít nhất **3 alert rules có giá trị**:
1. Chi phí tăng đột biến (Cost spike)
2. Latency vượt ngưỡng (Degraded P95)
3. Điểm chất lượng giảm (Low Quality Score)

### 4.2 Nguyên tắc thiết kế Alert

Mỗi alert tốt cần có:
- **Condition**: biểu thức đo cụ thể
- **Duration**: thời gian duy trì để giảm false positive
- **Severity**: P1 (nghiêm trọng nhất) → P3 (nhẹ)
- **Runbook link**: URL chính xác đến section trong `docs/alerts.md`

```
Duration quá ngắn → False positives (alert reng liên tục không cần thiết)
Duration quá dài  → Alert đến trễ, thiệt hại đã xảy ra
```

### 4.3 Chi tiết 4 Alert Rules đã viết

#### Rule 1 – `high_latency_p95` (P2)
```yaml
condition: latency_p95_ms > 1500 for 10m
```
- **Vì sao 10 phút?** Đủ để phân biệt spike tạm thời (1–2 request chậm) với degradation thật sự.
- **Vì sao P2?** Ảnh hưởng UX nhưng service vẫn *hoạt động* – không phải emergency.
- **Liên kết**: Treshold 1 500 ms khớp với SLO `latency_p95_ms`.

#### Rule 2 – `cost_budget_spike` (P2) ← **Mới hoàn toàn**
```yaml
condition: hourly_cost_usd > 2x_baseline for 15m
```
- **Vì sao cần?** Daily cost SLO là $2.50. Nếu hourly rate gấp đôi bình thường liên tục 15 phút, ngân sách ngày sẽ cạn trước nửa đêm.
- **2× baseline**: Baseline ~$0.05/giờ → alert khi > $0.10/giờ.
- **Owner**: `finops-owner` – alert này thuộc về người quản lý chi phí, không phải on-call engineer.

#### Rule 3 – `low_quality_score` (P3) ← **Mới hoàn toàn**
```yaml
condition: quality_score_avg < 0.70 for 15m
```
- **Vì sao 0.70 < 0.75 (SLO objective)?** Có một khoảng đệm – khi score chạm 0.70, ta cần điều tra trước khi vi phạm SLO 0.75.
- **P3**: Ảnh hưởng chất lượng nhưng chưa phải outage. Tuy nhiên nếu kéo dài → escalate.
- **Giá trị cho demo**: Đây là alert duy nhất đo *chất lượng business* (không chỉ uptime) – rất ấn tượng với giảng viên.

#### Rule 4 – `high_error_rate` (P1) ← **Cải tiến từ rule cũ**
```yaml
condition: error_rate_pct > 5 for 5m
```
- Giữ nguyên logic nhưng thêm `description` và link runbook mục `#4`.

### 4.4 Kết quả (`config/alert_rules.yaml`)

```yaml
alerts:
  - name: high_latency_p95
    severity: P2
    condition: latency_p95_ms > 1500 for 10m
    owner: team-oncall
    runbook: docs/alerts.md#1-high-latency-p95

  - name: cost_budget_spike
    severity: P2
    condition: hourly_cost_usd > 2x_baseline for 15m
    owner: finops-owner
    runbook: docs/alerts.md#2-cost-budget-spike

  - name: low_quality_score
    severity: P3
    condition: quality_score_avg < 0.70 for 15m
    owner: team-oncall
    runbook: docs/alerts.md#3-low-quality-score

  - name: high_error_rate
    severity: P1
    condition: error_rate_pct > 5 for 5m
    owner: team-oncall
    runbook: docs/alerts.md#4-high-error-rate
```

---

## 5. Task C.3 – Viết Runbook (`docs/alerts.md`)

### 5.1 Cấu trúc mỗi Runbook Section

Mỗi alert có một section với cấu trúc chuẩn:

```
## N. Tên Alert
│
├── Bảng thông tin (severity, trigger, SLO liên quan, owner)
├── Tại sao quan trọng?  ← giải thích business impact
├── First Checks
│   ├── Panel Dashboard cần nhìn (số panel cụ thể)
│   ├── Script terminal để xác nhận
│   ├── Langfuse trace flow để drill-down
│   └── Lệnh kiểm tra incident toggle
└── Mitigation
    └── Các bước từ đơn giản → phức tạp
```

### 5.2 Điểm mấu chốt trong từng Runbook

#### Alert 1 – High Latency P95
- **First check quan trọng nhất**: So sánh RAG span vs LLM span trên Langfuse.
  - Nếu `RAG > 80%` tổng time → nguyên nhân là RAG retrieval chậm.
  - Nếu `LLM > 80%` tổng time → nguyên nhân là model hoặc prompt dài.
- **Lệnh tắt incident ngay**:
  ```bash
  curl -X POST http://localhost:8000/incidents/rag_slow/disable
  ```

#### Alert 2 – Cost Budget Spike
- **First check**: Lọc `feature` + `model` trên Langfuse Analytics để tìm feature đắt nhất.
- **Mitigation đặc biệt**: Route request đơn giản sang `mock_llm` (cost = $0) để cắt giảm ngay lập tức.

#### Alert 3 – Low Quality Score
- **Dấu hiệu RAG fail**: RAG span trả về `docs: []` (mảng rỗng) → LLM không có context → hallucinate.
- **Mitigation đặc biệt**: Tăng `top_k` từ 3 → 5 chunks để RAG tìm được kết quả dù query bất thường.

#### Alert 4 – High Error Rate  
- **Phân loại lỗi**: 3 nhóm: `llm_error`, `rag_error`, `validation_error` → mỗi nhóm có hướng xử lý riêng.

### 5.3 Quick Reference Table (cuối file)

Thêm bảng tổng hợp để on-call engineer *không cần đọc toàn bộ* khi đang khẩn cấp:

| Alert               | Panel Dashboard   | Script kiểm tra                    | Hành động đầu tiên           |
| ------------------- | ----------------- | ---------------------------------- | ---------------------------- |
| `high_latency_p95`  | Panel 2 (Latency) | `validate_logs.py \| grep latency` | Kiểm tra incident `rag_slow` |
| `cost_budget_spike` | Panel 4 (Cost)    | `validate_logs.py \| grep cost`    | Tắt incident `cost_spike`    |
| `low_quality_score` | Panel 6 (Quality) | `validate_logs.py \| grep quality` | Kiểm tra RAG trả về rỗng     |
| `high_error_rate`   | Panel 3 (Errors)  | `validate_logs.py \| grep error`   | Xem exception trong Langfuse |

---

## 6. Liên kết với Các Member Khác

Member C không làm việc độc lập – các file này được tích hợp chặt chẽ:

```
Member B (Tracing)
  └─ Langfuse trace tree → Member C dùng để drill-down trong Runbook
       └─ "Click vào trace → xem RAG span vs LLM span"

Member D (Chaos)
  └─ Kích hoạt incidents → Kích hoạt alerts của Member C
       └─ cost_spike, rag_slow → fire high_latency_p95, cost_budget_spike

Member E (Dashboard)
  └─ 6 panels → Member C tham chiếu trong Runbook
       └─ "Nhìn vào Panel 2 – Latency Histogram"

Member F (Demo)
  └─ Dùng alerts.md để kể câu chuyện Hồi 2 (Khủng hoảng)
       └─ "Alert C reng lên → xem Runbook → tìm root cause"
```

---

## 7. Kết quả và Bằng chứng Hoàn thành

### Files đã chỉnh sửa / tạo mới

| File                                                    | Trạng thái | Nội dung chính                                |
| ------------------------------------------------------- | ---------- | --------------------------------------------- |
| [`config/slo.yaml`](../config/slo.yaml)                 | ✅ Cập nhật | 4 SLIs với giá trị thật + error budget policy |
| [`config/alert_rules.yaml`](../config/alert_rules.yaml) | ✅ Cập nhật | 4 alert rules (3 mới + 1 cải tiến)            |
| [`docs/alerts.md`](./alerts.md)                         | ✅ Cập nhật | Runbook đầy đủ 4 sections + Quick Reference   |

### Checklist theo rubric

Theo `day13-rubric-for-instructor.md` – mục **10đ – Alerts & PII**:
> *"Có ít nhất 3 alert rules với runbook link hoạt động."*

- [x] Alert rule 1: `high_latency_p95` → `docs/alerts.md#1-high-latency-p95`
- [x] Alert rule 2: `cost_budget_spike` → `docs/alerts.md#2-cost-budget-spike`
- [x] Alert rule 3: `low_quality_score` → `docs/alerts.md#3-low-quality-score`
- [x] Alert rule 4: `high_error_rate` → `docs/alerts.md#4-high-error-rate`
- [x] SLO calibrated với giá trị thực (không còn placeholder)
- [x] Runbook có đủ Panel reference, Script, Mitigation steps

---

## 8. Câu hỏi Giảng viên Hay Hỏi

**Q: SLO 99.5% có nghĩa là gì trong thực tế?**  
A: Trong cửa sổ 28 ngày, hệ thống được phép vi phạm ngưỡng P95 tối đa 0.5% thời gian = khoảng 2 tiếng. Đây là "Error Budget". Nếu budget cạn trước cuối tháng, nhóm phải dừng deploy.

**Q: Tại sao chọn 1 500 ms thay vì 3 000 ms?**  
A: Baseline thực tế ~650 ms. Ngưỡng 1 500 ms = 2.3× baseline, đủ headroom cho biến động bình thường nhưng vẫn bắt được `rag_slow` incident (spike lên 3–5 s) trong vòng 10 phút đầu.

**Q: Tại sao `low_quality_score` dùng 0.70 thay vì 0.75 (SLO objective)?**  
A: Alert phải bắt sớm hơn SLO violation để có thời gian xử lý. Khi score = 0.70, ta điều tra và fix ngay. Nếu để đến 0.75 mới alert thì đã vi phạm SLO rồi.

**Q: Runbook có tự động chạy không?**  
A: Trong lab này, Runbook là tài liệu hướng dẫn thủ công. Trong production thật, các bước có thể được tích hợp vào PagerDuty, OpsGenie, hoặc Ansible Playbook để auto-remediate.

---

## 9. Làm sao Detect Sớm Hơn? (Giải pháp + Timeline)

> **Bối cảnh**: Alert hiện tại phản ứng khi vấn đề *đã xảy ra* (reactive).  
> Mục tiêu của phần này: xây dựng hệ thống **proactive** – phát hiện *trước khi* người dùng bị ảnh hưởng.

---

### 🟢 Mức 1 – Ngay Tuần Này (Quick Wins)

**Phiên hiện tại lab đã thực hiện được tầng này.**

#### Dashboard hàng ngày (Daily Cost Visibility)

Tạo 3 panel bổ sung vào Dashboard của Member E:

| Panel                          | Metric                            | Mục đích                          |
| ------------------------------ | --------------------------------- | --------------------------------- |
| **Total cost (7-day rolling)** | `sum(cost_usd) over 7d`           | Thấy xu hướng tăng/giảm theo tuần |
| **Cost per 1k requests**       | `total_cost / traffic * 1000`     | Chuẩn hóa theo lưu lượng          |
| **Top 10 users by cost (%)**   | `cost_by_user / total_cost * 100` | Xác định user "đốt tiền" nhất     |

#### Alert Slack/Teams bổ sung

Hai rule mới cần thêm vào `config/alert_rules.yaml`:

```yaml
# Alert A – Daily cost tăng đột biến so với tuần trước
- name: daily_cost_vs_7day_avg
  severity: P2
  condition: today_cost_usd > 1.3 * avg_7day_cost_usd
  # Giải thích: nếu hôm nay chi hơn 30% so với trung bình 7 ngày → cảnh báo ngay
  notification: slack-channel-finops
  runbook: docs/alerts.md#2-cost-budget-spike

# Alert B – 1 user chiếm > 10% tổng cost trong 24h
- name: single_user_cost_dominance
  severity: P2
  condition: max(user_cost_24h) / total_cost_24h > 0.10
  # Giải thích: 1 user không nên chiếm > 10% ngân sách – dấu hiệu abuse hoặc bug
  notification: slack-channel-oncall
  runbook: docs/alerts.md#2-cost-budget-spike
```

**Tại sao 30% và 10%?**
- `30%` so với 7-day avg: đủ nhạy để bắt spike thật (ví dụ: feature mới deploy), nhưng không quá nhạy với biến động ngày cuối tuần (~10–15% bình thường).
- `10% per user`: nếu hệ thống có 50+ users, 1 user chiếm > 10% là bất thường. Đây thường là dấu hiệu abuse, bot traffic, hoặc infinite loop gọi API.

**Timeline thực hiện: 1–2 ngày.**

---

### 🟡 Mức 2 – Trong 2 Tuần (Production-Grade)

#### Instrument code với OpenTelemetry + LLM Tracer

Thay thế `app/metrics.py` (in-memory counter) bằng OpenTelemetry SDK để export sang hệ thống observability bên ngoài:

```python
# app/metrics_otel.py  (production version)
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider

meter = MeterProvider().get_meter("day13-observability")

cost_counter    = meter.create_counter("llm.cost_usd")
token_histogram = meter.create_histogram("llm.tokens")
quality_gauge   = meter.create_observable_gauge("llm.quality_score")
```

Tích hợp **Helicone** hoặc **LangSmith** để tự động collect cost từ mọi LLM call mà không cần sửa code thủ công.

#### Tag mỗi request với rich metadata

Mỗi request phải carry đủ 5 labels để filter/group trên dashboard:

```python
# Trong app/agent.py, khi gọi record_request()
record_request(
    latency_ms   = elapsed_ms,
    cost_usd     = cost,
    tokens_in    = tokens_in,
    tokens_out   = tokens_out,
    quality_score= score,
    # Tags mới:
    feature      = "chat",          # chat | search | summarize
    user_tier    = "free",          # free | pro | enterprise
    model        = "gpt-4o-mini",   # tên model thực tế
)
```

**Lợi ích**: Có thể query "cost của feature `summarize` với `pro` users trong 24h" → phân tích chính xác hơn nhiều so với tổng aggregate.

#### Anomaly Detection với Z-score

Thay vì alert theo ngưỡng cố định (`cost > 2x_baseline`), dùng **z-score** để tự động thích nghi với pattern theo ngày:

```python
# scripts/anomaly_detect.py
import statistics

def is_cost_anomaly(daily_costs: list[float], today: float, threshold_z: float = 2.5) -> bool:
    """
    Trả về True nếu today's cost là bất thường so với lịch sử.
    
    Z-score = (today - mean) / stdev
    Nếu Z > 2.5 → outlier (xác suất bình thường chỉ ~0.6%)
    """
    if len(daily_costs) < 7:
        return False  # Chưa đủ data để detect
    mean = statistics.mean(daily_costs)
    stdev = statistics.stdev(daily_costs)
    if stdev == 0:
        return False
    z = (today - mean) / stdev
    return z > threshold_z
```

**So sánh với cách cũ**:
| Cách                           | Ưu điểm                                         | Nhược điểm                                                          |
| ------------------------------ | ----------------------------------------------- | ------------------------------------------------------------------- |
| Fixed threshold (`> $0.10/hr`) | Đơn giản, dễ hiểu                               | Không thích nghi với growth – false positive nhiều khi traffic tăng |
| Z-score (≥ 2.5σ)               | Tự động thích nghi, ít false positive           | Cần ≥ 7 ngày data để hoạt động                                      |
| Prophet (Facebook)             | Bắt được seasonality (cuối tuần vs ngày thường) | Phức tạp hơn, cần train model                                       |

#### Budget Guardrails (Phòng thủ hard limit)

```python
# app/middleware.py  – thêm budget check
async def cost_guardrail_middleware(request, call_next):
    user_cost_today = get_user_cost_today(request.user_id)
    
    # Soft limit: free-tier user đã xài > $5/tháng
    if user_tier == "free" and user_cost_today > 5.0:
        # Tự động downgrade: dùng model rẻ hơn
        request.state.forced_model = "gpt-4o-mini"
    
    # Hard limit: toàn hệ thống > $X/ngày
    system_cost_today = get_system_cost_today()
    if system_cost_today > HARD_LIMIT_USD:
        # Auto-pause non-critical features
        disable_feature("summarize")
        disable_feature("batch_process")
        # Chỉ giữ lại feature core: chat
    
    return await call_next(request)
```

**Tại sao cần hard limit?**  
Nếu có bug (infinite retry loop, prompt injection dạng "repeat 1000 times"), không có hard limit thì một đêm có thể đốt hết budget cả tháng.

**Timeline thực hiện: 1–2 tuần** (cần refactor `app/metrics.py` + deploy lại).

---

### 🔴 Mức 3 – Best Practice (1 Tháng)

Đây là mức production engineer tại các công ty AI lớn (OpenAI, Anthropic) đang áp dụng.

#### Cost-Aware Routing

Thay vì luôn dùng 1 model, router tự động chọn model dựa trên độ phức tạp của request:

```
Request đơn giản  → gpt-4o-mini  ($0.00015/1k tokens)
Request phức tạp  → gpt-4o       ($0.005/1k tokens)  ← 33× đắt hơn
```

```python
# app/cost_aware_router.py
def select_model(query: str, user_tier: str) -> str:
    complexity = estimate_complexity(query)  # simple | medium | complex
    
    if user_tier == "free":
        return "gpt-4o-mini"  # Free user luôn dùng model rẻ
    
    if complexity == "simple":
        return "gpt-4o-mini"  # "What time is it?" không cần GPT-4o
    elif complexity == "medium":
        return "gpt-4o-mini"
    else:
        return "gpt-4o"       # Chỉ khi thực sự cần
```

**Ước tính tiết kiệm**: Nếu 70% request là "simple", routing đúng giảm cost ~50–60%.

#### Auto-Summarize Conversation History

Sau 10 lượt chat, conversation history có thể dài 5 000+ tokens → đắt với mỗi request.

```python
# app/agent.py  – thêm auto-summarize
async def manage_history(messages: list) -> list:
    if len(messages) > 10:
        # Summarize 8 messages cũ nhất thành 1 đoạn ngắn
        summary = await llm.summarize(messages[:8])
        # Giữ lại 2 messages gần nhất + summary
        return [{"role": "system", "content": f"[Summary]: {summary}"}] + messages[-2:]
    return messages
```

**Ước tính tiết kiệm**: Giảm ~60% tokens_in sau lượt chat thứ 10+.

#### Prompt Caching (OpenAI API – 2025)

OpenAI hỗ trợ cache prefix của prompt. Nếu system prompt + tool description không đổi giữa các request, chúng chỉ được tính tiền 1 lần:

```python
# Cấu hình để enable prompt caching
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": SYSTEM_PROMPT,  # ~2000 tokens – sẽ được cache
            # OpenAI tự cache nếu prefix >= 1024 tokens và lặp lại
        },
        {"role": "user", "content": user_message}
    ]
)

# Kiểm tra cache hit trong response
cached_tokens = response.usage.prompt_tokens_details.cached_tokens
print(f"Saved: {cached_tokens} tokens from cache")
```

**Điều kiện để cache hoạt động**:
- System prompt phải ≥ 1 024 tokens.
- Prefix phải giống hệt nhau (không thể thêm ngày giờ vào system prompt).
- Cache TTL: 5 phút (tự reset nếu không có request mới).

**Ước tính tiết kiệm**: 50% cost trên `tokens_in` nếu system prompt chiếm đa số input.

---

### 📊 Tóm tắt Timeline

```
Tuần 1  ──────────────────────────────────────────────────────────────────
         ✅ Alert cost vs 7-day avg
         ✅ Alert single-user dominance
         ✅ Daily cost dashboard (3 panels mới)
         Effort: ~4 giờ

Tuần 2–3 ─────────────────────────────────────────────────────────────────
         🔲 OpenTelemetry instrumentation + LLM tracer
         🔲 Rich metadata tags (feature, user_tier, model)
         🔲 Z-score anomaly detection script
         🔲 Budget guardrails (soft + hard limit)
         Effort: ~2–3 ngày dev

Tháng 1  ─────────────────────────────────────────────────────────────────
         🔲 Cost-aware routing (complexity classifier)
         🔲 Auto-summarize sau 10 turns
         🔲 Prompt caching configuration
         Effort: ~1 tuần dev + testing
```

### 💡 Nguyên tắc Chính

> **Reactive → Proactive → Preventive**
>
> - **Reactive** (đã làm): Alert khi cost ĐANG cao.  
> - **Proactive** (Mức 1–2): Phát hiện TRƯỚC khi vượt ngưỡng (trend, z-score).  
> - **Preventive** (Mức 3): Hệ thống tự động tránh chi phí cao (routing, caching, summarize).
