import time
import redis

HOST = "127.0.0.1"
PORT = 6380
N = 5000

r = redis.Redis(host=HOST, port=PORT, decode_responses=True)

def pct(a, p):
    a = sorted(a)
    return a[int(p * (len(a) - 1))]

# Warmup
for _ in range(200):
    r.ping()

# SET benchmark
set_lat = []
t0 = time.perf_counter()
for i in range(N):
    k = f"k{i}"
    v = "x" * 50
    s = time.perf_counter()
    r.set(k, v)
    set_lat.append((time.perf_counter() - s) * 1000)
t1 = time.perf_counter()

# GET benchmark
get_lat = []
t2 = time.perf_counter()
for i in range(N):
    k = f"k{i}"
    s = time.perf_counter()
    r.get(k)
    get_lat.append((time.perf_counter() - s) * 1000)
t3 = time.perf_counter()

print(f"SET: N={N} total={t1-t0:.3f}s ops/sec={N/(t1-t0):.1f}  p50={pct(set_lat,0.50):.3f}ms p95={pct(set_lat,0.95):.3f}ms p99={pct(set_lat,0.99):.3f}ms")
print(f"GET: N={N} total={t3-t2:.3f}s ops/sec={N/(t3-t2):.1f}  p50={pct(get_lat,0.50):.3f}ms p95={pct(get_lat,0.95):.3f}ms p99={pct(get_lat,0.99):.3f}ms")

