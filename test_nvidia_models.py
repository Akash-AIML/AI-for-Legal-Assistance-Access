import sys
import urllib.request
import urllib.error
import json
import time
import os

key = None

if len(sys.argv) > 1 and sys.argv[1].strip():
    key = sys.argv[1].strip()

if not key:
    key = os.environ.get("NVIDIA_API_KEY")

if not key:
    for env_path in ["compliance-ai/.env", ".env"]:
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("NVIDIA_API_KEY="):
                        k = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if k and not k.startswith("your_"):
                            key = k
                    elif line.startswith("OPENAI_API_KEY=") and "nvapi-" in line:
                        k = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if k:
                            key = k

if not key:
    print("\n[!] NVIDIA_API_KEY is not set.")
    try:
        key = input("Please paste your NVIDIA API Key (nvapi-...) here: ").strip()
    except (EOFError, KeyboardInterrupt):
        pass

if not key:
    print("Error: No API key provided. Exiting.")
    sys.exit(1)

chat_models = [
    "meta/llama-3.2-11b-vision-instruct",
    "meta/llama-3.2-90b-vision-instruct",
    "mistralai/mistral-large-2-instruct",
    "google/gemma-3-12b-it",
    "google/gemma-3-4b-it",
    "deepseek-ai/deepseek-v4-flash-0731",
    "ibm/granite-3.0-8b-instruct",
    "meta/codellama-70b",
    "mistralai/mistral-7b-instruct-v0.3",
    "01-ai/yi-large",
    "databricks/dbrx-instruct",
    "aisingapore/sea-lion-7b-instruct",
]

embed_models = [
    "nvidia/embed-qa-4",
    "snowflake/arctic-embed-l",
    "nvidia/nv-embedqa-mistral-7b-v2",
    "nvidia/llama-3.2-nv-embedqa-1b-v1"
]

print(f"\nTesting NVIDIA API Models (10s timeout limit) | Key: ...{key[-6:]}")
print("="*78)
print(f"{'MODEL ID':<42} | {'TYPE':<10} | {'STATUS':<10} | {'LATENCY (ms)'}")
print("="*78)

headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

working_chat = []
working_embed = []

for m in chat_models:
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    data = json.dumps({
        "model": m,
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 10
    }).encode()

    req = urllib.request.Request(url, data=data, headers=headers)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            elapsed = (time.time() - t0) * 1000
            res = json.loads(resp.read().decode())
            print(f"{m:<42} | {'Chat':<10} | \033[32m200 OK\033[0m     | {elapsed:.1f} ms")
            working_chat.append((m, elapsed))
    except urllib.error.HTTPError as e:
        print(f"{m:<42} | {'Chat':<10} | \033[31mHTTP {e.code}\033[0m   | -")
    except (urllib.error.URLError, TimeoutError, Exception) as e:
        if "timed out" in str(e).lower() or isinstance(e, TimeoutError):
            print(f"{m:<42} | {'Chat':<10} | \033[33mTIMEOUT >10s\033[0m | -")
        else:
            print(f"{m:<42} | {'Chat':<10} | \033[31mError\033[0m       | -")

for m in embed_models:
    url = "https://integrate.api.nvidia.com/v1/embeddings"
    data = json.dumps({
        "model": m,
        "input": ["Sample legal text for embedding."],
        "input_type": "query"
    }).encode()

    req = urllib.request.Request(url, data=data, headers=headers)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            elapsed = (time.time() - t0) * 1000
            res = json.loads(resp.read().decode())
            print(f"{m:<42} | {'Embedding':<10} | \033[32m200 OK\033[0m     | {elapsed:.1f} ms")
            working_embed.append((m, elapsed))
    except urllib.error.HTTPError as e:
        print(f"{m:<42} | {'Embedding':<10} | \033[31mHTTP {e.code}\033[0m   | -")
    except (urllib.error.URLError, TimeoutError, Exception) as e:
        if "timed out" in str(e).lower() or isinstance(e, TimeoutError):
            print(f"{m:<42} | {'Embedding':<10} | \033[33mTIMEOUT >10s\033[0m | -")
        else:
            print(f"{m:<42} | {'Embedding':<10} | \033[31mError\033[0m       | -")

print("="*78)
if working_chat:
    print("\n✅ Working & Fast Chat Models:")
    for m, l in working_chat:
        print(f"   • {m} ({l:.1f} ms)")
if working_embed:
    print("\n✅ Working Embedding Models:")
    for m, l in working_embed:
        print(f"   • {m} ({l:.1f} ms)")
print("="*78)
