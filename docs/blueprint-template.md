# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: C401 A2
- [REPO_URL]: 
- [MEMBERS]:
  - Member A: [Name] Hoàng Bá Minh Quang | Role: Tech Lead & Logging & PII
  - Member B: [Name] Đỗ Lê Thành Nhân | Role: Tracing & Enrichment
  - Member C: [Name] Nguyễn Anh Tài | Role: SLO & Alerts
  - Member D: [Name] Trần Quang Long | Role: Load Test & Dashboard
  - Member E: [Name] Nguyễn Công Quốc Huy| Role: Dashboard & Evidence

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE] 100/100

--- Lab Verification Results ---
Total log records analyzed: 1498
Records with missing required fields: 0
Records with missing enrichment (context): 0
Unique correlation IDs found: 708
Potential PII leaks detected: 0

--- Grading Scorecard (Estimates) ---
+ [PASSED] Basic JSON schema
+ [PASSED] Correlation ID propagation
+ [PASSED] Log enrichment
+ [PASSED] PII scrubbing

Estimated Score: 100/100

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT](screenshots\langfuse_1.png)
- [EVIDENCE_PII_REDACTION_SCREENSHOT](screenshots\langfuse_2.png)
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT](screenshots\langfuse_3.png)
- [TRACE_WATERFALL_EXPLANATION](screenshots\langfuse_3.png)

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT](screenshots\dashboard-1.jpeg)


### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT](screenshots\dashboard-1.jpeg)
```
alerts:
  # ──────────────────────────────────────────────────────────────
  # Rule 1 – Latency vượt ngưỡng (Degraded P95)
  # ──────────────────────────────────────────────────────────────
  - name: high_latency_p95
    severity: P2
    condition: latency_p95_ms > 1500 for 10m
    type: symptom-based
    owner: team-oncall
    description: >
      P95 tail latency exceeded the SLO threshold of 1 500 ms for 10
      consecutive minutes. Most likely cause: rag_slow incident active
      or an upstream model slowdown.
    runbook: docs/alerts.md#1-high-latency-p95

  # ──────────────────────────────────────────────────────────────
  # Rule 2 – Chi phí tăng đột biến (Cost Spike)
  # ──────────────────────────────────────────────────────────────
  - name: cost_budget_spike
    severity: P2
    condition: >
      hourly_cost_usd > 0.50 OR 
      avg_cost_per_request > 0.05
    type: symptom-based
    owner: finops-owner
    description: >
      Cost thresholds breached. Either hourly spend exceeded $0.50 
      (20% of daily budget) or average cost per request exceeded $0.05.
      Likely causes: High token usage per prompt or high traffic volume.
    runbook: docs/alerts.md#2-cost-budget-spike

  # ──────────────────────────────────────────────────────────────
  # Rule 3 – Điểm chất lượng giảm (Low Quality Score)
  # ──────────────────────────────────────────────────────────────
  - name: low_quality_score
    severity: P3
    condition: quality_score_avg < 0.70 for 15m
    type: symptom-based
    owner: team-oncall
    description: >
      Rolling average quality score (faithfulness + relevance heuristic)
      has fallen below 0.70 for 15 minutes. Possible causes: RAG
      retrieval degradation, prompt truncation, or model regression.
    runbook: docs/alerts.md#3-low-quality-score

  # ──────────────────────────────────────────────────────────────
  # Rule 4 – High Error Rate (existing, tightened threshold)
  # ──────────────────────────────────────────────────────────────
  - name: high_error_rate
    severity: P1
    condition: error_rate_pct > 5 for 5m
    type: symptom-based
    owner: team-oncall
    description: >
      More than 5% of requests are failing. Immediate investigation
      required to prevent SLO burn-rate exhaustion.
    runbook: docs/alerts.md#4-high-error-rate

  # ──────────────────────────────────────────────────────────────
  # Rule 5 – Chi phí hôm nay tăng > 30% so với trung bình 7 ngày
  # ──────────────────────────────────────────────────────────────
  - name: daily_cost_vs_7day_avg
    severity: P2
    condition: today_cost_usd > 1.3 * avg_7day_cost_usd
    type: trend-based
    owner: finops-owner
    description: >
      Today's accumulated cost has exceeded 130% of the 7-day rolling
      average. This is an early warning that the daily_cost_usd SLO
      objective of $2.50 may be breached before end of day.
      Common causes: new feature rollout, traffic spike, or prompt length increase.
    notification: slack-channel-finops
    runbook: docs/alerts.md#5-daily-cost-vs-7day-avg

  # ──────────────────────────────────────────────────────────────
  # Rule 6 – 1 user chiếm > 10% tổng chi phí trong 24h
  # ──────────────────────────────────────────────────────────────
  - name: single_user_cost_dominance
    severity: P2
    condition: max(user_cost_24h) / total_cost_24h > 0.10
    type: anomaly-based
    owner: team-oncall
    description: >
      A single user account has consumed more than 10% of the total
      system cost in the last 24 hours. In a system with 50+ users,
      this is statistically abnormal and may indicate API abuse,
      a runaway bot, or an infinite retry loop in a client integration.
    notification: slack-channel-oncall
    runbook: docs/alerts.md#6-single-user-cost-dominance

```
- [SAMPLE_RUNBOOK_LINK]: [docs/alerts.md#1-high-latency-p95] | [docs/alerts.md#L3]

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow, cost_spike
- [SYMPTOMS_OBSERVED]: Latency P95 tăng vọt từ 150ms lên 2,750ms ngay sau khi kích hoạt incident.
Chi phí trung bình mỗi request tăng 400% (từ $0.002 lên $0.008).
Hệ thống bắt đầu vi phạm SLO về Latency (< 3000ms) khi chạy load test ở mức concurrency = 5.
- [ROOT_CAUSE_PROVED_BY]: (List specific Trace ID or Log Line)
- [FIX_ACTION]: Tắt toggle incident, đề xuất áp dụng Cache cho RAG và giới hạn max_tokens cho LLM.
- [PREVENTIVE_MEASURE]: Thiết lập Alert P2 khi Latency P95 > 2s trong 5 phút để phát hiện sớm hiện tượng nghẽn cổ chai.

---

## 5. Individual Contributions & Evidence

### [MEMBER_A_NAME]: Hoàng Bá Minh Quang
- [TASKS_COMPLETED]: 
  - **Tech Lead:** Phân công nhiệm vụ, điều phối dự án, hỗ trợ các thành viên khác fix bug.
  - **Vận hành hệ thống Logging & Middleware:** Hoàn thiện `app/middleware.py` (correlation_id) và Log Enrichment trong `app/main.py`.
  - **Bảo mật & PII:** Kích hoạt bộ lọc PII trong `app/logging_config.py` và cập nhật regex trong `app/pii.py`.
  - **Dữ liệu kiểm thử:** Tạo bộ `mock_data` (`app/mock_rag.py`) để phục vụ cho truy xuất data.
- [EVIDENCE_LINK]: 
  - [middleware.py](app/middleware.py), [main.py](app/main.py), [logging_config.py](app/logging_config.py), [pii.py](app/pii.py), [mock_rag.py](app/mock_rag.py)


### [MEMBER_B_NAME]: Đỗ Lê Thành Nhân
- [TASKS_COMPLETED]:
  - Cấu hình hệ thống: Hoàn tất cài đặt và xác minh API Key (PUBLIC_KEY, SECRET_KEY) và LANGFUSE_HOST trong file .env. Đảm bảo SDK v3 kết nối an toàn tới Langfuse Cloud.
  - Hoàn thiện Tracing Framework
  - Xây dựng Child Spans (Cây Tracing): Triển khai Decorator @observe đồng bộ trên toàn bộ pipeline: mock_rag.py (loại span) và mock_llm.py (loại generation). Kết quả là UI Langfuse hiển thị mô hình cây (Tree structure) trực quan, cho thấy rõ thời gian xử lý của từng bước RAG và LLM.
  - Log Feedback & Quality: Tích hợp thành công cơ chế chấm điểm tự động. Mỗi yêu cầu của Agent đều được tính toán quality_score và đẩy trực tiếp lên Langfuse UI bằng langfuse_context.score(), cho phép theo dõi chất lượng câu trả lời theo thời gian thực.

- [EVIDENCE_LINK]:
Các [file](app/agent.py), [file](app/tracing.py), [file](app/mock_llm.py) đã được commit và rebase thành công lên nhánh chính.

### [MEMBER_C_NAME] Nguyễn Anh Tài
- [TASKS_COMPLETED]:
  - Hiệu chỉnh các mục tiêu SLO trong config/slo.yaml (Độ trễ < 1500ms, Tỷ lệ lỗi < 2%, Chi phí < $2.5).
  - Xây dựng 4 quy tắc cảnh báo có thể hành động trong config/alert_rules.yaml, kèm người phụ trách và mức độ nghiêm trọng.
  - Phát triển tài liệu Runbook ứng phó sự cố đầy đủ trong docs/alerts.md với các bước giảm thiểu dành cho kỹ sư trực on-call.
- [[config/alert_rules.yaml][docs/alerts.md]]: 

### [MEMBER_D_NAME] Trần Quang Long
- [TASKS_COMPLETED]:
Thiết kế và triển khai bộ 50 stress test cases đa dạng (PII, Prompt Injection, Long Context) để kiểm thử giới hạn hệ thống.
Thực hiện mô phỏng tải (Load Testing) với nhiều mức độ concurrency (1, 5, 10) để xác định điểm gãy (Breaking point) của hạ tầng.
Kích hoạt các kịch bản sự cố (Chaos Engineering) để kiểm chứng khả năng phát hiện lỗi của Dashboard và hệ thống Tracing.
Hỗ trợ Member A audit file logs nhằm đảm bảo 100% dữ liệu nhạy cảm (thẻ tín dụng, email) được che giấu thành công.
- [[EVIDENCE_LINK](https://github.com/minquan-alt/Lab13-Observability/blob/main/data/sample_queries.jsonl)]: 

### [MEMBER_E_NAME] Nguyễn Công Quốc Huy
- [TASKS_COMPLETED]: 
Thiết kế và triển khai dashboard observability gồm 6 panels chính:
  - Traffic (Request volume)
  - Error Rate
  - Latency (P50, P95, P99)
  - Cost (average & total)
  - Quality score
  - Total Errors
Xây dựng UI dashboard bằng FastAPI + HTML + Chart.js:
  - Tạo endpoint /dashboard
  - Render giao diện trực tiếp từ backend (không cần frontend riêng)
  - Thiết kế layout dạng grid + section (System / Performance / Cost)
- [EVIDENCE_LINK](screenshots/dashboard-1.jpeg)

---