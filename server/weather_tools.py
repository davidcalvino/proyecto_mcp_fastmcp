from .api_clients import fetch_weather, fetch_weather_forecast

def _validate_coordinates(lat: float, lon: float):
    if not (-90.0 <= float(lat) <= 90.0):
        raise ValueError("La latitud debe estar comprendida entre -90 y 90 grados")
    if not (-180.0 <= float(lon) <= 180.0):
        raise ValueError("La longitud debe estar comprendida entre -180 y 180 grados")

def get_current_weather(lat: float, lon: float) -> dict:
    """Obtiene el clima actual para unas coordenadas dadas.
    Args:
        lat: Latitud
        lon: Longitud
    """
    _validate_coordinates(lat, lon)
    result = fetch_weather(lat, lon)
    return result.get("current_weather", {})

def get_weather_forecast(lat: float, lon: float) -> dict:
    """Obtiene el pronóstico del tiempo de varios días para unas coordenadas.
    Args:
        lat: Latitud
        lon: Longitud
    """
    _validate_coordinates(lat, lon)
    result = fetch_weather_forecast(lat, lon)
    return result.get("daily", {})
