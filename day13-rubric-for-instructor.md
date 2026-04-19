# Rubric chấm điểm giảng viên - Day 13 Observability Lab

## Mục tiêu chấm
Rubric này mở rộng trực tiếp từ deliverable trong slide: logging JSON có correlation ID và PII sanitization, ít nhất 10 traces, dashboard 6 panels, SLO + alert rules có runbook, và blueprint document. Nó cũng bổ sung phần đánh giá demo, debug, và đóng góp cá nhân để phù hợp buổi lab 4 tiếng. 

**Tổng điểm: 100 + 10 bonus**

---

## A. Logging & Tracing - 30 điểm

### A1. Structured logging - 10 điểm
- 0: log rời rạc, không JSON
- 4: JSON nhưng thiếu field bắt buộc
- 7: JSON đúng schema cơ bản, có `ts`, `level`, `service`, `event`, `correlation_id`
- 10: JSON đúng schema, có context đầy đủ (`feature`, `model`, `session_id`, `user_id_hash`) và query được

### A2. Correlation ID propagation - 10 điểm
- 0: không có correlation ID
- 5: có nhưng chỉ hiện ở một phần log
- 8: đi xuyên suốt request flow
- 10: grep/search được cả flow theo một ID, demo được live

### A3. Tracing - 10 điểm
- 0: không có trace
- 4: trace có nhưng rời rạc hoặc < 10 traces
- 7: >= 10 traces, có tags cơ bản
- 10: trace có waterfall rõ, có cost/tokens/metadata, dùng được để debug

---

## B. Dashboard & Alerts - 25 điểm

### B1. Dashboard Layer 2 - 10 điểm
- 0: chưa có dashboard
- 4: có dashboard nhưng dưới 6 panels
- 7: đủ 6 panels
- 10: 6 panels rõ ràng, có đơn vị, threshold/SLO line, time range hợp lý

### B2. SLO definition - 5 điểm
- 0: không có SLO
- 3: có SLO nhưng mơ hồ
- 5: có bảng SLO rõ cho latency, error, cost, quality proxy

### B3. Alert rules + runbook - 10 điểm
- 0: không có alert
- 4: có alert nhưng không actionable
- 7: có >= 3 alert rules
- 10: alert symptom-based, có severity, owner, runbook link, và demo giải thích được

---

## C. Debugging & Incident Response - 25 điểm

### C1. Root cause identification - 15 điểm
- 0: không xác định được
- 5: đoán đúng một phần nhưng không có bằng chứng
- 10: xác định đúng nguyên nhân với metrics hoặc logs hoặc traces
- 15: xác định đúng bằng flow metrics -> traces -> logs

### C2. Explanation quality - 10 điểm
- 0: trả lời mơ hồ
- 4: có giải thích nhưng thiếu logic
- 7: giải thích rõ triệu chứng, dữ kiện, nguyên nhân
- 10: giải thích chặt chẽ, nêu được fix và preventive action

---

## D. Team contribution - 10 điểm

### D1. Evidence of contribution - 5 điểm
- 0: không có evidence
- 3: một vài thành viên có vai trò, thiếu rõ ràng
- 5: có phân công và bằng chứng qua commit/demo/report

### D2. Shared participation in demo - 5 điểm
- 0: 1 người nói toàn bộ
- 3: 2 người tham gia
- 5: >= 3 người tham gia, trả lời được câu hỏi đúng phần phụ trách

---

## E. Demo quality - 10 điểm

### E1. Live demo - 5 điểm
- 0: không chạy được
- 3: chạy được một phần
- 5: code chạy live, trace/log/dashboard đều hiển thị

### E2. Communication - 5 điểm
- 0: khó hiểu
- 3: hiểu được nhưng rời rạc
- 5: ngắn gọn, rõ ràng, đúng thuật ngữ, đúng flow demo

---

## Bonus - 10 điểm
- +3: cost optimization có số liệu trước/sau
- +3: quality metric hoặc quality proxy hợp lý
- +2: auto-instrumentation hoặc OTel semconv rõ ràng
- +2: có audit log tách riêng app log

---

## Điều kiện qua bài
- Có app chạy được
- Có log JSON với correlation ID
- Có ít nhất 10 traces
- Có dashboard 6 panels
- Có 3 alert rules
- Có blueprint document nộp cuối ngày

---

## Phiếu chấm nhanh
| Hạng mục | Điểm tối đa | Điểm nhóm |
|---|---:|---:|
| Logging & Tracing | 30 | |
| Dashboard & Alerts | 25 | |
| Debugging | 25 | |
| Team contribution | 10 | |
| Demo | 10 | |
| Bonus | 10 | |
| **Tổng** | **100 + 10** | |

## Nhận xét nhanh
- Điểm mạnh:
- Vấn đề chính:
- Root cause có được chứng minh tốt không:
- Khuyến nghị cải thiện:
