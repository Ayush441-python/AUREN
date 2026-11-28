"""Regresión de #389: una caché local vacía o ilegible no puede tumbar el fallback.

El contrato de `_cached` es devolver un DataFrame (posiblemente vacío). Cualquier
cosa que deje el archivo inservible —cero bytes tras una escritura interrumpida,
una copia manual a medias, un CSV truncado— tiene que terminar en el mismo sitio:
un DataFrame vacío, nunca una excepción de pandas que se escape hacia `_load`.
"""

import pandas as pd
import pytest

from engine.data import _cached, _load


def test_empty_csv_returns_an_empty_frame(tmp_path):
    empty = tmp_path / "prices.csv"
    empty.write_text("", encoding="utf-8")

    df = _cached(empty, ["NVDA"])

    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert list(df.columns) == []


def test_missing_file_still_returns_an_empty_frame(tmp_path):
    df = _cached(tmp_path / "does-not-exist.csv", ["NVDA"])

    assert df.empty


def test_truncated_csv_returns_an_empty_frame(tmp_path):
    # Una fila con menos campos de los que pide la cabecera: ParserError.
    truncated = tmp_path / "prices.csv"
    truncated.write_text("Date,NVDA,MSFT\n2026-01-02\n", encoding="utf-8")

    df = _cached(truncated, ["NVDA"])

    assert df.empty


def test_undecodable_bytes_return_an_empty_frame(tmp_path):
    broken = tmp_path / "prices.csv"
    broken.write_bytes(b"\xff\xfe\x00\x00binary,not,a,csv\n\x81\x82")

    df = _cached(broken, ["NVDA"])

    assert df.empty


def test_load_falls_back_to_an_empty_frame_instead_of_raising(tmp_path, monkeypatch):
    # Sin red (download devuelve None) y con una caché vacía, `_load` tiene que
    # devolver un DataFrame vacío: es el camino que el issue reporta como crash.
    monkeypatch.setattr("engine.data._download", lambda *args, **kwargs: None)
    empty = tmp_path / "prices.csv"
    empty.write_text("", encoding="utf-8")

    df = _load("Close", ["NVDA"], "2y", empty)

    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_a_readable_cache_is_still_used(tmp_path):
    good = tmp_path / "prices.csv"
    good.write_text("Date,NVDA,MSFT\n2026-01-02,100,200\n2026-01-05,101,201\n", encoding="utf-8")

    df = _cached(good, ["NVDA"])

    assert list(df.columns) == ["NVDA"]
    assert len(df) == 2
