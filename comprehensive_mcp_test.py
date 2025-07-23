#!/usr/bin/env python3
"""
Comprehensive test suite for UCKN MCP Server
"""
import asyncio
import json
import subprocess
import sys
import time
from typing import Any, Dict

async def run_mcp_test_sequence():
    """Run a comprehensive MCP server test sequence"""
    
    # Start the server process
    process = subprocess.Popen(
        [sys.executable, "-m", "uckn.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )
    
    try:
        # Wait for server to start
        await asyncio.sleep(1)
        
        test_results = {
            "initialization": False,
            "list_resources": False,
            "list_tools": False,
            "read_resource": False,
            "call_tool": False,
            "error_handling": False
        }
        
        # Test 1: Initialize
        print("🚀 Testing MCP Server Initialization...")
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
            response = json.loads(response_line.strip())
            if response.get("result") and "capabilities" in response["result"]:
                test_results["initialization"] = True
                print("✅ Initialization successful")
            else:
                print("❌ Initialization failed")
        
        # Test 2: List Resources
        print("\n📚 Testing List Resources...")
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
            if response.get("result") and "resources" in response["result"]:
                resources = response["result"]["resources"]
                print(f"✅ Found {len(resources)} resources:")
                for resource in resources:
                    print(f"  - {resource['name']}: {resource['description']}")
                test_results["list_resources"] = True
            else:
                print("❌ List resources failed")
        
        # Test 3: List Tools
        print("\n🔧 Testing List Tools...")
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/list"
        }
        
        process.stdin.write(json.dumps(list_tools_request) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            if response.get("result") and "tools" in response["result"]:
                tools = response["result"]["tools"]
                print(f"✅ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"  - {tool['name']}: {tool['description']}")
                test_results["list_tools"] = True
            else:
                print("❌ List tools failed")
        
        # Test 4: Read Resource
        print("\n📖 Testing Read Resource...")
        read_resource_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/read",
            "params": {
                "uri": "uckn://knowledge/patterns"
            }
        }
        
        process.stdin.write(json.dumps(read_resource_request) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            if response.get("result") and "contents" in response["result"]:
                print("✅ Resource read successful")
                content = response["result"]["contents"][0]
                print(f"  Content type: {content['type']}")
                print(f"  Content preview: {content['text'][:100]}...")
                test_results["read_resource"] = True
            else:
                print("❌ Read resource failed")
        
        # Test 5: Call Tool
        print("\n⚙️ Testing Tool Call...")
        call_tool_request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "search_patterns",
                "arguments": {
                    "query": "testing patterns",
                    "limit": 5
                }
            }
        }
        
        process.stdin.write(json.dumps(call_tool_request) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            if response.get("result") and "content" in response["result"]:
                print("✅ Tool call successful")
                content = response["result"]["content"][0]
                print(f"  Response type: {content['type']}")
                print(f"  Response preview: {content['text'][:100]}...")
                test_results["call_tool"] = True
            else:
                print("❌ Tool call failed")
        
        # Test 6: Error Handling
        print("\n🚨 Testing Error Handling...")
        invalid_request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "invalid/method"
        }
        
        process.stdin.write(json.dumps(invalid_request) + "\n")
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            if "error" in response:
                print("✅ Error handling working (invalid method caught)")
                test_results["error_handling"] = True
            else:
                print("❌ Error handling failed")
        
        # Summary
        print("\n" + "="*50)
        print("📊 COMPREHENSIVE TEST RESULTS:")
        print("="*50)
        
        passed = sum(test_results.values())
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! MCP Server is fully functional!")
            return True
        else:
            print("⚠️  Some tests failed. Server has issues.")
            return False
        
    except Exception as e:
        print(f"Test suite failed with exception: {e}")
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
    success = asyncio.run(run_mcp_test_sequence())
    sys.exit(0 if success else 1)