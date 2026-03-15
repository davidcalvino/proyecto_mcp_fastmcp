# Servidor y Cliente MCP: Clima y Monedas

Este proyecto implementa un agente de Inteligencia Artificial que conecta **OpenAI** (utilizando la nueva *Responses API*) con un servidor de herramientas basado en el estándar **Model Context Protocol (MCP)** mediante **FastMCP**.

El sistema proporciona capacidades conversacionales enriquecidas con datos externos confiables como consultas del clima (usando Open-Meteo) y conversión de monedas actualizada (usando ExchangeRate-API).

---

## 🚀 Requisitos e Instalación

1. **Clona y Prepara el Entorno**
   Crea un entorno virtual e instala las dependencias ubicadas en \`requirements.txt\`:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configura tus Claves de API**
   Copia el archivo base para configurar tus credenciales como variables de entorno:
   ```bash
   cp .env.example .env
   ```
   Abre el archivo `.env` resultante y agrega:
   - `OPENAI_API_KEY`: Tu clave de la API de OpenAI.
   - `EXCHANGERATE_API_KEY`: Tu clave de ExchangeRate-API.
   - `SERVER_PORT`: El puerto del servidor MCP (por defecto 8000).

---

## 💻 Uso de la Aplicación

El sistema está dividido en dos procesos autónomos que se comunican mediante Server-Sent Events (SSE). Es fundamental iniciar siempre primero el servidor.

1. **Inicia el Servidor MCP:**
   Abre una terminal y ejecuta:
   ```bash
   python main_server.py
   ```
2. **Inicia el Cliente (Agente de OpenAI):**
   Abre una segunda terminal interactiva y ejecuta:
   ```bash
   python main_client.py
   ```

### Comandos de la CLI
La Interfaz de Línea de Comandos (CLI) cuenta con soporte integrado para procesar comandos explícitos garantizando orquestación nativa, además de aceptar lenguaje natural:

- `/clima <ciudad>`: Interroga de manera forzada la API de geocodificación para obtener coordenadas exactas y seguidamente consulta el clima de la región. Todo de forma secuencial garantizada sin inferencias del modelo.
- `/monedas`: Solicita y muestra de manera estructurada una lista extensa de los códigos ISO de divisas disponibles para convertir (ej. USD, EUR, MXN).
- `/ayuda`: Despliega la documentación interna de la CLI.
- `/salir`: Finaliza la ejecución del cliente.

Si escribes oraciones en lenguaje natural (ej. "*Convierte 50 USD a EUR*"), el cliente canalizará el mensaje hacia la Responses API de OpenAI.

---

## 🛡️ Manejo de Errores y Límites (Rate Limits)

Esta aplicación presenta mecanismos de resiliencia explícitos frente a errores externos:

- **Red y Conectividad**: Internamente, tanto las llamadas hacia las API externas desde el servidor, como la comunicación del cliente con el servidor y OpenAI integran estrategias de *Exponential Backoff*. Si una solicitud de red falla por Timeouts (`APITimeoutError`) o Errores de Conexión, el sistema realizará hasta 3 reintentos incrementando la demora, antes de abortar de manera controlada.
- **Validación y Entidades No Encontradas**: Si solicitas geocodificar una ciudad inválida o inexistente (ej. `/clima Xyz123`), el sistema detectará el fallo en la API y retornará un mensaje amigable al usuario (e.g. *La ciudad no pudo ser localizada en el mapa*), en lugar de detener la ejecución de cuajo o mostrar un rastro de excepción (*stacktrace*).
- **Rate Limits Excedidos**: Excepciones de corte transversal como el exceso de cuota (`RateLimitError` emitido por OpenAI o agotamiento de consultas al servidor de terceros) son interceptadas en el cliente informando a través de consola para alertar al administrador sobre límites de uso agotados.
