import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import InitializeRequest, InitializeRequestParams, ListToolsRequest
import json

async def test_mcp_client():
    # Create HTTP client
    async with streamablehttp_client("http://localhost:8000/mcp") as (read, write):
        # Initialize request
        init_request = InitializeRequest(
            id=1,
            params=InitializeRequestParams(
                protocolVersion="2024-08-08",
                capabilities={},
                clientInfo={"name": "test-client", "version": "1.0.0"}
            )
        )
        
        # Send initialization request
        await write(init_request)
        
        # Read initialization response
        init_response = await read()
        print("Initialization response:")
        print(json.dumps(init_response, indent=2, default=str))
        
        # Tools list request
        tools_request = ListToolsRequest(id=2, params={})
        
        # Send tools list request
        await write(tools_request)
        
        # Read tools list response
        tools_response = await read()
        print("\nTools list response:")
        print(json.dumps(tools_response, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(test_mcp_client())
