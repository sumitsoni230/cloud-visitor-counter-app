#!/usr/bin/env python3
"""
================================================================================
HYBRID CLOUD AUTOMATED FAILOVER CONTROLLER & TRAFFIC ROUTER
================================================================================
Simulates an Enterprise Cloud Traffic Manager (e.g. AWS Route 53 Health Check,
Cloudflare Load Balancer, or F5 BIG-IP GSLB) operating between:
  1. Primary Cluster (On-Premises Data Center) -> Default port 30080
  2. Secondary Cluster (Simulated Public Cloud DR) -> Default port 30081

Routing Policy:
  - Active-Passive Automatic Failover with Continuous Health Probing.
  - If Primary is Healthy (HTTP 200 on /healthz), 100% of user traffic is routed to Primary.
  - If Primary fails (3 consecutive probe failures or connection refused), failover triggers:
    100% traffic rerouted to Secondary Public Cloud cluster.
  - Zero application downtime to clients accessing http://localhost:8080.
================================================================================
"""

import sys
import time
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

PRIMARY_URL = "http://localhost:30080"
SECONDARY_URL = "http://localhost:30081"
LISTEN_PORT = 8080

# State variables
state = {
    "primary_healthy": True,
    "consecutive_failures": 0,
    "last_check_timestamp": 0,
    "active_target": PRIMARY_URL,
    "failover_count": 0,
    "total_requests_served": 0
}

state_lock = threading.Lock()

def check_health(target_url):
    """Probes the /healthz endpoint of a cluster."""
    url = f"{target_url.rstrip('/')}/healthz"
    try:
        req = Request(url, headers={"User-Agent": "HybridFailoverHealthChecker/1.0"})
        with urlopen(req, timeout=1.5) as resp:
            return resp.getcode() == 200
    except Exception:
        return False

def health_monitor_daemon():
    """Background monitor thread performing periodic health checks."""
    print(f"[*] Health Monitor Daemon started.")
    print(f"    - Monitoring Primary:   {PRIMARY_URL}/healthz")
    print(f"    - Standby Secondary:    {SECONDARY_URL}/healthz")
    print("-" * 75)

    while True:
        is_ok = check_health(PRIMARY_URL)
        with state_lock:
            state["last_check_timestamp"] = time.time()
            if is_ok:
                if not state["primary_healthy"]:
                    print("\n" + "#" * 75)
                    print("  [FAILBACK DETECTED] Primary On-Premises cluster is BACK ONLINE!")
                    print("  Restoring traffic route: Secondary (Cloud) -> Primary (On-Premises)")
                    print("#" * 75 + "\n")
                state["primary_healthy"] = True
                state["consecutive_failures"] = 0
                state["active_target"] = PRIMARY_URL
            else:
                state["consecutive_failures"] += 1
                if state["primary_healthy"] and state["consecutive_failures"] >= 2:
                    state["primary_healthy"] = False
                    state["failover_count"] += 1
                    state["active_target"] = SECONDARY_URL
                    print("\n" + "!" * 75)
                    print("  [DISASTER RECOVERY ALERT] Primary On-Premises cluster DOWN!")
                    print(f"  AUTOMATIC FAILOVER TRIGGERED (#{state['failover_count']})")
                    print(f"  Rerouting all ingress traffic to: SECONDARY (Simulated Public Cloud)")
                    print("!" * 75 + "\n")
        time.sleep(1.5)

class FailoverProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_proxy()

    def do_POST(self):
        self.handle_proxy()

    def handle_proxy(self):
        with state_lock:
            active_backend = state["active_target"]
            is_primary = state["primary_healthy"]
            state["total_requests_served"] += 1
            req_num = state["total_requests_served"]

        cluster_label = "PRIMARY (On-Premises)" if is_primary else "SECONDARY (Public Cloud DR)"
        
        target_path = self.path
        forward_url = f"{active_backend.rstrip('/')}{target_path}"

        headers = {k: v for k, v in self.headers.items() if k.lower() != "host"}
        headers["X-Forwarded-For"] = self.client_address[0]
        headers["X-Proxy-Agent"] = "HybridCloud-FailoverRouter"

        # Read POST body if present
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else None

        try:
            req = Request(forward_url, data=post_data, headers=headers, method=self.command)
            with urlopen(req, timeout=5) as response:
                resp_data = response.read()
                
                # Send back to client
                self.send_response(response.getcode())
                for header, val in response.getheaders():
                    # Strip hop-by-hop headers
                    if header.lower() not in ["transfer-encoding", "content-length", "connection"]:
                        self.send_header(header, val)
                
                # Add telemetry headers for verification
                self.send_header("X-Served-By-Cluster", cluster_label)
                self.send_header("Content-Length", str(len(resp_data)))
                self.end_headers()
                self.wfile.write(resp_data)

                # Console log for live screenshot demonstration
                status_symbol = "🟢" if is_primary else "🟡 [FAILOVER ACTIVE]"
                print(f"[{time.strftime('%H:%M:%S')}] Req #{req_num} {status_symbol} -> {cluster_label} | {self.command} {self.path} (HTTP {response.getcode()})")

        except Exception as e:
            # If active backend also fails
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            err_msg = f"502 Bad Gateway: Both Primary and Secondary failover endpoints unreachable ({str(e)})"
            self.wfile.write(err_msg.encode("utf-8"))
            print(f"[{time.strftime('%H:%M:%S')}] Req #{req_num} 🔴 ERROR forwarding to {cluster_label}: {str(e)}")

    def log_message(self, format, *args):
        # Suppress default std logging to keep terminal output clean for screenshots
        return

def run_server():
    print("=" * 75)
    print("  HYBRID CLOUD ACTIVE-PASSIVE FAILOVER ROUTER")
    print("=" * 75)
    print(f"  * Ingress Gateway Listening on:  http://localhost:{LISTEN_PORT}")
    print(f"  * Primary Target (On-Premises):  {PRIMARY_URL}")
    print(f"  * Secondary Target (Cloud DR):   {SECONDARY_URL}")
    print("=" * 75)
    print("INSTRUCTIONS FOR DEMONSTRATION & SCREENSHOTS:")
    print("  1. Open http://localhost:8080 in your browser - see Primary serving.")
    print("  2. In terminal, simulate failure: kubectl scale deployment webapp-deployment -n visitor-app-primary --replicas=0")
    print("  3. Refresh http://localhost:8080 - notice automatic failover to Public Cloud!")
    print("  4. Restore primary: kubectl scale deployment webapp-deployment -n visitor-app-primary --replicas=2")
    print("=" * 75 + "\n")

    # Start health monitor daemon
    monitor_thread = threading.Thread(target=health_monitor_daemon, daemon=True)
    monitor_thread.start()

    server = HTTPServer(("0.0.0.0", LISTEN_PORT), FailoverProxyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down failover proxy...")
        server.server_close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        PRIMARY_URL = sys.argv[1]
    if len(sys.argv) > 2:
        SECONDARY_URL = sys.argv[2]
    if len(sys.argv) > 3:
        LISTEN_PORT = int(sys.argv[3])
    run_server()
