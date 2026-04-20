from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from structlog.contextvars import bind_contextvars

from .agent import LabAgent
from .incidents import disable, enable, status
from .logging_config import configure_logging, get_logger
from .metrics import record_error, snapshot
from .middleware import CorrelationIdMiddleware
from .pii import hash_user_id, summarize_text
from .schemas import ChatRequest, ChatResponse
from .tracing import tracing_enabled

configure_logging()
log = get_logger()
app = FastAPI(title="Day 13 Observability Lab")
app.add_middleware(CorrelationIdMiddleware)
agent = LabAgent()


@app.on_event("startup")
async def startup() -> None:
    log.info(
        "app_started",
        service=os.getenv("APP_NAME", "day13-observability-lab"),
        env=os.getenv("APP_ENV", "dev"),
        payload={"tracing_enabled": tracing_enabled()},
    )


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "tracing_enabled": tracing_enabled(), "incidents": status()}


@app.get("/metrics")
async def metrics() -> dict:
    return snapshot()


@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    # TODO: Enrich logs with request context (user_id_hash, session_id, feature, model, env)
    bind_contextvars(
        user_id_hash=hash_user_id(body.user_id),
        session_id=body.session_id or "unknown",
        feature=body.feature or "chat",
        model=body.model or "default",
        env=os.getenv("APP_ENV", "dev"),
    )

    log.info(   
        "request_received",
        service=os.getenv("APP_NAME", "api"),
        payload={"message_preview": summarize_text(body.message)},
    )
    try:
        result = agent.run(
            user_id=body.user_id,
            feature=body.feature,
            session_id=body.session_id,
            message=body.message,
        )
        log.info(
            "response_sent",
            service="api",
            latency_ms=result.latency_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            payload={"answer_preview": summarize_text(result.answer)},
        )
        return ChatResponse(
            answer=result.answer,
            correlation_id=request.state.correlation_id,
            latency_ms=result.latency_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            quality_score=result.quality_score,
        )
    except Exception as exc:  # pragma: no cover
        error_type = type(exc).__name__
        record_error(error_type)
        log.error(
            "request_failed",
            service="api",
            error_type=error_type,
            payload={"detail": str(exc), "message_preview": summarize_text(body.message)},
        )
        raise HTTPException(status_code=500, detail=error_type) from exc


@app.post("/incidents/{name}/enable")
async def enable_incident(name: str) -> JSONResponse:
    try:
        enable(name)
        log.warning("incident_enabled", service="control", payload={"name": name})
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/incidents/{name}/disable")
async def disable_incident(name: str) -> JSONResponse:
    try:
        disable(name)
        log.warning("incident_disabled", service="control", payload={"name": name})
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

from fastapi.responses import HTMLResponse

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Observability Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

        <style>
            body {
                font-family: Arial;
                background: #0f172a;
                color: white;
                padding: 20px;
            }

            h1 {
                text-align: center;
            }

            h2 {
                margin-top: 30px;
                color: #94a3b8;
            }

            .grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
            }

            .card {
                background: #1e293b;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
            }

            .value {
                font-size: 24px;
                font-weight: bold;
                margin-top: 10px;
            }

            canvas {
                background: #1e293b;
                padding: 10px;
                border-radius: 10px;
                margin-top: 20px;
            }
        </style>
    </head>

    <body>
        <h1>📊 Observability Dashboard</h1>

        <h2>🟦 System Health</h2>
        <div class="grid">
            <div class="card">
                <div>Traffic</div>
                <div class="value" id="traffic">-</div>
            </div>

            <div class="card">
                <div>Error Rate</div>
                <div class="value" id="error_rate">-</div>
            </div>

            <div class="card">
                <div>Total Errors</div>
                <div class="value" id="errors">-</div>
            </div>
        </div>

        <!-- 🔥 GRAPH -->
        <canvas id="trafficChart"></canvas>

        <h2>🟨 Performance</h2>
        <div class="grid">
            <div class="card"><div>P50</div><div class="value" id="p50">-</div></div>
            <div class="card"><div>P95</div><div class="value" id="p95">-</div></div>
            <div class="card"><div>P99</div><div class="value" id="p99">-</div></div>
        </div>

        <h2>🟩 Cost & Quality</h2>
        <div class="grid">
            <div class="card"><div>Avg Cost</div><div class="value" id="cost">-</div></div>
            <div class="card"><div>Quality</div><div class="value" id="quality">-</div></div>
        </div>

        <script>
            const ctx = document.getElementById('trafficChart').getContext('2d');

            const chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Requests (7 days)',
                        data: []
                    }]
                },
                options: {
                    scales: {
                        x: {
                            ticks: {
                                autoSkip: false   // 🔥 tránh mất cột
                            }
                        },
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });

            // 🔥 luôn tạo đủ 7 ngày + label KHÔNG TRÙNG
            function getLast7Days(data) {
                const result = [];
                const today = new Date();

                for (let i = 6; i >= 0; i--) {
                    const d = new Date();
                    d.setDate(today.getDate() - i);

                    const key = d.toISOString().slice(0, 10); // YYYY-MM-DD

                    result.push({
                        label: key,   // 🔥 QUAN TRỌNG: unique label
                        value: data[key] || 0
                    });
                }

                return result;
            }

            async function updateDashboard() {
                try {
                    const res = await fetch("/metrics");
                    const data = await res.json();

                    const totalErrors = Object.values(data.error_breakdown || {})
                        .reduce((a, b) => a + b, 0);

                    const errorRate = data.traffic > 0
                        ? (totalErrors / data.traffic).toFixed(3)
                        : 0;

                    // cards
                    document.getElementById("traffic").innerText = data.traffic ?? 0;
                    document.getElementById("error_rate").innerText = errorRate;
                    document.getElementById("errors").innerText = totalErrors;

                    document.getElementById("p50").innerText = (data.latency_p50 ?? 0) + " ms";
                    document.getElementById("p95").innerText = (data.latency_p95 ?? 0) + " ms";
                    document.getElementById("p99").innerText = (data.latency_p99 ?? 0) + " ms";

                    document.getElementById("cost").innerText = data.avg_cost_usd ?? 0;
                    document.getElementById("quality").innerText = data.quality_avg ?? 0;

                    // 🔥 ALWAYS fallback
                    const trafficData = data.traffic_by_day || {};

                    const last7 = getLast7Days(trafficData);

                    console.log("DEBUG last7:", last7); // 👈 check ở console

                    chart.data.labels = last7.map(x => x.label);
                    chart.data.datasets[0].data = last7.map(x => x.value);

                    chart.update();

                } catch (e) {
                    console.error("Dashboard error:", e);
                }
            }

            setInterval(updateDashboard, 3000);
            updateDashboard();
        </script>
    </body>
    </html>
    """