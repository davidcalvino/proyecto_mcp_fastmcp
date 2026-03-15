import json
import asyncio
import logging
from openai import AsyncOpenAI, APIConnectionError, APITimeoutError, RateLimitError, APIStatusError
from mcp import ClientSession
from config.settings import OPENAI_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def _call_openai_with_retries(input_list: list, openai_tools: list, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return await client.responses.create(
                model="gpt-4o",
                input=input_list,
                tools=openai_tools
            )
        except (APIConnectionError, APITimeoutError) as e:
            logger.warning(f"Error de conectividad con OpenAI (intento {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise RuntimeError(f"Fallo al conectar con OpenAI tras {max_retries} intentos: {e}")
        except RateLimitError as e:
            logger.warning(f"Límite de cuota excedido en OpenAI (intento {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise RuntimeError(f"Límite de cuota finalizado o superado persistente: {e}")
        except APIStatusError as e:
            logger.error(f"Error devuelto por la API de OpenAI (HTTP {e.status_code}): {e}")
            raise RuntimeError(f"La API de OpenAI regresó un error HTTP {e.status_code}: {e}")
            
        await asyncio.sleep(2 ** attempt)  # Exponential backoff

async def _call_mcp_tool_with_retries(session: ClientSession, name: str, args: dict, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return await session.call_tool(name, args)
        except Exception as e:
            logger.warning(f"Error de conectividad/ejecución con servidor MCP al llamar '{name}' (intento {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise RuntimeError(f"Error persistente al ejecutar {name} en el servidor MCP tras {max_retries} intentos: {e}")
            await asyncio.sleep(2 ** attempt)

async def process_agent_turn(input_list: list, session: ClientSession, openai_tools: list) -> str:
    """Procesa un turno conversacional recursivo con la Responses API de OpenAI"""
    try:
        response = await _call_openai_with_retries(input_list, openai_tools)
    except Exception as e:
        return f"Error crítico al comunicarse con OpenAI: {str(e)}"
    
    output_items = getattr(response, "output", [])
    if output_items is None:
        output_items = []
    elif not isinstance(output_items, (list, tuple)):
        output_items = [output_items]
        
    # Agregar todos los outputs al historial para dar contexto continuo
    if output_items:
        input_list.extend(output_items)
    
    tool_calls = []
    for item in output_items:
        if getattr(item, "type", None) == "function_call" and hasattr(item, "call_id"):
            tool_calls.append(item)
    
    if tool_calls:
        for tool_call in tool_calls:
            name = getattr(tool_call, "name", "")
            raw_args = getattr(tool_call, "arguments", "{}")
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except json.JSONDecodeError:
                args = {}
            
            try:
                # Ejecutar herramienta a través del protocolo MCP con reintentos
                result = await _call_mcp_tool_with_retries(session, name, args)
                
                # Extraer texto de la respuesta MCP
                content_list = []
                if hasattr(result, "content") and isinstance(result.content, list):
                    for res_item in result.content:
                        if getattr(res_item, "type", None) == "text" and hasattr(res_item, "text"):
                            content_list.append(res_item.text)
                content_str = "\n".join(content_list)
            except Exception as e:
                content_str = f"Error al ejecutar {name}: {str(e)}"
            
            input_list.append({
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": content_str
            })
            
        # Llamada recursiva tras procesar herramientas
        return await process_agent_turn(input_list, session, openai_tools)
    
    return getattr(response, "output_text", str(response))

