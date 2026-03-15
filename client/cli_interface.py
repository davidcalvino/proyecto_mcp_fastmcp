import asyncio
from client.openai_client import process_agent_turn, _call_mcp_tool_with_retries
from mcp import ClientSession
from mcp.client.sse import sse_client
from config.settings import SERVER_PORT

async def start_cli_async():
    print("=== Asistente MCP (Clima y Monedas) ===")
    print("Usando FastMCP y OpenAI Responses API.")
    print("Escribe /ayuda para ver comandos, /salir para terminar.")
    
    url = f"http://127.0.0.1:{SERVER_PORT}/sse"
    
    # Mantenemos la conexión SSE abierta durante toda la sesión
    async with sse_client(url) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            
            mcp_tools = await session.list_tools()
            openai_tools = []
            
            # Traducción del esquema MCP al formato de Responses API
            for tool in mcp_tools.tools:
                openai_tools.append({
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                })
            
            input_list = [{"role": "user", "content": "Eres un asistente útil que responde consultas de clima y monedas. Para el clima, primero geocodifica la ciudad y luego pide el clima usando lat y lon. Responde directamente sin preámbulos."}]
            
            while True:
                try:
                    user_input = input("\n> ")
                except EOFError:
                    break
                    
                cmd = user_input.strip()
                if cmd == "/salir":
                    print("Saliendo...")
                    break
                elif cmd == "/ayuda":
                    print("Comandos disponibles:")
                    print("/salir   - Salir del programa")
                    print("/ayuda   - Mostrar esta ayuda")
                    print("/monedas - Listar códigos de monedas soportados")
                    print("/clima <ciudad> - Consultar el clima explícitamente")
                    print("Ejemplos en chat: 'Convierte 100 USD a EUR', '¿Qué tiempo hace en Madrid?'")
                    continue
                elif cmd == "/monedas":
                    print("Obteniendo lista de monedas soportadas...")
                    try:
                        # Usamos EUR como base arbitraria para obtener la lista
                        result = await _call_mcp_tool_with_retries(session, "tool_get_exchange_rates", {"base": "EUR"})
                        
                        raw_content = next((item.text for item in result.content if item.type == "text"), "{}")
                        import json
                        data = json.loads(raw_content)
                        rates = data.get("conversion_rates", {})
                        monedas = list(rates.keys())
                        
                        if monedas:
                            print(f"\nSe soportan {len(monedas)} monedas. Algunas principales:")
                            # Mostrar 15 principales para no saturar
                            print(", ".join(monedas[:15]) + " ...")
                        else:
                            print("\nNo se pudieron cargar las monedas en este momento.")
                            
                    except Exception as e:
                        print("\n❌ Error: No se pudo conectar con el servicio de monedas.")
                        print(f"Detalle técnico: {e}")
                    continue
                elif cmd.startswith("/clima "):
                    ciudad = cmd.replace("/clima ", "").strip()
                    if not ciudad:
                        print("Por favor, especifica una ciudad. Ejemplo: /clima Madrid")
                        continue
                        
                    print(f"Buscando coordenadas para '{ciudad}'...")
                    try:
                        geocode_res = await _call_mcp_tool_with_retries(session, "tool_geocode_city", {"city": ciudad})
                        raw_geo = next((item.text for item in geocode_res.content if item.type == "text"), "{}")
                        import json
                        geo_data = json.loads(raw_geo)
                        
                        if "latitude" not in geo_data:
                            # Puede ser que el fetch dict dictaminó un ValueError encapsulado en el texto o vacío
                            raise ValueError(f"No se encontró la ciudad: {ciudad}")
                            
                        lat, lon = geo_data["latitude"], geo_data["longitude"]
                        pais = geo_data.get("country", "")
                        print(f"📍 Encontrado: {ciudad} ({pais}) -> Lat: {lat}, Lon: {lon}")
                        
                        print("Obteniendo clima actual...")
                        weather_res = await _call_mcp_tool_with_retries(session, "tool_get_current_weather", {"lat": lat, "lon": lon})
                        raw_weather = next((item.text for item in weather_res.content if item.type == "text"), "{}")
                        weather_data = json.loads(raw_weather)
                        
                        temp = weather_data.get("temperature", "N/A")
                        wind = weather_data.get("windspeed", "N/A")
                        print(f"\n🌤️  Clima en {ciudad}: {temp}°C, Viento: {wind} km/h")
                        
                    except Exception as e:
                        msg = str(e)
                        if "No se encontró" in msg or "not found" in msg.lower():
                            print(f"\n❌ Error: La ciudad '{ciudad}' no pudo ser localizada en el mapa. Revisa la ortografía.")
                        elif "connect" in msg.lower() or "timeout" in msg.lower():
                            print("\n❌ Error de red: Hubo un problema de conexión al intentar obtener los datos. Por favor verifica tu conexión a internet o intenta más tarde.")
                        else:
                            print(f"\n❌ Ocurrió un error inesperado al consultar el clima: {msg}")
                    continue
                    
                # Si no es un comando explícito, delegar a OpenAI
                input_list.append({"role": "user", "content": user_input})
                try:
                    response_text = await process_agent_turn(input_list, session, openai_tools)
                    print(f"\nAsistente: {response_text}")
                except Exception as e:
                    print(f"\n❌ Error de comunicación con OpenAI o el servidor MCP: {e}")
                    input_list.pop() # Eliminar el mensaje que falló

def start_cli():
    try:
        asyncio.run(start_cli_async())
    except KeyboardInterrupt:
        print("\nSaliendo...")

