# Cloud Visitor Counter Application (Flask + Redis + Kubernetes)

A high-availability, autoscaling, containerized web application deployed on Kubernetes with automated hybrid cloud failover and measured FinOps cost optimizations.

---

## Quick Navigation
- **Architecture Diagram**: [ARCHITECTURE.md](file:///C:/Users/ssoni/.gemini/antigravity/scratch/visitor-counter-app/ARCHITECTURE.md)
- **Full Academic Project Report**: [REPORT.md](file:///C:/Users/ssoni/.gemini/antigravity/scratch/visitor-counter-app/REPORT.md)
- **Cost Optimization Analysis**: [cost_optimization/COST_ANALYSIS.md](file:///C:/Users/ssoni/.gemini/antigravity/scratch/visitor-counter-app/cost_optimization/COST_ANALYSIS.md)
- **Screenshots Guide**: [SCREENSHOTS_GUIDE.md](file:///C:/Users/ssoni/.gemini/antigravity/scratch/visitor-counter-app/SCREENSHOTS_GUIDE.md)
- **GitHub Repository Link**: [github_link.txt](file:///C:/Users/ssoni/.gemini/antigravity/scratch/visitor-counter-app/github_link.txt)

---

## Prerequisites
- **Docker Desktop** (with Kubernetes enabled) or **Minikube**
- **kubectl**
- **Python 3.9+** (for load testing and failover router)

---

## Step-by-Step Execution Guide

### Task 1: Containerization (Docker Compose)
1. Build and start containers:
   ```bash
   docker compose up -d --build
   ```
2. Check running status:
   ```bash
   docker ps
   ```
3. Open your browser at `http://localhost:5000` to view the Visitor Counter.
4. Stop containers when done:
   ```bash
   docker compose down
   ```

---

### Task 2: Kubernetes Deployment & Self-Healing
1. Apply the complete Kubernetes manifest:
   ```bash
   kubectl apply -f k8s.yaml
   ```
2. Verify all resources in the namespace:
   ```bash
   kubectl get all,pvc -n visitor-app
   ```
3. Access the application in your browser:
   - If using Minikube: `minikube service webapp-service -n visitor-app`
   - If using Docker Desktop Kubernetes / NodePort: `http://localhost:30080`
4. Test **Self-Healing**:
   ```bash
   # Delete one web pod
   kubectl get pods -n visitor-app
   kubectl delete pod <pod-name> -n visitor-app
   # Watch Kubernetes immediately recreate a healthy replacement
   kubectl get pods -n visitor-app -w
   ```

---

### Task 3: Horizontal Pod Autoscaling (HPA)
1. Ensure the Kubernetes Metrics Server is active:
   ```bash
   # For Minikube:
   minikube addons enable metrics-server
   ```
2. Apply the HPA manifest:
   ```bash
   kubectl apply -f hpa.yaml
   ```
3. Monitor HPA in Terminal 1:
   ```bash
   kubectl get hpa -n visitor-app -w
   ```
4. Run the automated load generator in Terminal 2:
   ```bash
   python load_test.py --url http://localhost:30080 --concurrency 8 --duration 60
   ```
5. Watch replicas scale from 2 up to 5+ in Terminal 1!

---

### Task 4: Hybrid Cloud Simulation & Automated Failover
1. Deploy Primary (On-Premises) and Secondary (Simulated Public Cloud) clusters:
   ```bash
   kubectl apply -f hybrid_cloud/primary_cluster.yaml
   kubectl apply -f hybrid_cloud/secondary_cluster.yaml
   ```
2. Start the automated Failover Controller in Terminal 1:
   ```bash
   python hybrid_cloud/failover_controller.py
   ```
3. Open `http://localhost:8080` in your browser:
   - Notice the telemetry shows: **On-Premises Private Data Center (Cluster 1)**.
4. In Terminal 2, simulate a complete Primary cluster outage:
   ```bash
   kubectl scale deployment webapp-deployment -n visitor-app-primary --replicas=0
   ```
5. Refresh `http://localhost:8080` in your browser:
   - The failover router automatically transfers traffic!
   - Telemetry now shows: **Simulated Public Cloud (AWS/GCP - Cluster 2)** with zero downtime!
6. Restore the primary cluster:
   ```bash
   kubectl scale deployment webapp-deployment -n visitor-app-primary --replicas=2
   ```

---

### Task 5: Cost Optimization Verification
Read the in-depth comparative analysis in [cost_optimization/COST_ANALYSIS.md](file:///C:/Users/ssoni/.gemini/antigravity/scratch/visitor-counter-app/cost_optimization/COST_ANALYSIS.md) detailing:
1. **Container Image Reduction**: 1,024 MB down to 145 MB (85.8% reduction).
2. **Compute Right-Sizing**: 90% reduction in CPU request reservations, cutting required cluster nodes from 4 to 1 (87.5% VM cost reduction).
3. **Dynamic HPA Elasticity**: Consuming only 2,160 pod-hours/month vs. 7,200 static pod-hours/month (70% savings).
4. **Hybrid Cloud Cold Standby**: Active-passive DR reducing cloud standby spend by 93.4%.

---

## Submission Checklist for Students
1. Push code to your **PUBLIC** GitHub repository (instructions in `github_link.txt`).
2. Download repository as a ZIP file (`Code` -> `Download ZIP`).
3. Prepare all screenshots in the `screenshots/` folder following `SCREENSHOTS_GUIDE.md`.
4. Ensure your **Previous Team Research Paper** PDF is ready.
5. Upload both the project ZIP/folder and the Team Research Paper to the specified [Google Drive Folder](https://drive.google.com/drive/folders/1KufvIIZrEiJqsXuI5Fz78rXC87UwD8W_?usp=sharing).
