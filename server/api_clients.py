import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError, RequestException
from config.settings import EXCHANGERATE_API_KEY
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _handle_request_errors(func):
    """Decorador para manejar errores comunes de red usando la librería requests."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Timeout as e:
            logger.error(f"Error de timeout: {e}")
            raise RuntimeError(f"Tiempo de espera agotado al conectar con el servicio: {str(e)}")
        except ConnectionError as e:
            logger.error(f"Error de conexión: {e}")
            raise RuntimeError(f"Error de conexión de red. Verifica tu conexión a internet: {str(e)}")
        except HTTPError as e:
            logger.error(f"Error HTTP: {e}")
            status_code = e.response.status_code if e.response is not None else "Desconocido"
            raise RuntimeError(f"El servicio respondió con un error HTTP {status_code}: {str(e)}")
        except RequestException as e:
            logger.error(f"Error general de requests: {e}")
            raise RuntimeError(f"Ocurrió un error inesperado al realizar la solicitud de red: {str(e)}")
    return wrapper

@_handle_request_errors
def fetch_exchange_rate(base: str) -> dict:
    if not EXCHANGERATE_API_KEY:
        raise ValueError("Falta EXCHANGERATE_API_KEY")
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/latest/{base.upper()}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()

@_handle_request_errors
def fetch_geocode(city: str) -> dict:
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=es&format=json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    if not data.get("results"):
        raise ValueError(f"No se encontró la ciudad: {city}")
    return data["results"][0]

@_handle_request_errors
def fetch_weather(lat: float, lon: float) -> dict:
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()

@_handle_request_errors
def fetch_weather_forecast(lat: float, lon: float) -> dict:
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
