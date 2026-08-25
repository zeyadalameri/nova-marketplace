import argparse
import statistics
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


def request_once(url: str):
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            response.read(1024)
            return response.status, time.perf_counter() - started
    except Exception:
        return 0, time.perf_counter() - started


def main():
    parser = argparse.ArgumentParser(description="Small NOVA HTTP load smoke test.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()
    urls = [f"{args.base_url.rstrip('/')}/products/?featured=true" for _ in range(args.requests)]
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        results = [future.result() for future in as_completed([executor.submit(request_once, url) for url in urls])]
    durations = sorted(duration for _, duration in results)
    failures = sum(status < 200 or status >= 400 for status, _ in results)
    p95 = durations[min(len(durations) - 1, int(len(durations) * 0.95))]
    print({"requests": len(results), "failures": failures, "mean_ms": round(statistics.mean(durations) * 1000, 2), "p95_ms": round(p95 * 1000, 2)})
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
