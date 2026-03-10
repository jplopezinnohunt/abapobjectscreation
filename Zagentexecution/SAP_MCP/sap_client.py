import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.types import TextContent

async def call_and_print(session: ClientSession, function: str, parameters: dict):
    print(f"\nCalling {function} with parameters: {parameters}")
    try:
        result = await session.call_tool(
            name="call_sap_function",
            arguments={
                "function": function,
                "parameters": parameters
            }
        )

        print(f"\nResult from {function}:")
        for content in result.content:
            if isinstance(content, TextContent):
                print(content.text)
            else:
                print(f"[{type(content).__name__}] {content}")
    except Exception as e:
        print(f"Error calling {function}: {e}")

async def main():
    # Create subprocess parameters to start sap_server.py
    server_params = StdioServerParameters(
        command="python",
        args=["sap_server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            try:
                await asyncio.wait_for(session.initialize(), timeout=10)
            except asyncio.TimeoutError:
                print("Error: Timeout initializing session with SAP server.")
                return

            # Example 1
            await call_and_print(session, "BAPI_GL_GETGLACCPERIODBALANCES", {
                "COMPANYCODE": "C999",
                "GLACCT": "0010010101",
                "FISCALYEAR": "2023",
                "CURRENCYTYPE": "10"
            })

            print("\n" + "="*50 + "\n")

            # Example 2
            await call_and_print(session, "BAPI_USER_GET_DETAIL", {
                "USERNAME": "SAPUSER"
            })

            print("\n" + "="*50 + "\n")

            # Example 3: Optimized example for dynamic SQL queries
            await call_and_print(session, "Z_DYNAMIC_SQL_QUERY", {
                "IV_SQL_TEXT": "SELECT * FROM BSEG"
            })

if __name__ == "__main__":
    asyncio.run(main())
