import json
import httpx
import asyncio
import sys
import argparse
from contextlib import asynccontextmanager
from fastmcp import FastMCP
from mcp.types import TextContent, CallToolResult
from typing import Any, Dict, Optional
import logging
import anyio

# ========== Initialize Logging ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("SAP_MCP")

# ========== SAP Service Class ==========
class SAPService:
    def __init__(self, config_file: str = "config.json"):
        self.config = self.load_config(config_file)
        self.base_url = self.config["sap_api"]["base_url"]
        self.client = self.config["sap_api"]["client"]
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.session = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_connections=100)
        )
        logger.info("HTTP session established")

    def load_config(self, file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load configuration file: {str(e)}")
            raise

    async def call_sap_function(self, function: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}?sap-client={self.client}"
        payload = {"FUNCTION": function, "PARAMETER": parameters}
        auth = None
        if username := self.config["sap_api"].get("username"):
            auth = (username, self.config["sap_api"].get("password", ""))

        try:
            response = await self.session.post(
                url,
                json=payload,
                auth=auth,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"SAP API error [{e.response.status_code}]: {e.response.text[:200]}")
            return {"error": f"SAP API error: {e.response.status_code}", "details": str(e)}
        except (httpx.RequestError, json.JSONDecodeError) as e:
            logger.error(f"Network/parsing error: {str(e)}")
            return {"error": f"Network request failed: {str(e)}"}

# ========== Global SAP Service Instance ==========
sap_service = SAPService()

# ========== Create FastMCP Instance ==========
mcp = FastMCP(
    name="SAP-MCP-Server",
    dependencies=["httpx"]
)

# ========== Tool Function: Call SAP Function ==========
@mcp.tool()
async def call_sap_function(
    function: str, 
    parameters: Optional[Any] = None,
    ctx: Optional[Any] = None
) -> CallToolResult:
    """
    Call SAP functions via RESTful API

    Parameters:
      function (str): SAP function name (e.g. BAPI_PO_CREATE)
      parameters (dict or str): Function parameters as dict or JSON string
    """
    if parameters is None:
        parameters = {}
    elif isinstance(parameters, str):
        try:
            parameters = json.loads(parameters)
            logger.info("String parameters successfully converted to dictionary")
        except json.JSONDecodeError:
            logger.warning("Parameter is a string, not JSON format, passed as raw string")
            parameters = {"_raw_string": parameters}
    
    logger.info(f"Calling SAP function: {function} with parameters: {parameters}")

    try:
        result = await sap_service.call_sap_function(function, parameters)
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        )
    except Exception as e:
        logger.exception(f"SAP function call exception: {function}")
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps({
                "error": f"Internal service error: {str(e)}",
                "function": function
            }))] 
        )

# ========== Main Run Function ==========
def main():
    parser = argparse.ArgumentParser(description="SAP MCP Server")
    parser.add_argument(
        "--transport", 
        choices=["stdio", "http"], 
        default="stdio",
        help="Transport method (default: stdio)"
    )
    parser.add_argument(
        "--host", 
        default="127.0.0.1",
        help="HTTP service listening address (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=3000,
        help="HTTP service listening port (default: 3000)"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting SAP MCP service (transport method: {args.transport})...")
    if args.transport == "http":
        mcp.run(transport="streamable-http", path="/mcp", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")
    logger.info("Service stopped")

# ========== Entry Point ==========
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.exception("Unhandled global exception")
        exit(1)
