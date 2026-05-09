"""Orders mapping tests (mock client, no Binance keys)."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from bot.orders import OrderResult, map_order_response, place_limit_order, place_market_order


def test_map_order_response_minimal() -> None:
    raw = {
        "orderId": 12345,
        "symbol": "BTCUSDT",
        "status": "NEW",
        "side": "BUY",
        "type": "LIMIT",
        "origQty": "0.010",
        "executedQty": "0",
        "price": "92000",
        "avgPrice": "0",
    }
    r = map_order_response(raw)
    assert r == OrderResult(
        order_id=12345,
        symbol="BTCUSDT",
        side="BUY",
        order_type="LIMIT",
        status="NEW",
        orig_qty="0.010",
        executed_qty="0",
        price="92000",
        avg_price="0",
    )


@pytest.fixture()
def dummy_client() -> MagicMock:
    mock = MagicMock()
    mock.create_futures_order.return_value = {
        "orderId": 1,
        "symbol": "ETHUSDT",
        "status": "FILLED",
        "side": "SELL",
        "type": "MARKET",
        "origQty": "2",
        "executedQty": "2",
        "price": "0",
        "avgPrice": "2500.5",
    }
    return mock


def test_place_market_order_formats_client_call(dummy_client: MagicMock) -> None:
    place_market_order(dummy_client, symbol="ETHUSDT", side="SELL", quantity=Decimal("2"))

    dummy_client.create_futures_order.assert_called_once()
    call_kw = dummy_client.create_futures_order.call_args.kwargs
    assert call_kw["symbol"] == "ETHUSDT"
    assert call_kw["side"] == "SELL"
    assert call_kw["type"] == "MARKET"


def test_place_limit_order(dummy_client: MagicMock) -> None:
    dummy_client.create_futures_order.return_value = {
        "orderId": 9,
        "symbol": "ETHUSDT",
        "status": "NEW",
        "side": "BUY",
        "type": "LIMIT",
        "origQty": "1",
        "executedQty": "0",
        "price": "2000",
        "avgPrice": "0",
    }

    place_limit_order(
        dummy_client,
        symbol="ETHUSDT",
        side="BUY",
        quantity=Decimal("1"),
        price=Decimal("2000"),
    )

    kwargs = dummy_client.create_futures_order.call_args.kwargs
    assert kwargs["timeInForce"] == "GTC"
    assert kwargs["price"] == "2000"
