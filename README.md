 **Mini Redis (Python)**

A lightweight Redis-compatible server implemented in Python that supports the Redis Serialization Protocol (RESP), multiple concurrent clients, key expiration (TTL), and durable persistence using an append-only file (AOF) with replay on restart.

This project was built to understand low-level systems concepts such as protocol parsing, socket-based servers, data durability, and performance benchmarking.

 **Features**

\- RESP protocol support  
  \- Parses Redis Serialization Protocol (RESP) requests  
  \- Compatible with standard clients such as \`redis-cli\`

\- Multi-client TCP server  
  \- Thread-per-connection model  
  \- Supports multiple concurrent clients

\- Supported commands  
  \- \`PING\`, \`ECHO\`  
  \- \`SET\`, \`GET\`, \`DEL\`  
  \- \`MSET\`, \`MGET\`  
  \- TTL commands: \`SET key value EX seconds\`, \`EXPIRE\`, \`TTL\`  
  \- \`FLUSHDB\`

\- Key expiration (TTL)  
  \- Lazy expiration on access  
  \- TTL metadata stored per key

\- Durability via Append-Only File (AOF)  
  \- All mutating commands are logged  
  \- State is reconstructed by replaying the AOF on startup  
  \- Data survives server restarts

\- Performance benchmarking  
  \- Measured throughput and latency using a Python Redis client

 **Project Structure**

mini-redis/  
src/  
mini\_redis/  
protocol.py \# RESP parsing and encoding  
datastore.py \# In-memory key-value store with TTL  
aof.py \# Append-only file persistence and replay  
server.py \# Command handling and TCP server  
run.py \# Application entrypoint  
benchmarks/  
bench\_set\_get.py \# Throughput and latency benchmarks  
[README.md](http://README.md)

 **Requirements**

\- Python 3.9+  
\- \`redis-cli\` (for testing)  
\- Python Redis client (for benchmarks)

Install the Python dependency:  
\`\`\`bash  
python3 \-m pip install redis

## **Running the Server**

The server runs on port **6380** by default.

python3 src/run.py

You should see:

MiniRedis listening on 127.0.0.1:6380 (AOF=appendonly.aof)

## **Basic Usage (via redis-cli)**

redis-cli \-p 6380 PING  
redis-cli \-p 6380 SET hello world  
redis-cli \-p 6380 GET hello

### **TTL Example**

redis-cli \-p 6380 SET a 1 EX 2  
redis-cli \-p 6380 TTL a

After expiration:

redis-cli \-p 6380 GET a  
\# (nil)

## **Persistence Demo (AOF Replay)**

The server uses an **append-only file (AOF)** to log all mutating commands and replay them on startup, allowing data to survive restarts.

### **Steps**

1. Start the server:

python3 src/run.py

2. Write a key:

redis-cli \-p 6380 FLUSHDB

redis-cli \-p 6380 SET persist\_me 42

redis-cli \-p 6380 GET persist\_me

Expected output:

"42"

3. Stop the server:

Ctrl \+ C

4. Restart the server:

python3 src/run.py

5. Verify the key is still present:

redis-cli \-p 6380 GET persist\_me

Expected output:

"42"

### **Explanation**

* All write operations (SET, DEL, MSET, EXPIRE, FLUSHDB) are appended to an AOF file.  
* On startup, the server replays the log to reconstruct in-memory state.  
* This ensures durability across restarts without requiring snapshots.

## **Benchmarks**

Benchmarks were run using the Python Redis client.

Run:

python3 benchmarks/bench\_set\_get.py

### **Results (local machine)**

SET: N=5000 total=0.218s ops/sec=22959.1  p50=0.040ms p95=0.059ms p99=0.076ms  
GET: N=5000 total=0.172s ops/sec=29039.7  p50=0.033ms p95=0.040ms p99=0.058ms

## **Design Notes**

* The system is intentionally implemented using simple data structures to emphasize clarity and correctness.  
* TTL expiration is primarily lazy (checked on access).  
* AOF replay restores state; TTL values specified with EX are reapplied relative to restart time.

## **Possible Extensions**

* Background thread for proactive TTL cleanup  
* Snapshotting (RDB-style persistence)  
* Configurable port and AOF path via CLI arguments  
* INFO command for server statistics  
* Asynchronous I/O model for improved scalability

**Learning Outcomes**

This project provided hands-on experience with:

* Network programming and TCP servers  
* Binary protocol parsing and serialization  
* In-memory data stores and expiration semantics  
* Write-ahead logging and crash recovery  
* Performance benchmarking and latency analysis

