from collections import defaultdict

metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "total_latency": 0
}


def record_request(status_code: int, latency_ms: float):
    metrics["total_requests"] += 1
    metrics["total_latency"] += latency_ms

    if status_code < 400:
        metrics["successful_requests"] += 1
    else:
        metrics["failed_requests"] += 1


def get_metrics():
    avg_latency = 0

    if metrics["total_requests"] > 0:
        avg_latency = (
            metrics["total_latency"]
            / metrics["total_requests"]
        )

    return {
        **metrics,
        "average_latency_ms": round(avg_latency, 2)
    }