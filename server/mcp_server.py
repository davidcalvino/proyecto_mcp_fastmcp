import os
from mcp.server.fastmcp import FastMCP
from .currency_tools import convert_currency, get_exchange_rates
from .geocoding_tools import geocode_city
from .weather_tools import get_current_weather, get_weather_forecast

# Inicializar FastMCP
mcp = FastMCP("ServidorClimaMonedas")

@mcp.tool()
def tool_convert_currency(amount: float, source: str, target: str) -> dict:
    """Convierte una cantidad monetaria específica de una moneda de origen a una de destino.
    
    Esta herramienta contacta a un servicio de tasas de cambio actualizado en tiempo real
    y devuelve el valor convertido aplicando la tasa correspondiente. Se utiliza para cálculos
    y conversiones financieras entre divisas globales.
    
    Args:
        amount (float): La cantidad numérica de la moneda origen a convertir. Debe ser un número positivo.
        source (str): Código ISO de 3 letras de la moneda origen (ej. 'USD', 'EUR', 'JPY').
        target (str): Código ISO de 3 letras de la moneda destino (ej. 'MXN', 'GBP', 'CAD').
        
    Returns:
        dict: Un diccionario con el resultado de la conversión, la tasa aplicada, y los códigos usados.
    """
    return convert_currency(amount, source, target)

@mcp.tool()
def tool_get_exchange_rates(base: str) -> dict:
    """Obtiene las tasas de cambio actuales para múltiples monedas basándose en una moneda de referencia.
    
    Llama a una API externa que devuelve los factores de conversión desde la moneda base hacia
    una lista extensa de divisas soportadas a nivel global.
    
    Args:
        base (str): Código ISO de 3 letras de la moneda base o de referencia (ej. 'USD').
        
    Returns:
        dict: Un diccionario donde las claves son los códigos de monedas y los valores las tasas respectivas respecto a la base.
    """
    return get_exchange_rates(base)

@mcp.tool()
def tool_geocode_city(city: str) -> dict:
    """Encuentra y devuelve las coordenadas geográficas aproximadas (latitud, longitud) de una ciudad.
    
    Busca por texto libre el nombre de una ciudad o localidad para obtener sus coordenadas necesarias
    para otras APIs basadas en ubicación (como clima o mapas), así como el país y la zona horaria asociada.
    
    Args:
        city (str): Nombre descriptivo de la ciudad a buscar. No debe estar vacío ni contener solo espacios en blanco.
        
    Returns:
        dict: Un diccionario con 'latitude' (latitud), 'longitude' (longitud), 'country' (país) y 'timezone' (zona horaria).
    """
    return geocode_city(city)

@mcp.tool()
def tool_get_current_weather(lat: float, lon: float) -> dict:
    """Obtiene las condiciones meteorológicas actuales para unas coordenadas geográficas concretas.
    
    Informa del estado del tiempo presente (temperatura superficial, humedad, viento, etc.) en
    la ubicación especificada por latitud y longitud, consultando la API de Open-Meteo.
    
    Args:
        lat (float): Latitud en grados decimales. Un valor comprendido entre -90.0 y 90.0.
        lon (float): Longitud en grados decimales. Un valor comprendido entre -180.0 y 180.0.
        
    Returns:
        dict: Un diccionario detallando el estado actual del tiempo (temperatura, velocidad del viento, código meteorológico, etc.).
    """
    return get_current_weather(lat, lon)

@mcp.tool()
def tool_get_weather_forecast(lat: float, lon: float) -> dict:
    """Obtiene el pronóstico del tiempo proyectado en varios días para unas coordenadas dadas.
    
    Retorna datos predictivos sobre la temperatura máxima y mínima diaria de los próximos días
    para ayudar en la planificación anticipada, ajustándose a la zona horaria local de origen automáticamente.
    
    Args:
        lat (float): Latitud en grados decimales. Debe estar entre -90.0 y 90.0.
        lon (float): Longitud en grados decimales. Debe estar entre -180.0 y 180.0.
        
    Returns:
        dict: Un diccionario conteniendo arrays por día ('time', 'temperature_2m_max', 'temperature_2m_min').
    """
    return get_weather_forecast(lat, lon)

def start_server():
    port = int(os.getenv("SERVER_PORT", "8000"))
    print(f"Iniciando FastMCP en puerto {port} con transporte SSE...")
    mcp.run(transport='sse', port=port)
