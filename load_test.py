#!/usr/bin/env python3
"""
Automated Load Generation Script for HPA Autoscaling Verification.
Sends concurrent HTTP requests to trigger CPU utilization spikes on the webapp.
"""

import sys
import time
import argparse
import threading
from urllib.request import urlopen, Request
from urllib.error import URLError

def send_request(url, request_id, results):
    try:
        t0 = time.time()
        req = Request(url, headers={"User-Agent": "HPA-Load-Tester/1.0"})
        with urlopen(req, timeout=5) as response:
            status = response.getcode()
            elapsed = time.time() - t0
            results["success"] += 1
            results["times"].append(elapsed)
    except URLError as e:
        results["failed"] += 1
    except Exception:
        results["failed"] += 1

def run_load_test(target_url, concurrency=10, duration_seconds=60, cpu_cycles=3500000):
    print("=" * 70)
    print("  HPA AUTOSCALING LOAD GENERATOR")
    print("=" * 70)
    print(f"Target URL:         {target_url}")
    print(f"Concurrency:        {concurrency} worker threads")
    print(f"Duration:           {duration_seconds} seconds")
    print(f"CPU Load Parameter: {cpu_cycles} cycles/request")
    print("-" * 70)
    print("Sending traffic to trigger Horizontal Pod Autoscaler (HPA)...")
    print("Monitor HPA in another terminal via: kubectl get hpa -n visitor-app -w")
    print("-" * 70)

    url_with_load = f"{target_url.rstrip('/')}/load?cycles={cpu_cycles}"
    
    start_time = time.time()
    results = {"success": 0, "failed": 0, "times": []}

    while time.time() - start_time < duration_seconds:
        threads = []
        for i in range(concurrency):
            t = threading.Thread(target=send_request, args=(url_with_load, i, results))
            t.daemon = True
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        elapsed_so_far = int(time.time() - start_time)
        print(f"[{elapsed_so_far}s / {duration_seconds}s] Requests Sent: {results['success']} OK, {results['failed']} Failed", end="\r")
        time.sleep(0.1)

    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print("LOAD TEST FINISHED")
    print(f"Total Elapsed Time: {round(total_time, 2)} s")
    print(f"Successful Requests: {results['success']}")
    print(f"Failed Requests:     {results['failed']}")
    if results["times"]:
        avg_time = sum(results["times"]) / len(results["times"])
        print(f"Average Response Time: {round(avg_time, 4)} s")
    print("=" * 70)
    print("Check autoscaling status:")
    print("  kubectl get hpa -n visitor-app")
    print("  kubectl get pods -n visitor-app -l app=webapp")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HPA Load Generator")
    parser.add_argument("--url", default="http://localhost:30080", help="Webapp base URL")
    parser.add_argument("--concurrency", type=int, default=8, help="Number of concurrent threads")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds")
    parser.add_argument("--cycles", type=int, default=3000000, help="CPU cycles per request")
    args = parser.parse_args()

    run_load_test(args.url, args.concurrency, args.duration, args.cycles)
