#!/usr/bin/env python
# coding: utf-8

# In this demo we will use our dummy MCP Model with FastAPI and Uvicorn as API layer.

# Installation [fastapi, uvicorn]
# we will use '!uv pip' command or '%pip install' method

# In[1]:
#get_ipython().system('uv pip install fastapi uvicorn psutil')
# 1- Importing Required Packages

# In[2]:


import json
import sys 
import requests
# Required for Uvicorn
import uvicorn
import socket
import time
import psutil
from multiprocessing import Process
# End of Uvicorn process specific library intake
from typing import Any, Dict, Annotated
from fastapi import FastAPI, Body
from pydantic import BaseModel, Field, BeforeValidator


# In[3]:


# Define a Universal Normalization Function
def normalize_text_input(value: Any) -> str:
    """
    Cleans up any messy string input automatically.
    - Converts to string type safely.
    - Strips leading/trailing spaces.
    - Squashes multiple spaces down to a single space (e.g., 'Souvik    Dhar' -> 'souvik dhar').
    - Converts everything to lowercase for uniform database comparison.
    """
    if not isinstance(value, str):
        value = str(value)

    # Remove leading/trailing spaces, lowercase it, and split/join to remove extra middle spaces
    cleaned = " ".join(value.strip().lower().split())
    return cleaned


# In[4]:


# Create a reusable normalized data type
NormalizedString = Annotated[str, BeforeValidator(normalize_text_input)]


# In[5]:


def pretty_format_json(raw_json_str: str) -> str:
    """Parses a raw JSON string and returns a beautifully indented version."""
    try:
        data = json.loads(raw_json_str)
        return json.dumps(data, indent=4) # indent=4 makes it look clean
    except Exception:
        return raw_json_str # Fallback if it's not a JSON string


# In[6]:


# Below code will help to overcome Jupyter Notebook issue
def print_full_output(text: str):
    """Forces the terminal environment to print the entire text without truncation."""
    # Split the long string into lines and print them one by one
    for line in text.splitlines():
        print(line)
    # Force the terminal to instantly output everything in the queue
    sys.stdout.flush()


# In[7]:


# Universal Protocal Packers and Formatters

# Request wrapper
def wrap_request(msg_id: int, method: str, params: dict) -> str:
    """ Pack a client action into a standardized JSON-RPC 2.0 Text Format """
    payload = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "method": method,
        "params": params
    }
    return json.dumps(payload) # convert dictionary to raw text string


# In[8]:


# Wrap Error Response - To be used by MCP Server

def wrap_error_response(msg_id: int, code: int, message: str) -> str:
    """ Pack a server error into standard JSON-RPC text format. """
    payload = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": f"Error Code: {code}, Message: {message}"
    }
    return json.dumps(payload)


# In[9]:


# Wrap Successful Response  - to be used by MCP Server
def wrap_success_response(msg_id: int, result: Any) -> str:
    """ Pack a successful server result into a standard text format 
    to avoid divercified response types from different end points. """

    payload = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": result
    }

    return json.dumps(payload)


# Creating the MCPServer

# - Creating Agent Classes

# In[10]:


# MCP Server 2 Agents
class EmployeeLookupInput(BaseModel):
    full_name: NormalizedString = Field(description="First and Last name of the employee to search. ")

class SlackAlertInput(BaseModel):
    channel: NormalizedString = Field(description="Target channel starting with a '#' tag. ")
    message_text: NormalizedString = Field(
        description="The notification text content to post to the slack channel. "
    )


# - MCP Server
# 

# In[11]:


class SupportMCPServer:
    def __init__(self):
        self.name = "Networked-Support-Server"
        self.tools_registry = {
            "lookup_employee_email":
            {
                "description": "Searches corporate directory for an email",
                "schema": EmployeeLookupInput.model_json_schema(),
                "model_class": EmployeeLookupInput
            },
            "send_slack_alert": 
            {
                "description": "Dispatches an automated instant message notification to a specific team room.",
                "schema": SlackAlertInput.model_json_schema(),
                "model_class": SlackAlertInput
            }
        }

    def handle_incoming_request(self, raw_json_request: Any) -> str:
        req_id = 0
        try:
            if isinstance(raw_json_request, str):
                request = json.loads(raw_json_request)
            else:
                request = raw_json_request
            #request = json.dumps(raw_json_request)

            req_id = request.get("id", 0)         # default is 0
            method = request.get("method", "")    # default blank method
            params = request.get("params", {})    # default blank dictionary

            # Route 1: Handle Tool Discovery Request

            if method == "tools/list":
                clean_menu = {}
                for name, t in self.tools_registry.items():
                    clean_menu[name] = {
                        "description": t["description"],
                        "schema": t["schema"]
                    }
                return wrap_success_response(req_id, clean_menu)

            if method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})

                # Check if given tool is present into tools-registry
                if tool_name not in self.tools_registry:
                    return wrap_error_response(req_id, -32601, f"Tool : {tool_name} not found .")

                # When given tool is present

                tool_info = self.tools_registry[tool_name]
                ModelClass = tool_info["model_class"]
                validated_data = ModelClass.model_validate(tool_args)

                # Note: model_validate() is built-in function inside Pydantic which acts as a gatekeeper to enforce those rules on incoming data

                # Executing the core logic 
                if tool_name == "lookup_employee_email":
                    mock_directory = {
                        "souvik dhar": "souvik.dhar@hotmail.com", 
                        "jane smith" : "jsmith@gmail.com",
                        "tom alen" : "talen@outlook.com"
                    }
                    search_query = validated_data.full_name.lower()
                    email = mock_directory.get(search_query, "Email profile not found.")
                    return wrap_success_response(
                        req_id, 
                        f"[DIRECTORY] Result : {email}"
                        )
                elif tool_name == "send_slack_alert":                
                    return wrap_success_response(
                        req_id,
                        f"[SLACK] Message successfully delivered to channel '{validated_data.channel}': '{validated_data.message_text}' "
                    )

            else:
                return wrap_error_response(req_id, -32601, f"Method : {method} not found")
        except Exception as e:
            return wrap_error_response(req_id, -32602, f"Server Error : {str(e)}")


# - Defining the MCP Server Instance

# In[12]:


mcp_server_instance = SupportMCPServer()


# - Initialize FastAPI App

# In[13]:


app = FastAPI(title="MCP Support Web Server Endpoint. ")


# - Registering the FastAPI Networking Bridge

# In[14]:


@app.post("/mcp/v1/gateway")
def mcp_network_gateway(payload: Dict[str, Any] = Body(...)):
    # Payload will be of type dictionary
    # - The 'keys' of the dictionary must be of type 'str' 
    # - The 'values' mapped the dictionary key could be absolutely anything such as integers("id":1),
    # strings ("method": "tools/list") or nested subdirectories ("params": {})
    # = Body(...) - Overrides the default behaviour or sending parameters over embedded URL 
    # (/gateway?id=1&method=tools/list). It asks FastAPI to wait till the entire payload is being
    # transmitted over network, look inside the hidden HTTP Request Body and parse that raw text stream
    # into python dictionary

    """
    A single universal endpoint. It behaves exactly like an I/O cable, passing raw dictionary payload
    directly into our explicit server object
    """

    raw_json_stirng = json.dumps(payload)
    raw_string_response = mcp_server_instance.handle_incoming_request(raw_json_stirng)

    return json.loads(raw_string_response)


# - Uvicorn Server Start/Stop process

# In[15]:


# Check if a given port on local host is already occupied or not
def is_port_in_use(port: int) -> dict:
    """
    Check if a local TCP/IPv4 or TCP/IPv6 port is already occupied
    by an active listening process.
    """
    try:
        for conn in psutil.net_connections(kind="inet"):
            if not conn.laddr:
                continue

            if conn.laddr.port != port:
                continue

            # For server-port conflict, only LISTEN matters.
            if conn.status != psutil.CONN_LISTEN:
                continue

            if conn.pid:
                try:
                    proc = psutil.Process(conn.pid)
                    return {
                        "in_use": True,
                        "process_name": proc.name(),
                        "pid": conn.pid
                    }
                except psutil.NoSuchProcess:
                    return {
                        "in_use": True,
                        "process_name": "Dormant/No Process name found",
                        "pid": conn.pid
                    }
                except psutil.AccessDenied:
                    return {
                        "in_use": True,
                        "process_name": "Access Denied / Protected System",
                        "pid": conn.pid
                    }

            return {
                "in_use": True,
                "process_name": "Unknown Process",
                "pid": None
            }

    except Exception as e:
        print(f"[Warning] Failed to scan connections via psutil:\n{str(e)}")

    return {
        "in_use": False,
        "process_name": None,
        "pid": None
    }


# In[16]:


# Run Uvicorn server

def run_uvicorn_server(port: int):
    """
    Target function execute entirely inside the independent background process
    """

    uvicorn.run(
        app=app, 
        host="127.0.0.1", 
        port=port, 
        log_level="error"
    )


# In[17]:


# Start MCP Service

def start_mcp_service(port) -> Process:
    """ 
    Check the environment and safely boots up the background server process.
    """
    port_status = is_port_in_use(port)
    if port_status["in_use"]:
        print("\n" + "═"*70)
        print(" ⚠️  PORT CONFLICT DETECTED")
        print("═"*70)
        print(f" -> Port {port} is occupied. Skipping background server launch.")
        print(f" -> Owning Process Name : '{port_status['process_name']}'")
        print(f" -> Active Process ID   : {port_status['pid']}")
        print("═"*70 + "\n")
        return None

    # if port is not occupied
    print(f"[System Info] Port '{port}' is free. Booting up background process .")
    server_process = Process(target=run_uvicorn_server, args=(port,), daemon=True)
    server_process.start()

    # Wait until the fresh uvicorn server finishes  booting and claims the port
    dots = 0
    max_checks = 20
    checks_done = 0
    while checks_done < max_checks:

        check = is_port_in_use(port)
        if check["in_use"]:
            # Clear the loading text line completely before printing the success message
            print("\r" + " " * 60 + "\r", end="", flush=True) 
            break 


        # ✅ NEW: Check if process died early (important signal)
        if not server_process.is_alive():
            raise RuntimeError(
                f"Uvicorn process terminated before binding to port {port}. Check startup errors."
            )


        print(f"\r⌛ Uvicorn Server is still booting up{'.' * (dots % 4 + 1)}   ", end="", flush=True)
        checks_done += 1
        dots += 1
        time.sleep(0.2)

    
    if checks_done >= max_checks:
        raise RuntimeError(
        f"Timeout: Uvicorn did not bind to port {port}."
        )

    print(f"[System Info] Background Uvicorn service successfully listening on port {port}!")
    return server_process


# MCP Client Class

# In[ ]:


class SimpleMCPClient:
    def __init__(self, mcp_server_url: str):
        self.mcp_server_url = mcp_server_url
        self.request_counter = 1
        self.discovered_tools = {}

    def _transmit_over_network(self, raw_json_request: str) -> str:
        """
        Helper that replace directy memory access with an HTTP web transport.
        """
        # convert string back to dict for the requests library payload format
        dict_payload = json.loads(raw_json_request)

         # 🔍 ADD THIS DIAGNOSTIC LINE TO TRACK TRUNCATION:
        print(f"🕵️ DEBUG TRACE -> self.mcp_server_url value is: '{self.mcp_server_url}'")

        # Sending the packet to the mcp_server
        response = requests.post(self.mcp_server_url, json=dict_payload)

        return json.dumps(response.json())

    def list_tools(self):
        msg_id = self.request_counter
        self.request_counter += 1

        # Request tools from this specific server
        raw_request = wrap_request(msg_id=msg_id, method="tools/list", params={})
        print(f"\n[Client -> Wire]: {raw_request}")

        raw_response = self._transmit_over_network(raw_request)

         # Parse response
        response_dict = json.loads(raw_response)
        tools_found = response_dict.get("result", {})


        print("\n" + "="*60 + "\n 📋 EXPLICIT CLIENT RECEIVED NETWORK DISCOVERY SUMMARY:\n" + "="*60)
        print(f"\n📡 Discovered {len(tools_found)} tools from server [{self.mcp_server_url}]:")
        for tool_name, tool_details in tools_found.items():
                print(f"  🔹 Tool: {tool_name}")
                print(f"     Description: {tool_details.get('description')}")

                # CRITICAL STEP: Remember which server owns this tool name!
                self.discovered_tools = tools_found


        #print("\n" + "="*60 + "\n 📋 EXPLICIT CLIENT RECEIVED NETWORK DISCOVERY SUMMARY:\n" + "="*60)
        #print_full_output(pretty_format_json(raw_response))

    def call_tool(self, tool_name: str, arguments: dict):
        msg_id = self.request_counter
        self.request_counter += 1

        params_payload = {
            "name": tool_name,
            "arguments": arguments
        }

        raw_request = wrap_request(msg_id=msg_id, method="tools/call", params=params_payload)
        print(f"\n[Client -> Wire]: {raw_request}")

        #Explicit call to the MCP Server using _transmit_over_network() function
        raw_response = self._transmit_over_network(raw_request)

        print("\n" + "#"*60 + "\n 📥 EXPLICIT CLIENT RECEIVED NETWORK EXECUTION RESPONSE:\n" + "#"*60)
        print_full_output(pretty_format_json(raw_response))



# - Creating Entry point for users, the "main" function

# In[ ]:


if __name__ == "__main__":
    # ✅ FIX 1: Point to complete loopback IP address, target port 8000, and gateway route path
    MCP_HOST = "127.0.0.1"
    MCP_PORT = 8000
    GATEWAY_URL = f"http://{MCP_HOST}:{MCP_PORT}/mcp/v1/gateway"

    print(f"[DEBUG] GATEWAY_URL = {GATEWAY_URL}")

    # Trying to bring the MCP Process using uvicorn
    try:
        mcp_process = start_mcp_service(MCP_PORT)

        try:
            # Instantiate the MCP Client
            my_mcp_client = SimpleMCPClient(mcp_server_url=GATEWAY_URL)

            # 1. Trigger network discovery handshake
            my_mcp_client.list_tools()

            print("\n" + "═"*60)
            print(" 🕹️  ENTERED INTERACTIVE MCP CONSOLE RUNTIME")
            print("═"*60)
            print("Type 'exit' at any prompt to terminate the session.\n")

            while True:
                # Build available tool options list tracking index using network dictionary cache
                available_tools = list(my_mcp_client.discovered_tools.keys())

                if not available_tools:
                    print("❌ No tools discovered on connected servers. Exiting system.")
                    break

                print("\n--- 📋 AVAILABLE SYSTEM TOOLS ---")
                for index, tool_name in enumerate(available_tools, start=1):
                    tool_data = my_mcp_client.discovered_tools[tool_name]
                    desc = tool_data["description"]
                    print(f"[{index}] {tool_name:<25} \n    Summary: {desc}")

                print("-" * 60) 

                # Get the tool selection choice for the user
                user_choice = input("\nEnter the Tool Number or Tool Name to Execute: ").strip()

                if user_choice.lower() in {"exit", "bye", "done"}:
                    print("\nShutting down interactive MCP console context. Goodbye!")
                    break 

                selected_tool = None 
                if user_choice.isdigit():
                    idx = int(user_choice) - 1
                    if 0 <= idx < len(available_tools):
                        selected_tool = available_tools[idx]
                elif user_choice in available_tools:
                    selected_tool = user_choice

                if not selected_tool:
                    print("⚠️  Invalid tool selection choice option. Please try again.")
                    continue

                # Fetch properties using raw text dictionaries returned over HTTP path channel wire
                tool_data = my_mcp_client.discovered_tools[selected_tool]
                schema_properties = tool_data["schema"].get("properties", {})

                print(f"\n📝 Gathering arguments for '{selected_tool}':")
                user_arguments = {}
                cancelled = False

                for field_name, field_info in schema_properties.items():
                    desc_text = field_info.get("description", "No description available")
                    expected_type = field_info.get("type", "string")

                    print(f" 🔹 Field [{field_name}]: {desc_text} (Expected Type: {expected_type})")
                    field_input = input(f"    Enter value for {field_name}: ").strip()

                    if field_input.lower() == 'exit':
                        cancelled = True 
                        break 

                    # Safe string/array type converter logic block for network client interface
                    if expected_type == "array":
                        user_arguments[field_name] = [item.strip() for item in field_input.split(",") if item.strip()] if field_input else []
                    else:
                        user_arguments[field_name] = field_input

                if cancelled:
                    print("❌ Tool call execution execution routine abandoned.")
                    continue

                # Hand inputs over to the Client Router for dispatch processing across gateway path
                my_mcp_client.call_tool(selected_tool, user_arguments)

        finally:
            # 3. Graceful shutdown handler intercept
            print("\n" + "═"*60)
            print(" 🛑 SERVICE SHUTDOWN CONTROLLER ACTIVATED")
            print("═"*60)

            # ✅ FIX 2: Correctly capture and chain string cleaning functions to save the input state
            user_input = input("Do you want to stop Uvicorn Service? (yes/no): ").strip().lower()

            # ✅ FIX 3: Check string validation matching conditions natively (string in list)
            if user_input in ["yes", "y"]:
                if mcp_process and mcp_process.is_alive():
                    print("[System Info] Terminating background Uvicorn service process cleanly...")
                    mcp_process.terminate()
                    mcp_process.join()
                    print("[System Info] Uvicorn service stopped. Port 8000 released.")
                else:
                    print("[System Info] No local background process to terminate (uvicorn is running externally).")
            else:
                print("[System Info] Exiting script console loop but leaving the Uvicorn service instance running in the background.")

    except Exception as e:
        print(f"❌ Runtime Error occurred: \n{str(e)}")

