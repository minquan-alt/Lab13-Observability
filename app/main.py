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
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

        <style>
            * { box-sizing: border-box; }

            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                background: #0f172a;
                color: white;
                padding: 20px;
                margin: 0;
            }

            h1 { text-align: center; margin-bottom: 10px; }
            h2 { margin-top: 30px; color: #94a3b8; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }

            .grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
            }

            .card {
                background: #1e293b;
                padding: 18px;
                border-radius: 10px;
                text-align: center;
                border: 2px solid transparent;
                transition: border-color 0.4s, background 0.4s;
            }

            .card.alert-p1 { border-color: #ef4444; background: #2d1212; animation: pulse-red 1s infinite; }
            .card.alert-p2 { border-color: #f59e0b; background: #2d220c; }
            .card.alert-p3 { border-color: #facc15; background: #2d2b0c; }
            .card.ok       { border-color: #22c55e; }

            @keyframes pulse-red {
                0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }
                50%       { box-shadow: 0 0 12px 4px rgba(239,68,68,0.6); }
            }

            .value {
                font-size: 24px;
                font-weight: bold;
                margin-top: 8px;
            }
            .value.red    { color: #ef4444; }
            .value.yellow { color: #f59e0b; }
            .value.green  { color: #22c55e; }

            .chart-container {
                background: #1e293b;
                padding: 16px;
                border-radius: 10px;
                margin-top: 20px;
                position: relative;
                height: 300px;
            }

            canvas { width: 100% !important; }

            /* ── ALERT PANEL ─────────────────────────────────── */
            #alert-banner {
                display: none;
                background: #7f1d1d;
                border: 1px solid #ef4444;
                border-radius: 8px;
                padding: 10px 16px;
                margin-bottom: 16px;
                font-size: 14px;
                animation: pulse-red 1s infinite;
            }

            .alert-table { width: 100%; border-collapse: collapse; margin-top: 6px; }
            .alert-table th, .alert-table td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #334155; font-size: 13px; }
            .alert-table th { color: #94a3b8; font-weight: 600; }
            .badge {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 9999px;
                font-size: 11px;
                font-weight: bold;
            }
            .badge-p1 { background: #ef4444; color: white; }
            .badge-p2 { background: #f59e0b; color: black; }
            .badge-p3 { background: #facc15; color: black; }
            .badge-ok  { background: #22c55e; color: black; }

            a.runbook { color: #38bdf8; font-size: 12px; }

            /* ── CONTROLS ───────────────────────────────────── */
            .controls {
                text-align: center;
                margin-top: 20px;
            }

            button {
                padding: 8px 16px;
                margin: 0 5px;
                border: 1px solid #334155;
                border-radius: 6px;
                cursor: pointer;
                background: #1e293b;
                color: #94a3b8;
                font-weight: 600;
                transition: all 0.2s;
            }

            button.active {
                background: #3b82f6;
                color: white;
                border-color: #3b82f6;
            }
        </style>
    </head>

    <body>
        <h1>📊 Observability Dashboard</h1>

        <!-- 🚨 ALERT BANNER (hiện khi có P1) -->
        <div id="alert-banner">
            🚨 <strong>CRITICAL ALERT ACTIVE</strong> — Xem bảng Alert bên dưới để biết chi tiết.
        </div>

        <!-- 🚨 ALERT PANEL -->
        <h2>🚨 Active Alerts</h2>
        <div style="background:#1e293b; border-radius:10px; padding:16px;">
            <table class="alert-table">
                <thead>
                    <tr>
                        <th>Rule</th>
                        <th>Severity</th>
                        <th>Status</th>
                        <th>Current Value</th>
                        <th>Threshold</th>
                        <th>Runbook</th>
                    </tr>
                </thead>
                <tbody id="alert-rows">
                    <tr><td colspan="6" style="color:#64748b;">Loading…</td></tr>
                </tbody>
            </table>
        </div>

        <!-- SYSTEM HEALTH -->
        <h2>🟦 System Health</h2>
        <div class="grid">
            <div class="card" id="card-traffic">
                <div>Traffic</div>
                <div class="value" id="traffic">-</div>
            </div>
            <div class="card" id="card-error-rate">
                <div>Error Rate</div>
                <div class="value" id="error_rate">-</div>
            </div>
            <div class="card" id="card-errors">
                <div>Total Errors</div>
                <div class="value" id="errors">-</div>
            </div>
        </div>

        <!-- CHART & TOGGLES -->
        <div class="controls">
            <button id="btnTraffic" class="active">Traffic Volume</button>
            <button id="btnTokens">Token Usage</button>
        </div>
        <div class="chart-container">
            <canvas id="mainChart"></canvas>
        </div>

        <!-- PERFORMANCE -->
        <h2>🟨 Performance</h2>
        <div class="grid">
            <div class="card" id="card-p50"><div>P50 Latency</div><div class="value" id="p50">-</div></div>
            <div class="card" id="card-p95"><div>P95 Latency</div><div class="value" id="p95">-</div></div>
            <div class="card" id="card-p99"><div>P99 Latency</div><div class="value" id="p99">-</div></div>
        </div>

        <!-- COST & QUALITY -->
        <h2>🟩 Cost & Quality</h2>
        <div class="grid">
            <div class="card" id="card-cost"><div>Total Cost (USD)</div><div class="value" id="cost">-</div></div>
            <div class="card" id="card-quality"><div>Avg Quality Score</div><div class="value" id="quality">-</div></div>
        </div>

        <script>
            // ── GLOBAL STATE ──────────────────────────────────
            let currentMode = "traffic"; // "traffic" or "tokens"

            // ── Chart.js setup ────────────────────────────────
            const ctx = document.getElementById('mainChart').getContext('2d');
            const chart = new Chart(ctx, {
                type: 'bar',
                data: { labels: [], datasets: [] },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { stacked: false, ticks: { autoSkip: false, color: '#94a3b8' }, grid: { color: '#1e293b' } },
                        y: { stacked: false, beginAtZero: true, ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
                    },
                    plugins: { legend: { labels: { color: '#94a3b8' } } }
                }
            });

            function getLast7Days() {
                const days = [];
                const today = new Date();
                for (let i = 6; i >= 0; i--) {
                    const d = new Date();
                    d.setDate(today.getDate() - i);
                    days.push(d.toISOString().slice(0, 10));
                }
                return days;
            }

            // ── Alert rule definitions ────────────────────────
            const ALERT_RULES = [
                {
                    id: 'high_error_rate',
                    label: 'High Error Rate',
                    severity: 'P1',
                    getValue: d => {
                        const errs = Object.values(d.error_breakdown || {}).reduce((a,b)=>a+b,0);
                        return d.traffic > 0 ? (errs / d.traffic * 100) : 0;
                    },
                    isFiring: v => v > 5,
                    format: v => v.toFixed(2) + '%',
                    threshold: '> 5%',
                    runbook: 'docs/alerts.md#4-high-error-rate',
                    cardId: 'card-error-rate',
                    valueId: 'error_rate',
                },
                {
                    id: 'high_latency_p95',
                    label: 'High Latency P95',
                    severity: 'P2',
                    getValue: d => d.latency_p95 ?? 0,
                    isFiring: v => v > 1500,
                    format: v => v + ' ms',
                    threshold: '> 1500 ms',
                    runbook: 'docs/alerts.md#1-high-latency-p95',
                    cardId: 'card-p95',
                    valueId: 'p95',
                },
                {
                    id: 'cost_budget_spike',
                    label: 'Cost Budget Spike',
                    severity: 'P2',
                    getValue: d => d.total_cost_usd ?? 0,
                    isFiring: v => v > 2.5,
                    format: v => '$' + v.toFixed(4),
                    threshold: '> $2.50/day',
                    runbook: 'docs/alerts.md#2-cost-budget-spike',
                    cardId: 'card-cost',
                    valueId: 'cost',
                },
                {
                    id: 'low_quality_score',
                    label: 'Low Quality Score',
                    severity: 'P3',
                    getValue: d => d.quality_avg ?? 1,
                    isFiring: v => v < 0.70 && v > 0,
                    format: v => v.toFixed(3),
                    threshold: '< 0.70',
                    runbook: 'docs/alerts.md#3-low-quality-score',
                    cardId: 'card-quality',
                    valueId: 'quality',
                },
            ];

            function applyCardState(cardId, firing, severity) {
                const card = document.getElementById(cardId);
                if (!card) return;
                card.className = 'card';
                if (firing) {
                    card.classList.add(severity === 'P1' ? 'alert-p1' : severity === 'P2' ? 'alert-p2' : 'alert-p3');
                } else {
                    card.classList.add('ok');
                }
            }

            async function updateDashboard() {
                try {
                    const res = await fetch("/metrics");
                    const data = await res.json();

                    // ── Basic metrics ──────────────────────────
                    const totalErrors = Object.values(data.error_breakdown || {}).reduce((a,b)=>a+b,0);
                    const errorRatePct = data.traffic > 0 ? (totalErrors / data.traffic * 100).toFixed(2) : 0;

                    document.getElementById("traffic").innerText = data.traffic ?? 0;
                    document.getElementById("error_rate").innerText = errorRatePct + '%';
                    document.getElementById("errors").innerText = totalErrors;
                    document.getElementById("p50").innerText = (data.latency_p50 ?? 0) + " ms";
                    document.getElementById("p95").innerText = (data.latency_p95 ?? 0) + " ms";
                    document.getElementById("p99").innerText = (data.latency_p99 ?? 0) + " ms";
                    document.getElementById("cost").innerText = '$' + (data.total_cost_usd ?? 0).toFixed(4);
                    document.getElementById("quality").innerText = (data.quality_avg ?? 0).toFixed(3);

                    // ── Chart Update ──────────────────────────
                    const days = getLast7Days();
                    chart.data.labels = days;

                    if (currentMode === "traffic") {
                        const trafficData = data.traffic_by_day || {};
                        chart.data.datasets = [{
                            label: "Requests",
                            data: days.map(d => trafficData[d] || 0),
                            backgroundColor: '#3b82f6',
                            borderRadius: 4
                        }];
                        chart.options.scales.x.stacked = false;
                        chart.options.scales.y.stacked = false;
                    } else {
                        // FALLBACK if tokens_in_by_day doesn't exist yet in metrics.py
                        const tIn = data.tokens_in_by_day || {};
                        const tOut = data.tokens_out_by_day || {};
                        chart.data.datasets = [
                            { label: "Tokens In", data: days.map(d => tIn[d] || (data.tokens_in_total/7 || 0)), backgroundColor: '#10b981', borderRadius: 4 },
                            { label: "Tokens Out", data: days.map(d => tOut[d] || (data.tokens_out_total/7 || 0)), backgroundColor: '#8b5cf6', borderRadius: 4 }
                        ];
                        chart.options.scales.x.stacked = true;
                        chart.options.scales.y.stacked = true;
                    }
                    chart.update();

                    // ── Alerts Evaluation ──────────────────────
                    let hasP1 = false;
                    const rows = ALERT_RULES.map(rule => {
                        const val = rule.getValue(data);
                        const firing = rule.isFiring(val);
                        if (firing && rule.severity === 'P1') hasP1 = true;

                        applyCardState(rule.cardId, firing, rule.severity);

                        let badgeClass = firing ? `badge-${rule.severity.toLowerCase()}` : 'badge-ok';
                        let statusText = firing ? `🔴 FIRING` : `✅ OK`;
                        let runbookHtml = firing ? `<a class="runbook" href="${rule.runbook}" target="_blank">📖 Runbook</a>` : `—`;

                        return `<tr>
                            <td><strong>${rule.label}</strong></td>
                            <td><span class="badge ${badgeClass}">${rule.severity}</span></td>
                            <td>${statusText}</td>
                            <td>${rule.isFiring(val) ? rule.format(val) : '—'}</td>
                            <td style="color:#64748b;">${rule.threshold}</td>
                            <td>${runbookHtml}</td>
                        </tr>`;
                    }).join('');

                    document.getElementById("alert-rows").innerHTML = rows;
                    document.getElementById("alert-banner").style.display = hasP1 ? 'block' : 'none';

                } catch (e) {
                    console.error("Dashboard error:", e);
                }
            }

            // ── Toggles ──────────────────────────────────────
            document.getElementById("btnTraffic").onclick = () => {
                currentMode = "traffic";
                document.getElementById("btnTraffic").classList.add("active");
                document.getElementById("btnTokens").classList.remove("active");
                updateDashboard();
            };
            document.getElementById("btnTokens").onclick = () => {
                currentMode = "tokens";
                document.getElementById("btnTokens").classList.add("active");
                document.getElementById("btnTraffic").classList.remove("active");
                updateDashboard();
            };

            setInterval(updateDashboard, 3000);
            updateDashboard();
        </script>
    </body>
    </html>
    """