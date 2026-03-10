# SAP MCP Server and Client / SAP MCP服务器和客户端

English | [中文](#中文--english)

## English

This project provides an MCP (Model Context Protocol) server and client implementation for interacting with SAP systems via a RESTful API.

### Project Structure

- `config.json`: Configuration file for SAP API connection
- `sap_server.py`: MCP server implementation with SAP function calling tool
- `sap_client.py`: MCP client demonstrating usage of the server
- `requirements.txt`: Python dependencies
- `test_mcp_client_final.py`: HTTP-based MCP client test
- `simple_test.py`: Simple HTTP test for the MCP server

### Installation

1. Install the required dependencies (MCP SDK version 1.3.0 or higher):
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

Update the `config.json` file with your SAP API connection details:
```json
{
  "sap_api": {
    "base_url": "http://192.168.1.129:8000/zmy_service",
    "client": "100",
    "username": "your_username",
    "password": "your_password"
  }
}
```

If you don't need authentication, you can leave the `username` and `password` fields as they are or remove them entirely.

### Usage

#### Running the Client

To run the client example:
```bash
python sap_client.py
```

This will:
1. Start the MCP server
2. Connect to it via stdio
3. Execute example SAP function calls
4. Display the results

#### Running the Server in HTTP Mode

To run the server in HTTP mode:
```bash
python sap_server.py --transport http --host 127.0.0.1 --port 8000
```

#### Testing with HTTP Client

To test with the HTTP client:
```bash
python simple_test.py
```

### Using the MCP Tool Directly

The MCP server provides a `call_sap_function` tool with the following parameters:
- `function_name` (string, required): Name of the SAP function to call
- `parameters` (object, optional): Parameters for the SAP function

Example tool call:
```json
{
  "function_name": "BAPI_GL_GETGLACCPERIODBALANCES",
  "parameters": {
    "COMPANYCODE": "C999",
    "GLACCT": "0010010101",
    "FISCALYEAR": "2023",
    "CURRENCYTYPE": "10"
  }
}
```

### How It Works

1. The MCP server (`sap_server.py`) provides a tool called `call_sap_function`
2. When called, this tool makes an HTTP POST request to your SAP RESTful API
3. The API response is returned through the MCP protocol to the client
4. The client (`sap_client.py`) demonstrates how to use this tool with example calls

### Extending the Implementation

To add more SAP functions or modify the behavior:
1. Modify the `call_sap_tool` function in `sap_server.py`
2. Add additional examples in `sap_client.py`
3. Update the configuration in `config.json` as needed

### Error Handling

The implementation includes basic error handling for:
- Network errors
- JSON parsing errors
- Missing function names

Errors are returned in the response as JSON objects with an "error" key.

### Additional Notes

For SAP dynamic RFC code, please contact: zhangxj1@foxmail.com

---

## 中文

本项目提供了一个通过RESTful API与SAP系统交互的MCP（Model Context Protocol）服务器和客户端实现。

### 项目结构

- `config.json`：SAP API连接的配置文件
- `sap_server.py`：MCP服务器实现，包含SAP函数调用工具
- `sap_client.py`：演示服务器使用方法的MCP客户端
- `requirements.txt`：Python依赖项
- `test_mcp_client_final.py`：基于HTTP的MCP客户端测试
- `simple_test.py`：用于MCP服务器的简单HTTP测试

### 安装

1. 安装所需的依赖项（MCP SDK版本1.3.0或更高）：
   ```bash
   pip install -r requirements.txt
   ```

### 配置

更新`config.json`文件中的SAP API连接详情：
```json
{
  "sap_api": {
    "base_url": "http://192.168.1.129:8000/zmy_service",
    "client": "100",
    "username": "your_username",
    "password": "your_password"
  }
}
```

如果不需要身份验证，可以保留`username`和`password`字段不变或完全删除它们。

### 使用方法

#### 运行客户端

运行客户端示例：
```bash
python sap_client.py
```

这将：
1. 启动MCP服务器
2. 通过stdio连接到服务器
3. 执行示例SAP函数调用
4. 显示结果

#### 以HTTP模式运行服务器

以HTTP模式运行服务器：
```bash
python sap_server.py --transport http --host 127.0.0.1 --port 8000
```

#### 使用HTTP客户端测试

使用HTTP客户端进行测试：
```bash
python simple_test.py
```

### 直接使用MCP工具

MCP服务器提供了一个名为`call_sap_function`的工具，具有以下参数：
- `function_name`（字符串，必需）：要调用的SAP函数名称
- `parameters`（对象，可选）：SAP函数的参数

工具调用示例：
```json
{
  "function_name": "BAPI_GL_GETGLACCPERIODBALANCES",
  "parameters": {
    "COMPANYCODE": "C999",
    "GLACCT": "0010010101",
    "FISCALYEAR": "2023",
    "CURRENCYTYPE": "10"
  }
}
```

### 工作原理

1. MCP服务器（`sap_server.py`）提供了一个名为`call_sap_function`的工具
2. 调用时，该工具向您的SAP RESTful API发出HTTP POST请求
3. API响应通过MCP协议返回给客户端
4. 客户端（`sap_client.py`）演示如何使用此工具进行示例调用

### 扩展实现

要添加更多SAP函数或修改行为：
1. 修改`sap_server.py`中的`call_sap_tool`函数
2. 在`sap_client.py`中添加更多示例
3. 根据需要更新`config.json`中的配置

### 错误处理

实现包含基本的错误处理：
- 网络错误
- JSON解析错误
- 缺少函数名称

错误以包含"error"键的JSON对象形式在响应中返回。

### 附加说明

如需获取SAP动态RFC代码，请联系：zhangxj1@foxmail.com
