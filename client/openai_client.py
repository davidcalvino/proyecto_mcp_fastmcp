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
    
    # Agregar todos los outputs al historial para dar contexto continuo
    if response.output:
        input_list.extend(response.output)
    
    # Extraer los tool_calls si el modelo decidió usar herramientas
    tool_calls = [item for item in response.output if item.type == "function_call"]
    
    if tool_calls:
        for tool_call in tool_calls:
            name = tool_call.name
            args = json.loads(tool_call.arguments)
            
            try:
                # Ejecutar herramienta a través del protocolo MCP con reintentos
                result = await _call_mcp_tool_with_retries(session, name, args)
                
                # Extraer texto de la respuesta MCP
                content_list = []
                for res_item in result.content:
                    if res_item.type == "text":
                        content_list.append(res_item.text)
                content_str = "\n".join(content_list)
            except Exception as e:
                # Error en la herramienta devuelto como contexto a OpenAI
                content_str = f"Error al ejecutar {name}: {str(e)}"
            
            # Formato requerido por la Responses API para el resultado
            input_list.append({
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": content_str
            })
            
        # Llamada recursiva tras procesar herramientas
        return await process_agent_turn(input_list, session, openai_tools)
    
    return response.output_text

