import os
import socket
import time
from flask import Flask, render_template_string, jsonify, request
import redis

app = Flask(__name__)

# Configuration from Environment Variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", 0))
CLUSTER_NAME = os.getenv("CLUSTER_NAME", "Local / Primary Cluster")
ENVIRONMENT = os.getenv("ENVIRONMENT", "Development / On-Premises")
APP_VERSION = os.getenv("APP_VERSION", "v1.0.0")

# Redis Connection with retry and timeout configuration
def get_redis_client():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        db=REDIS_DB,
        socket_connect_timeout=2,
        socket_timeout=2,
        decode_responses=True
    )

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloud Visitor Counter</title>
    <style>
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary: #059669;
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --border: #e2e8f0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 2rem 1rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }
        .container {
            max-width: 680px;
            width: 100%;
        }
        .header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .badge {
            display: inline-block;
            padding: 0.35rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.75rem;
        }
        .badge-cloud {
            background-color: #dbeafe;
            color: #1e40af;
        }
        .badge-status {
            background-color: #dcfce7;
            color: #15803d;
        }
        .badge-error {
            background-color: #fee2e2;
            color: #b91c1c;
        }
        h1 {
            font-size: 2.25rem;
            margin: 0.5rem 0;
            color: var(--text-main);
            font-weight: 800;
        }
        .subtitle {
            color: var(--text-muted);
            font-size: 1rem;
            margin: 0;
        }
        .counter-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
            padding: 2.5rem;
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .counter-label {
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }
        .counter-number {
            font-size: 4.5rem;
            font-weight: 900;
            color: var(--primary);
            line-height: 1.1;
            margin: 0.75rem 0;
            font-feature-settings: "tnum";
        }
        .info-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
        }
        .info-item {
            display: flex;
            flex-direction: column;
        }
        .info-key {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--text-muted);
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
        }
        .info-value {
            font-size: 0.95rem;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            color: var(--text-main);
            background: #f1f5f9;
            padding: 0.35rem 0.6rem;
            border-radius: 6px;
            word-break: break-all;
        }
        .actions {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-top: 1.5rem;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            font-size: 0.95rem;
            border-radius: 8px;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s ease;
            border: none;
        }
        .btn-primary {
            background-color: var(--primary);
            color: white;
        }
        .btn-primary:hover {
            background-color: var(--primary-dark);
        }
        .btn-secondary {
            background-color: #f1f5f9;
            color: var(--text-main);
            border: 1px solid var(--border);
        }
        .btn-secondary:hover {
            background-color: #e2e8f0;
        }
        .footer {
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 2rem;
        }
        @media (max-width: 600px) {
            .info-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="badge badge-cloud">Cloud Computing Project</span>
            <h1>Cloud Visitor Counter</h1>
            <p class="subtitle">Distributed High-Availability Web Application (Flask + Redis + Kubernetes)</p>
        </div>

        <div class="counter-card">
            <div class="counter-label">Total Visits Tracked</div>
            {% if redis_ok %}
                <div class="counter-number">{{ visits }}</div>
                <div><span class="badge badge-status">Redis Connected & Active</span></div>
            {% else %}
                <div class="counter-number" style="color: #ef4444;">Offline</div>
                <div><span class="badge badge-error">Redis Disconnected: {{ error_msg }}</span></div>
            {% endif %}
            
            <div class="actions">
                <a href="/" class="btn btn-primary">Refresh Count (+1)</a>
                <a href="/healthz" class="btn btn-secondary">Health Check</a>
            </div>
        </div>

        <div class="info-card">
            <h3 style="margin-top: 0; margin-bottom: 1rem; font-size: 1.1rem;">Cluster & Runtime Telemetry</h3>
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-key">Active Cluster</span>
                    <span class="info-value">{{ cluster_name }}</span>
                </div>
                <div class="info-item">
                    <span class="info-key">Deployment Environment</span>
                    <span class="info-value">{{ environment }}</span>
                </div>
                <div class="info-item">
                    <span class="info-key">Serving Pod / Hostname</span>
                    <span class="info-value">{{ hostname }}</span>
                </div>
                <div class="info-item">
                    <span class="info-key">Pod IP Address</span>
                    <span class="info-value">{{ host_ip }}</span>
                </div>
                <div class="info-item">
                    <span class="info-key">Application Version</span>
                    <span class="info-value">{{ app_version }}</span>
                </div>
                <div class="info-item">
                    <span class="info-key">Timestamp (UTC)</span>
                    <span class="info-value">{{ timestamp }}</span>
                </div>
            </div>
        </div>

        <div class="footer">
            Cloud Computing Small Project &bull; Kubernetes &bull; HPA &bull; Hybrid Cloud Failover &bull; Cost Optimization
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    hostname = socket.gethostname()
    try:
        host_ip = socket.gethostbyname(hostname)
    except Exception:
        host_ip = "127.0.0.1"

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    redis_ok = True
    visits = 0
    error_msg = ""

    try:
        r = get_redis_client()
        visits = r.incr("visitor_count")
    except Exception as e:
        redis_ok = False
        error_msg = str(e)

    return render_template_string(
        HTML_TEMPLATE,
        visits=visits,
        redis_ok=redis_ok,
        error_msg=error_msg,
        hostname=hostname,
        host_ip=host_ip,
        cluster_name=CLUSTER_NAME,
        environment=ENVIRONMENT,
        app_version=APP_VERSION,
        timestamp=timestamp
    )

@app.route("/healthz")
@app.route("/health")
def health():
    """Liveness probe endpoint."""
    return jsonify({
        "status": "healthy",
        "cluster": CLUSTER_NAME,
        "environment": ENVIRONMENT,
        "hostname": socket.gethostname(),
        "timestamp": time.time()
    }), 200

@app.route("/ready")
def readiness():
    """Readiness probe endpoint: verifies Redis backend connectivity."""
    try:
        r = get_redis_client()
        r.ping()
        return jsonify({
            "status": "ready",
            "redis": "connected",
            "cluster": CLUSTER_NAME,
            "hostname": socket.gethostname()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "not_ready",
            "redis": "error",
            "error": str(e),
            "cluster": CLUSTER_NAME
        }), 503

@app.route("/load")
def simulate_load():
    """
    Simulates CPU load to facilitate HPA (Horizontal Pod Autoscaling) testing.
    Usage: /load?cycles=5000000 (default: 3000000)
    """
    cycles = int(request.args.get("cycles", 3000000))
    start_time = time.time()
    # Compute intensive loop
    x = 0
    for i in range(cycles):
        x += (i * i) % 7
    elapsed = time.time() - start_time
    return jsonify({
        "message": "Load simulation completed",
        "cycles": cycles,
        "elapsed_seconds": round(elapsed, 4),
        "hostname": socket.gethostname(),
        "cluster": CLUSTER_NAME
    }), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
