from .api_clients import fetch_geocode

def geocode_city(city: str) -> dict:
    """Obtiene coordenadas (latitud/longitud), país y zona horaria de una ciudad.
    Args:
        city: Nombre de la ciudad a buscar
    """
    if not city or not str(city).strip():
        raise ValueError("El nombre de la ciudad no puede estar vacío")
    
    result = fetch_geocode(city)
    return {
        "latitude": result["latitude"],
        "longitude": result["longitude"],
        "country": result.get("country", ""),
        "timezone": result.get("timezone", "")
    }
