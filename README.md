# AI Platform Inference Service (Kubernetes + CI/CD + Observability)

Production-oriented service and deployment pattern used to support AI and data-intensive workloads on Kubernetes.

It includes:
- FastAPI inference-style API (model, real production patterns)
- Prometheus metrics (/metrics), health checks (/healthz, /readyz)
- Kubernetes manifests with resource requests/limits + probes
- Horizontal Pod Autoscaler (HPA)
- GitHub Actions CI (lint + unit smoke + Docker build)

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
