#!/usr/bin/env python3
"""
Test script for UCKN MCP Server
"""

import asyncio
import json
import subprocess
import sys


async def test_mcp_server():
    """Test the MCP server with basic protocol messages"""

    # Start the server process
    process = subprocess.Popen(
        [sys.executable, "-m", "uckn.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0,
    )

    try:
        # Wait a moment for server to start
        await asyncio.sleep(1)

        # Check if process is still running
        if process.poll() is not None:
            stderr_output = process.stderr.read()
            print(f"Server crashed immediately. Error: {stderr_output}")
            return False

        # Test 1: Initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }

        print("Sending initialize request...")
        try:
            process.stdin.write(json.dumps(init_request) + "\n")
            process.stdin.flush()

            # Read response with timeout
            response_line = process.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                print(f"Initialize response: {response}")
            else:
                print("No response to initialize request")
                # Check stderr for errors
                stderr_output = process.stderr.read()
                if stderr_output:
                    print(f"Server stderr: {stderr_output}")
                return False

        except BrokenPipeError:
            print("Server process terminated unexpectedly")
            stderr_output = process.stderr.read()
            if stderr_output:
                print(f"Server stderr: {stderr_output}")
            return False

        print("MCP Server basic test completed successfully!")
        return True

    except Exception as e:
        print(f"Test failed: {e}")
        return False
    finally:
        # Clean up process
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)
