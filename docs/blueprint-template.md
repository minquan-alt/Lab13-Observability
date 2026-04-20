# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: 
- [REPO_URL]: 
- [MEMBERS]:
  - Member A: [Name] | Role: Logging & PII
  - Member B: [Name] | Role: Tracing & Enrichment
  - Member C: [Name] | Role: SLO & Alerts
  - Member D: [Name] | Role: Load Test & Dashboard
  - Member E: [Name] | Role: Demo & Report

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: /100
- [TOTAL_TRACES_COUNT]: 
- [PII_LEAKS_FOUND]: 

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: [Path to image]
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: [Path to image]
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: [Path to image]
- [TRACE_WATERFALL_EXPLANATION]: (Briefly explain one interesting span in your trace)

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: [Path to image]
- [SLO_TABLE]:
| SLI         |     Target | Window | Current Value |
| ----------- | ---------: | ------ | ------------: |
| Latency P95 |   < 3000ms | 28d    |               |
| Error Rate  |       < 2% | 28d    |               |
| Cost Budget | < $2.5/day | 1d     |               |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: [Path to image]
- [SAMPLE_RUNBOOK_LINK]: [docs/alerts.md#L...]

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: (e.g., rag_slow)
- [SYMPTOMS_OBSERVED]: 
- [ROOT_CAUSE_PROVED_BY]: (List specific Trace ID or Log Line)
- [FIX_ACTION]: 
- [PREVENTIVE_MEASURE]: 

---

## 5. Individual Contributions & Evidence

### [MEMBER_A_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: (Link to specific commit or PR)

### [MEMBER_B_NAME]: Đỗ Lê Thành Nhân
- [TASKS_COMPLETED]:
  - Cấu hình hệ thống: Hoàn tất cài đặt và xác minh API Key (PUBLIC_KEY, SECRET_KEY) và LANGFUSE_HOST trong file .env. Đảm bảo SDK v3 kết nối an toàn tới Langfuse Cloud.
  - Hoàn thiện Tracing Framework
  - Xây dựng Child Spans (Cây Tracing): Triển khai Decorator @observe đồng bộ trên toàn bộ pipeline: mock_rag.py (loại span) và mock_llm.py (loại generation). Kết quả là UI Langfuse hiển thị mô hình cây (Tree structure) trực quan, cho thấy rõ thời gian xử lý của từng bước RAG và LLM.
  - Log Feedback & Quality: Tích hợp thành công cơ chế chấm điểm tự động. Mỗi yêu cầu của Agent đều được tính toán quality_score và đẩy trực tiếp lên Langfuse UI bằng langfuse_context.score(), cho phép theo dõi chất lượng câu trả lời theo thời gian thực.

- [EVIDENCE_LINK]:
Các [file](app/agent.py), [file](app/tracing.py), [file](app/mock_llm.py) đã được commit và rebase thành công lên nhánh chính.

### [MEMBER_C_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### [MEMBER_D_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]:


### [MEMBER_E_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
