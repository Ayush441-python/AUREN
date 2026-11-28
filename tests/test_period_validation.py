"""#405: un periodo con cero delante no puede colarse como "la caché de dos años".

El patrón anterior aceptaba `01y`, `0y`, `00y`, `0mo` y `02mo`. El proveedor
devuelve vacío para todos ellos, así que `engine/data.py` caía en la caché
empaquetada y el llamante recibía 730 sesiones con HTTP 200, sin ningún campo que
dijera que la ventana se había sustituido. En producción, `period=1y` daba 251
sesiones y `period=01y` daba 730 con la misma petición por lo demás.

El arreglo vive en el esquema, que es donde se puede rechazar con un mensaje.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.main import app
from backend.app.schemas.requests import PERIOD_PATTERN, PortfolioRequest
import re

PATTERN = re.compile(PERIOD_PATTERN)
client = TestClient(app)

VALID = ["ytd", "max", "1y", "2y", "5y", "10y", "99y", "1mo", "3mo", "6mo", "12mo", "99mo"]
INVALID = ["0y", "00y", "01y", "02y", "0mo", "00mo", "01mo", "02mo", "0", "000", "1w", "1d",
           "y", "mo", "", " 1y", "1y ", "1Y", "1MO", "-1y", "1.5y", "100y", "1yy"]


@pytest.mark.parametrize("period", VALID)
def test_the_periods_the_provider_understands_are_accepted(period):
    assert PATTERN.match(period), period
    assert PortfolioRequest(weights={"AAPL": 100}, period=period).period == period


@pytest.mark.parametrize("period", INVALID)
def test_zero_padded_and_unknown_periods_are_rejected(period):
    assert not PATTERN.match(period), period
    with pytest.raises(ValidationError):
        PortfolioRequest(weights={"AAPL": 100}, period=period)


def test_the_endpoint_answers_422_instead_of_serving_the_two_year_cache():
    # Sin red: el esquema rechaza antes de tocar el proveedor.
    response = client.post("/risk", json={"weights": {"AAPL": 100}, "period": "01y"})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail[0]["loc"][-1] == "period"


def test_a_valid_period_still_reaches_the_endpoint():
    # 422 solo por el periodo; cualquier otro desenlace significa que pasó el esquema.
    response = client.post("/risk", json={"weights": {"AAPL": 100}, "period": "1y"})

    assert response.status_code != 422


def test_the_error_names_the_offending_field_and_the_accepted_shape():
    # Pydantic pone el patrón, no la descripción: el mensaje tiene que mostrar al
    # menos los literales aceptados y el valor que se rechazó.
    with pytest.raises(ValidationError) as excinfo:
        PortfolioRequest(weights={"AAPL": 100}, period="0y")

    message = str(excinfo.value)
    assert "period" in message
    assert "ytd" in message  # el patrón nombra los literales que sí valen
    assert "0y" in message  # y el valor rechazado, para que se vea qué se envió


def test_the_openapi_schema_publishes_the_stricter_pattern():
    schema = client.get("/openapi.json").json()
    period = schema["components"]["schemas"]["PortfolioRequest"]["properties"]["period"]

    assert period["pattern"] == PERIOD_PATTERN
    assert "zero-padded" in period["description"]
