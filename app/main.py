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
    try:
        bind_contextvars(
            user_id_hash=hash_user_id(body.user_id),
            session_id=body.session_id or "unknown",
            feature=body.feature or "chat",
            model=body.model or agent.model,
            env=os.getenv("APP_ENV", "dev"),
        )

        log.info(   
            "request_received",
            service=os.getenv("APP_NAME", "api"),
            payload={"message_preview": summarize_text(body.message)},
        )

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
                font-size: 28px;
                font-weight: bold;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <h1>📊 Observability Dashboard</h1>
        <div class="grid">
            <div class="card">
                <div>Request Rate</div>
                <div class="value" id="traffic">-</div>
            </div>

            <div class="card">
                <div>Error Rate</div>
                <div class="value" id="error_rate">-</div>
            </div>

            <div class="card">
                <div>Latency P95</div>
                <div class="value" id="latency">-</div>
            </div>

            <div class="card">
                <div>Avg Cost ($)</div>
                <div class="value" id="cost">-</div>
            </div>

            <div class="card">
                <div>Quality</div>
                <div class="value" id="quality">-</div>
            </div>

            <div class="card">
                <div>Total Errors</div>
                <div class="value" id="errors">-</div>
            </div>
        </div>

        <script>
            async function loadMetrics() {
                const res = await fetch("/metrics");
                const data = await res.json();

                const totalErrors = Object.values(data.error_breakdown)
                    .reduce((a, b) => a + b, 0);

                const errorRate = data.traffic > 0
                    ? (totalErrors / data.traffic).toFixed(3)
                    : 0;

                document.getElementById("traffic").innerText = data.traffic;
                document.getElementById("error_rate").innerText = errorRate;
                document.getElementById("latency").innerText = data.latency_p95 + " ms";
                document.getElementById("cost").innerText = data.avg_cost_usd;
                document.getElementById("quality").innerText = data.quality_avg;
                document.getElementById("errors").innerText = totalErrors;
            }

            setInterval(loadMetrics, 1000);
            loadMetrics();
        </script>
    </body>
    </html>
    """