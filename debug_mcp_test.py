#!/usr/bin/env python3
"""
Debug MCP Server responses
"""
import asyncio
import json
import subprocess
import sys

async def debug_mcp_server():
    """Debug what the server is actually returning"""
    
    process = subprocess.Popen(
        [sys.executable, "-m", "uckn.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )
    
    try:
        await asyncio.sleep(1)
        
        # First initialize the server
        print("🔍 Initializing server first...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            init_response = json.loads(response_line.strip())
            print("Init response received")
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }
        
        process.stdin.write(json.dumps(initialized_notification) + "\n")
        process.stdin.flush()
        
        # Test list resources debug
        print("🔍 DEBUGGING List Resources...")
        list_resources_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "resources/list"
        }
        
        process.stdin.write(json.dumps(list_resources_request) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            print("Raw response:")
            print(json.dumps(response, indent=2))
        else:
            print("No response received")
        
    except Exception as e:
        print(f"Debug failed: {e}")
    finally:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

if __name__ == "__main__":
    asyncio.run(debug_mcp_server())