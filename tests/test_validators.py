"""Unit tests for bot.validators (no network)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from bot.validators import (
    validate_limit_price,
    validate_market_vs_limit_combo,
    validate_order_type,
    validate_price_tick,
    validate_qty_step,
    validate_quantity,
    validate_side,
    validate_symbol,
)


def test_validate_symbol_ok() -> None:
    assert validate_symbol(" btcusdt ") == "BTCUSDT"


def test_validate_symbol_rejects_noise() -> None:
    with pytest.raises(ValueError):
        validate_symbol("BTC-USDT")


def test_validate_side_ok() -> None:
    assert validate_side("buy") == "BUY"


def test_validate_side_bad() -> None:
    with pytest.raises(ValueError):
        validate_side("LONG")


def test_validate_order_type() -> None:
    assert validate_order_type("limit") == "LIMIT"


def test_validate_quantity_decimal() -> None:
    q = validate_quantity("0.001")
    assert q == Decimal("0.001")


def test_validate_quantity_rejects_negative() -> None:
    with pytest.raises(ValueError):
        validate_quantity("-1")


def test_validate_limit_price_requires_positive() -> None:
    with pytest.raises(ValueError):
        validate_limit_price("0")


def test_market_rejects_extraneous_price() -> None:
    with pytest.raises(ValueError):
        validate_market_vs_limit_combo("MARKET", "3400")


def test_limit_requires_price() -> None:
    with pytest.raises(ValueError):
        validate_market_vs_limit_combo("LIMIT", None)


def test_limit_accepts_price() -> None:
    validate_market_vs_limit_combo("LIMIT", "3400")


def test_qty_step_must_match() -> None:
    validate_qty_step(Decimal("0.01"), step_size_str="0.01", min_qty_str="0.001")
    with pytest.raises(ValueError):
        validate_qty_step(Decimal("0.015"), step_size_str="0.01", min_qty_str="0.001")


def test_price_tick() -> None:
    validate_price_tick(Decimal("100.50"), tick_str="0.01")
    with pytest.raises(ValueError):
        validate_price_tick(Decimal("100.501"), tick_str="0.01")
