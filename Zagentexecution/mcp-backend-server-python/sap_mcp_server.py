import os
from dotenv import load_dotenv
from typing import Any
from pyrfc import Connection, RFCError
from mcp.server.fastmcp import FastMCP

# Load SAP credentials from .env
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("SAP_Backend_MCP")

def get_sap_connection(system_id="D01") -> Connection:
    """Establish and return a connection to the SAP backend.
    Supports system_id (e.g., 'D01', 'P01') to choose configuration.
    """
    # Load .env from the server directory
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path)

    try:
        # Prefix for system-specific environment variables
        prefix = f"SAP_{system_id}_"
        
        # Fallback to generic SAP_* if specific prefix not found
        def get_env(key, default=None):
            return os.getenv(prefix + key) or os.getenv("SAP_" + key) or default

        conn_params = {
            "ashost": get_env("ASHOST"),
            "sysnr": get_env("SYSNR"),
            "client": get_env("CLIENT"),
            "user": get_env("USER"),
            "lang": get_env("LANG", "EN")
        }
        
        passwd = get_env("PASSWD") or get_env("PASSWORD")
        if passwd:
            conn_params["passwd"] = passwd

        if get_env("SNC_MODE") == "1":
            conn_params["snc_mode"] = "1"
            conn_params["snc_partnername"] = get_env("SNC_PARTNERNAME")
            conn_params["snc_qop"] = get_env("SNC_QOP", "9")
            
        conn = Connection(**conn_params)
        return conn
    except Exception as e:
        raise RuntimeError(f"Failed to connect to SAP system {system_id}: {str(e)}")

@mcp.tool()
def read_sap_table(table_name: str, max_rows: int = 10, delimiter: str = "|", options: str = "", system_id: str = "D01") -> str:
    """Read data from an SAP transparent table using the native RFC_READ_TABLE BAPI.
    
    Args:
        table_name: The name of the SAP table to read (e.g., 'T001', 'FMFINCODE').
        max_rows: Maximum number of rows to return.
        delimiter: Delimiter for the resulting table data columns.
        options: WHERE clause for filtering (e.g., "ERFDAT >= '20240101'").
        system_id: Target system ID ('D01' or 'P01').
    """
    conn = get_sap_connection(system_id)
    try:
        # Call the standard SAP BAPI to read table data
        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE=table_name,
            DELIMITER=delimiter,
            ROWCOUNT=max_rows,
            OPTIONS=[{"TEXT": options}]
        )
        
        # Format the response clearly
        fields = [field["FIELDNAME"] for field in result.get("FIELDS", [])]
        data = result.get("DATA", [])
        
        output = [f"Data for SAP Table {table_name} (System: {system_id})"]
        output.append(f"Columns: {delimiter.join(fields)}")
        output.append("-" * 40)
        
        if not data:
            output.append("No records found.")
        else:
            for row in data:
                output.append(row["WA"])
                
        return "\n".join(output)
        
    except RFCError as e:
        return f"SAP RFC Error: {str(e)}"
    except Exception as e:
        return f"Unexpected Error: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
def search_abap_objects(object_name: str, object_type: str = "PROG", max_results: int = 50, system_id: str = "D01") -> str:
    """Search for ABAP objects (Programs, Classes, Tables) based on a name pattern.
    
    Args:
        object_name: The pattern to search for (e.g., 'ZCRP*', 'MARA').
        object_type: Type of object (PROG = Program, CLAS = Class, TABL = Table).
        system_id: Target system ID ('D01' or 'P01').
    """
    conn = get_sap_connection(system_id)
    try:
        # Using TADIR to find objects
        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="TADIR",
            DELIMITER="|",
            ROWCOUNT=max_results,
            OPTIONS=[{"TEXT": f"OBJ_NAME LIKE '{object_name}' AND OBJECT = '{object_type}'"}]
        )
        
        data = result.get("DATA", [])
        if not data:
            return f"No results found in system {system_id} for {object_type} matching '{object_name}'."
            
        output = [f"Search Results ({system_id}) for {object_type} matching '{object_name}':"]
        for row in data:
            output.append(f"- {row['WA'].split('|')[0].strip()}")
            
        return "\n".join(output)
    except Exception as e:
        return f"Error searching objects: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
def get_abap_source(object_name: str, object_type: str = "PROG", system_id: str = "D01") -> str:
    """Read the source code of an ABAP program or class method.
    
    Args:
        object_name: Name of the program or class.
        object_type: 'PROG' for programs/reports, 'CLAS' for classes.
        system_id: Target system ID ('D01' or 'P01').
    """
    conn = get_sap_connection(system_id)
    try:
        if object_type == "PROG":
            # Using SIW_RFC_READ_REPORT as verified replacement for RFC_READ_REPORT
            result = conn.call("SIW_RFC_READ_REPORT", I_NAME=object_name)
            lines = result.get("E_TAB_CODE", [])
            if not lines:
                return f"Source for {object_name} ({system_id}) is empty or not found."
            
            return "\n".join([line.get("LINE", "") for line in lines])
            
        elif object_type == "CLAS":
            return f"Retrieval for {object_type} (Classes) requires method-specific selection via SEO* tables or similar BAPIs."
            
        return f"Retrieval for {object_type} not yet implemented."
    except Exception as e:
        return f"Error reading source: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
def get_class_methods(class_name: str, system_id: str = "D01") -> str:
    """List all methods of an ABAP class.
    
    Args:
        class_name: Name of the ABAP class (e.g., 'CL_SALV_TABLE').
        system_id: Target system ID ('D01' or 'P01').
    """
    conn = get_sap_connection(system_id)
    try:
        # SEOCOMPO contains components of classes/interfaces
        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="SEOCOMPO",
            DELIMITER="|",
            OPTIONS=[{"TEXT": f"CLSNAME = '{class_name}' AND CMPTYPE = '1'"}] # CMPTYPE 1 = Method
        )
        
        data = result.get("DATA", [])
        if not data:
            return f"No methods found for class '{class_name}' in system {system_id}."
            
        output = [f"Methods for class {class_name} ({system_id}):"]
        for row in data:
            # Field 2 usually contains the CMPNAME (Component Name)
            fields = row['WA'].split('|')
            if len(fields) > 1:
                output.append(f"- {fields[1].strip()}")
                
        return "\n".join(output)
    except Exception as e:
        return f"Error reading class methods: {str(e)}"
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting SAP Backend MCP Server...")
    # By default, start with standard input/output transport for MCP
    mcp.run(transport="stdio")
