"""Client error-mapping tests (no live Binance HTTP)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from binance.exceptions import BinanceAPIException

from bot.client import (
    CLOCK_SYNC_MESSAGE,
    BinanceFuturesClient,
    TradingBotError,
)


def test_reraise_timestamp_sync_message(mocker) -> None:
    mocker.patch("binance.client.Client.ping")
    cli = BinanceFuturesClient(api_key="k", api_secret="s")
    resp = MagicMock()
    body = '{"code": -1021, "msg": "Timestamp outside recv window"}'
    exc = BinanceAPIException(resp, 400, body)

    with pytest.raises(TradingBotError) as err:
        cli._reraise(exc)  # noqa: SLF001

    assert err.value.binance_code == -1021
    assert CLOCK_SYNC_MESSAGE in str(err.value)


def test_reraise_generic_binance_maps_to_trading_bot_error(mocker) -> None:
    mocker.patch("binance.client.Client.ping")
    cli = BinanceFuturesClient(api_key="k", api_secret="s")
    resp = MagicMock()
    body = '{"code": -4140, "msg": "Precision error"}'
    exc = BinanceAPIException(resp, 400, body)

    with pytest.raises(TradingBotError) as err:
        cli._reraise(exc)  # noqa: SLF001

    assert err.value.binance_code == -4140
