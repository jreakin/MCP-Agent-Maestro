# Agent-MCP/mcp_template/mcp_server_src/tools/registry.py
from typing import List, Dict, Any, Callable, Awaitable, Optional, Union
import mcp.types as mcp_types # Assuming this is the correct import for your mcp.types

# Import utility for JSON sanitization, as handle_tool uses it
from ..utils.json_utils import sanitize_json_input, get_sanitized_json_body
# Import the central logger
from ..core.config import logger

# Tool implementations will be imported here once they are created.
# For now, we'll define placeholders for the functions they will call.
# These will be replaced by actual imports from other tool modules.
# e.g., from .admin_tools import create_agent_tool_impl, view_status_tool_impl, ...
#       from .task_tools import assign_task_tool_impl, ...
#       from .rag_tools import ask_project_rag_tool_impl

# --- Tool Function Placeholders (to be replaced by actual imports) ---
# These represent the core logic of each tool, now separated from parsing/auth.
async def placeholder_tool_logic(*args, **kwargs) -> List[mcp_types.TextContent]:
    tool_name = kwargs.get('_tool_name', 'unknown_placeholder_tool')
    logger.warning(f"Placeholder logic called for tool: {tool_name} with args: {args}, kwargs: {kwargs}")
    return [mcp_types.TextContent(type="text", text=f"Placeholder response for {tool_name}. Not implemented in registry yet.")]

# This dictionary will map tool names to their implementation functions.
# It will be populated by importing and assigning the actual tool functions.
# Example:
# tool_implementations: Dict[str, Callable[..., Awaitable[List[mcp_types.TextContent]]]] = {
# "create_agent": create_agent_tool_impl, # from .admin_tools
# "view_status": view_status_tool_impl,   # from .admin_tools
# ... and so on for all tools
# }
# For now, it's empty and will be filled as we create the tool modules.
tool_implementations: Dict[str, Callable[..., Awaitable[List[mcp_types.TextContent]]]] = {}

# This list will hold the schema definitions for all tools.
# It will be populated by defining each tool's schema.
# Example entry:
# {
# "name": "create_agent",
# "description": "Create a new agent...",
# "inputSchema": { ... schema ... }
# }
tool_schemas: List[Dict[str, Any]] = []


# --- Core Tool Registry Functions ---

def register_tool(
    name: str,
    description: str,
    input_schema: Dict[str, Any],
    implementation: Callable[..., Awaitable[List[mcp_types.TextContent]]]
):
    """
    Registers a tool's schema and its implementation.
    This function will be called by each tool module to register itself.
    """
    global tool_schemas, tool_implementations
    
    # Check for duplicate tool names
    if name in tool_implementations:
        logger.warning(f"Tool '{name}' is being re-registered. Overwriting previous definition.")

    tool_schemas.append({
        "name": name,
        "description": description,
        "inputSchema": input_schema
        # mcp.types.Tool in the original also had an outputSchema, which can be added if needed.
    })
    tool_implementations[name] = implementation
    logger.info(f"Registered tool: {name}")


async def list_available_tools() -> List[mcp_types.Tool]:
    """
    Returns a list of available tools with their schemas.
    This replaces the logic from `@app.list_tools()` in main.py (lines 1636-1858).
    It now reads from the `tool_schemas` list populated by `register_tool`.
    """
    from ..core.config import SECURITY_ENABLED, SECURITY_SCAN_TOOL_SCHEMAS
    from ..security import PoisonDetector
    
    # Convert the stored schema dictionaries to mcp_types.Tool objects
    # The original code directly returned a list of mcp_types.Tool.
    # We need to ensure the structure matches.
    
    # The `tool_schemas` list already contains dictionaries in the format
    # that can be directly used to instantiate `mcp_types.Tool` if the keys match.
    # Let's assume `mcp_types.Tool` can be constructed from a dictionary
    # with 'name', 'description', and 'inputSchema'.
    
    mcp_tool_list: List[mcp_types.Tool] = []
    detector = PoisonDetector() if (SECURITY_ENABLED and SECURITY_SCAN_TOOL_SCHEMAS) else None
    
    for schema_dict in tool_schemas:
        try:
            # Security scan if enabled
            if detector:
                scan_result = await detector.scan_tool_schema(schema_dict)
                if not scan_result.safe:
                    logger.warning(
                        f"Tool '{schema_dict.get('name')}' failed security scan: "
                        f"{[t.type for t in scan_result.threats]}"
                    )
                    # Optionally skip unsafe tools or sanitize them
                    # For now, we'll log and continue
            
            # Assuming mcp_types.Tool can be initialized like this:
            # Tool(name="...", description="...", inputSchema={...})
            # If it requires specific keyword arguments, adjust accordingly.
            # The original `types.Tool` in main.py was directly instantiated.
            tool_instance = mcp_types.Tool(
                name=schema_dict["name"],
                description=schema_dict["description"],
                inputSchema=schema_dict["inputSchema"]
                # outputSchema=schema_dict.get("outputSchema") # If you add outputSchema
            )
            mcp_tool_list.append(tool_instance)
        except Exception as e:
            logger.error(f"Failed to create mcp_types.Tool instance for '{schema_dict.get('name', 'Unknown')}': {e}", exc_info=True)
            # Optionally, skip this tool or add a placeholder error tool.
            # For now, skipping problematic ones.

    return mcp_tool_list


async def dispatch_tool_call(
    tool_name: str,
    raw_arguments: Union[Dict[str, Any], List[Dict[str, Any]]] # Original accepted list or dict
) -> List[mcp_types.TextContent]:
    """
    Handles a tool call by dispatching to the appropriate implementation.
    This replaces the logic from `@app.call_tool()` in main.py (lines 1861-1931).
    """
    # Sanitize arguments input (main.py:1863-1877)
    sanitized_arguments: Any
    try:
        if isinstance(raw_arguments, list):
            # The original code had a recursive call to handle_tool for lists.
            # This is complex. A simpler approach is to define if tools accept lists of args
            # or if the client should make individual calls.
            # For 1-to-1 with original `handle_tool`'s list processing:
            # This implies that a single tool call message could contain a list of argument sets
            # for the *same* tool, and the server processes them sequentially, concatenating results.
            # This is an unusual pattern for tool calls.
            # Let's assume for now that a tool call is for one set of arguments.
            # If the list processing is essential, it needs careful thought on how it interacts
            # with individual tool function signatures.
            # The original code:
            # if isinstance(arguments, list):
            #     sanitized_args = []
            #     for arg in arguments:
            #         sanitized_args.append(sanitize_json_input(arg))
            #     results = []
            #     for arg in sanitized_args:
            #         res = await handle_tool(name, arg) # Recursive call
            #         results.extend(res)
            #     return results
            # This recursive structure is problematic for a clean dispatch.
            # For now, we will assume `raw_arguments` is a single dictionary for one tool call.
            # If list processing for a single tool name is needed, the tool implementation itself
            # should be designed to handle a list of argument sets.
            # The MCP protocol itself (mcp.types) might clarify if a "tool_call" message
            # can have a list of argument sets.
            # Given the structure of `call_mcp_tool` in the prompt (singular arguments),
            # it's more likely `raw_arguments` is a single Dict.
            if isinstance(raw_arguments, dict):
                sanitized_arguments = sanitize_json_input(raw_arguments)
            else: # If it's a list, and we are not supporting recursive calls here.
                logger.error(f"Received a list of arguments for tool '{tool_name}', but registry expects a single argument dictionary per call.")
                return [mcp_types.TextContent(type="text", text="Error: Server tool dispatcher expects a single argument set, not a list.")]

        elif not isinstance(raw_arguments, dict):
            # Try to sanitize and parse if not a dict (e.g., a JSON string from a raw request)
            sanitized_arguments = sanitize_json_input(raw_arguments)
            if not isinstance(sanitized_arguments, dict):
                # If after sanitization it's still not a dict, it's an invalid format.
                raise ValueError(f"Tool arguments for '{tool_name}' must be a dictionary after sanitization, got {type(sanitized_arguments)}")
        else: # It's already a dict
            sanitized_arguments = sanitize_json_input(raw_arguments) # Still sanitize it

    except ValueError as e:
        logger.error(f"Invalid input arguments for tool '{tool_name}': {e}")
        return [mcp_types.TextContent(type="text", text=f"Invalid input arguments: {str(e)}")]
    except Exception as e: # Catch any other sanitization errors
        logger.error(f"Error sanitizing arguments for tool '{tool_name}': {e}", exc_info=True)
        return [mcp_types.TextContent(type="text", text=f"Error processing tool arguments: {str(e)}")]


    # Dispatch to the correct tool implementation (main.py:1879 onwards)
    if tool_name in tool_implementations:
        implementation_func = tool_implementations[tool_name]
        try:
            # Security: Scan and monitor tool execution if enabled
            from ..core.config import SECURITY_ENABLED, SECURITY_SCAN_TOOL_RESPONSES
            from ..security import PoisonDetector, ResponseSanitizer, SecurityMonitor
            from ..core import globals as g
            
            detector = None
            sanitizer = None
            monitor = None
            
            if SECURITY_ENABLED:
                if SECURITY_SCAN_TOOL_RESPONSES:
                    detector = PoisonDetector()
                    from ..core.config import SECURITY_SANITIZATION_MODE
                    sanitizer = ResponseSanitizer(mode=SECURITY_SANITIZATION_MODE)
                
                # Initialize monitor if not already done
                if not hasattr(g, 'security_monitor'):
                    g.security_monitor = SecurityMonitor()
                    from ..core.config import SECURITY_ALERT_WEBHOOK
                    if SECURITY_ALERT_WEBHOOK:
                        g.security_monitor.set_alert_webhook(SECURITY_ALERT_WEBHOOK)
                monitor = g.security_monitor
            
            # Security: Scan tool arguments before execution
            if detector:
                # Scan arguments for injection attempts
                arguments_str = str(sanitized_arguments)
                arg_scan_result = await detector.scan_text(
                    arguments_str,
                    context=f"tool.{tool_name}.arguments"
                )
                if not arg_scan_result.safe:
                    logger.warning(
                        f"Tool arguments for '{tool_name}' contained threats: "
                        f"{[t.type for t in arg_scan_result.threats]}"
                    )
                    # Log security alert
                    if monitor:
                        from ..security.models import SecurityAlert
                        alert = SecurityAlert(
                            severity='HIGH',
                            message=f"Security threat detected in tool arguments for '{tool_name}'",
                            details={
                                'tool_name': tool_name,
                                'threats': [t.type for t in arg_scan_result.threats],
                                'threat_count': len(arg_scan_result.threats)
                            },
                            tool_name=tool_name
                        )
                        await monitor.alert_queue.put(alert)
                    
                    # Block execution if critical threat detected
                    critical_threats = [t for t in arg_scan_result.threats if t.severity in ['HIGH', 'CRITICAL']]
                    if critical_threats:
                        logger.error(
                            f"Blocking tool execution '{tool_name}' due to critical security threat in arguments"
                        )
                        return [mcp_types.TextContent(
                            type="text",
                            text=f"Security Error: Tool execution blocked due to detected security threat in arguments."
                        )]
            
            # Execute tool
            result = await implementation_func(sanitized_arguments)
            
            # Security: Scan response and track usage
            if monitor:
                # Extract agent_id from arguments if available
                agent_id = sanitized_arguments.get('agent_id') or sanitized_arguments.get('token', 'unknown')
                # Convert result to string for monitoring
                response_str = ' '.join([item.text for item in result if hasattr(item, 'text')])
                await monitor.track_tool_call(
                    agent_id=str(agent_id),
                    tool_name=tool_name,
                    tool_params=sanitized_arguments,
                    response=response_str
                )
            
            if detector and sanitizer:
                # Scan each text content item
                sanitized_result = []
                for item in result:
                    if hasattr(item, 'text'):
                        scan_result = await detector.scan_tool_response(item.text)
                        if not scan_result.safe:
                            logger.warning(
                                f"Tool response from '{tool_name}' contained threats: "
                                f"{[t.type for t in scan_result.threats]}"
                            )
                            
                            # Log security alert for response threats
                            if monitor:
                                from ..security.models import SecurityAlert
                                alert = SecurityAlert(
                                    severity='HIGH',
                                    message=f"Security threat detected in tool response for '{tool_name}'",
                                    details={
                                        'tool_name': tool_name,
                                        'threats': [t.type for t in scan_result.threats],
                                        'threat_count': len(scan_result.threats)
                                    },
                                    tool_name=tool_name
                                )
                                await monitor.alert_queue.put(alert)
                            
                            sanitized_text = sanitizer.sanitize(item.text, scan_result)
                            sanitized_result.append(mcp_types.TextContent(type="text", text=sanitized_text))
                        else:
                            sanitized_result.append(item)
                    else:
                        sanitized_result.append(item)
                return sanitized_result

            return result

        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
            return [mcp_types.TextContent(type="text", text=f"Internal error executing tool '{tool_name}': {str(e)}")]
    else:
        logger.warning(f"Unknown tool called: {tool_name}")
        # Original main.py:1930 (raise ValueError(f"Unknown tool: {name}"))
        # Returning an error message is friendlier for an API.
        return [mcp_types.TextContent(type="text", text=f"Error: Unknown tool '{tool_name}'.")]

# The actual tool schemas and implementations will be populated by calls to `register_tool`
# from each of the specific tool modules (e.g., admin_tools.py, task_tools.py, etc.)
# when those modules are imported by the application (e.g., in mcp_server_src/tools/__init__.py).