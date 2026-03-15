from .api_clients import fetch_exchange_rate

def convert_currency(amount: float, source: str, target: str) -> dict:
    """Convierte una cantidad de una moneda a otra.
    Args:
        amount: Cantidad a convertir
        source: Código de moneda origen (ej. USD)
        target: Código de moneda destino (ej. EUR)
    """
    if amount < 0:
        raise ValueError("La cantidad a convertir no puede ser negativa")
    if not isinstance(source, str) or len(source) != 3 or not source.isalpha():
        raise ValueError("El código de moneda origen debe tener exactamente 3 caracteres alfabéticos (ej. USD)")
    if not isinstance(target, str) or len(target) != 3 or not target.isalpha():
        raise ValueError("El código de moneda destino debe tener exactamente 3 caracteres alfabéticos (ej. EUR)")
    
    data = fetch_exchange_rate(source)
    rates = data.get("conversion_rates", {})
    if target.upper() not in rates:
        raise ValueError(f"Moneda destino {target} no soportada")
    rate = rates[target.upper()]
    return {"amount": amount * rate, "rate": rate, "source": source, "target": target}

def get_exchange_rates(base: str) -> dict:
    """Obtiene las tasas de cambio para múltiples monedas basadas en una moneda base.
    Args:
        base: Código de la moneda base (ej. USD)
    """
    if not isinstance(base, str) or len(base) != 3 or not base.isalpha():
        raise ValueError("El código de moneda base debe tener exactamente 3 caracteres alfabéticos (ej. USD)")
    return fetch_exchange_rate(base)
