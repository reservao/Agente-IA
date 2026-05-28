#!/usr/bin/env python3
"""Simple MCP server exposing qwen2.5-coder:7b via Ollama for basic coding tasks."""
import sys, json, subprocess

def ollama_ask(prompt: str, model: str = "qwen2.5-coder:7b") -> str:
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt, capture_output=True, text=True, timeout=120
    )
    return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr.strip()}"

def handle(req: dict) -> dict:
    method = req.get("method", "")
    req_id = req.get("id")

    if method == "initialize":
        return {"jsonrpc":"2.0","id":req_id,"result":{
            "protocolVersion":"2024-11-05",
            "capabilities":{"tools":{}},
            "serverInfo":{"name":"ollama-coder","version":"1.0"}
        }}

    if method == "tools/list":
        return {"jsonrpc":"2.0","id":req_id,"result":{"tools":[{
            "name": "ollama_code",
            "description": "Ask qwen2.5-coder:7b to write or explain simple code. Use for boilerplate, utility functions, basic JS snippets, CSS, and straightforward tasks. Claude handles architecture, complex logic, and review.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prompt": {"type":"string","description":"The coding task or question"}
                },
                "required": ["prompt"]
            }
        }]}}

    if method == "tools/call":
        prompt = req.get("params", {}).get("arguments", {}).get("prompt", "")
        output = ollama_ask(prompt)
        return {"jsonrpc":"2.0","id":req_id,"result":{"content":[{"type":"text","text":output}]}}

    return {"jsonrpc":"2.0","id":req_id,"result":{}}

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        req = json.loads(line)
        resp = handle(req)
        print(json.dumps(resp), flush=True)
    except Exception as e:
        print(json.dumps({"jsonrpc":"2.0","id":None,"error":{"code":-32700,"message":str(e)}}), flush=True)
