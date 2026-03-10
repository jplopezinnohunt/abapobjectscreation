import requests
import json

# Create session
session = requests.Session()

# Set default headers
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
}

# Initialize request
init_data = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-08-08",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
}

# Send initialization request
init_response = session.post(
    "http://localhost:8000/mcp",
    json=init_data,
    headers=headers
)

print("=== Initialization response ===")
print(f"状态码: {init_response.status_code}")
print(f"响应内容: {init_response.text}")

# 获取会话ID
session_id = init_response.headers.get("mcp-session-id")
print(f"会话ID: {session_id}")

if session_id:
    # 更新头部包含会话ID
    headers["mcp-session-id"] = session_id
    
    # 等待一段时间确保初始化完成
    import time
    time.sleep(1)
    
    # 工具列表请求
    tools_data = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    tools_response = session.post(
        "http://localhost:8000/mcp",
        json=tools_data,
        headers=headers
    )
    
    print("\n=== 工具列表响应 ===")
    print(f"状态码: {tools_response.status_code}")
    print(f"响应内容: {tools_response.text}")
    
    # 调用SAP函数请求
    call_data = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "call_sap_function",
            "arguments": {
                "function": "Z_DYNAMIC_SQL_QUERY",
                "parameters": {
                    "IV_SQL_TEXT": "SELECT * FROM BSEG"
                }
            }
        }
    }
    
    call_response = session.post(
        "http://localhost:8000/mcp",
        json=call_data,
        headers=headers
    )
    
    print("\n=== 调用SAP函数响应 ===")
    print(f"状态码: {call_response.status_code}")
    print(f"响应内容: {call_response.text}")
else:
    print("未能获取会话ID，无法继续测试")
