"""Thin Binance futures testnet wrapper and TradingBotError."""

from __future__ import annotations

import logging
import os
from typing import Any, NoReturn, cast

import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException

LOGGER = logging.getLogger(__name__)

FUTURES_TESTNET_FAPI = "https://testnet.binancefuture.com/fapi"

CLOCK_SYNC_MESSAGE = (
    "System clock out of sync — check your local time settings (must be within 1000ms of server)."
)


class TradingBotError(Exception):
    """Application-level wrapper for Binance/network failures."""

    def __init__(
        self,
        message: str,
        *,
        binance_code: int | str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.binance_code = binance_code
        self.status_code = status_code

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.binance_code is not None:
            parts.append(f"(binance_code={self.binance_code})")
        if self.status_code is not None:
            parts.append(f"(http={self.status_code})")
        return " ".join(parts)


def _normalize_code(code: Any) -> int | str | None:
    if code is None:
        return None
    if isinstance(code, int):
        return code
    try:
        return int(str(code))
    except ValueError:
        return str(code)


class BinanceFuturesClient:
    """USDT-M futures testnet client with explicit FAPI base URL."""

    def __init__(self, api_key: str | None = None, api_secret: str | None = None) -> None:
        key = api_key or os.getenv("BINANCE_API_KEY", "")
        secret = api_secret or os.getenv("BINANCE_API_SECRET", "")
        self._client = Client(key, secret, testnet=True)

        self._client.FUTURES_URL = FUTURES_TESTNET_FAPI  # noqa: SLF001
        if hasattr(self._client, "FUTURES_API_URL"):
            self._client.FUTURES_API_URL = FUTURES_TESTNET_FAPI  # noqa: SLF001

        LOGGER.debug("Futures client configured for testnet FAPI base %s", FUTURES_TESTNET_FAPI)

    def create_futures_order(self, **params: Any) -> dict[str, Any]:
        try:
            raw = self._client.futures_create_order(**params)
            LOGGER.debug("futures_create_order response keys: %s", list(raw.keys()))
            return cast(dict[str, Any], raw)
        except BinanceAPIException as exc:
            self._reraise(exc)
        except requests.RequestException as exc:
            LOGGER.exception("Network failure during futures_create_order")
            raise TradingBotError(f"Network error: {exc}") from exc

    def get_futures_account(self) -> dict[str, Any]:
        try:
            return cast(dict[str, Any], self._client.futures_account())
        except BinanceAPIException as exc:
            self._reraise(exc)
        except requests.RequestException as exc:
            LOGGER.exception("Network failure during futures_account")
            raise TradingBotError(f"Network error: {exc}") from exc

    def futures_exchange_info(self) -> dict[str, Any]:
        """USDS-M futures `GET /fapi/v1/exchangeInfo` (python-binance: `futures_exchange_info`)."""

        try:
            return cast(dict[str, Any], self._client.futures_exchange_info())
        except BinanceAPIException as exc:
            self._reraise(exc)
        except requests.RequestException as exc:
            LOGGER.exception("Network failure during futures_exchange_info")
            raise TradingBotError(f"Network error: {exc}") from exc

    def get_symbol_filters(self, symbol: str) -> dict[str, str]:
        """
        LOT_SIZE / PRICE_FILTER metadata for validating qty and price ticks.
        """
        sym_upper = symbol.upper()
        payload = self.futures_exchange_info()
        for sym in payload.get("symbols", []):
            if sym.get("symbol") != sym_upper:
                continue
            out: dict[str, str] = {}
            for flt in sym.get("filters", []):
                ftype = flt.get("filterType")
                if ftype == "LOT_SIZE":
                    out["step_size"] = str(flt["stepSize"])
                    out["min_qty"] = str(flt["minQty"])
                elif ftype == "PRICE_FILTER":
                    out["tick_size"] = str(flt["tickSize"])
            if "step_size" not in out or "min_qty" not in out:
                raise TradingBotError(
                    f"Missing LOT_SIZE filter for {sym_upper}",
                    binance_code=None,
                )
            return out

        raise TradingBotError(f"Unknown symbol for exchangeInfo: {sym_upper}")

    def _reraise(self, exc: BinanceAPIException) -> NoReturn:
        LOGGER.warning(
            "BinanceAPIException code=%s message=%s",
            getattr(exc, "code", None),
            getattr(exc, "message", str(exc)),
        )
        norm = _normalize_code(getattr(exc, "code", None))
        if norm == -1021 or norm == "-1021":
            raise TradingBotError(
                CLOCK_SYNC_MESSAGE,
                binance_code=-1021,
                status_code=getattr(exc, "status_code", None),
            ) from exc
        msg = getattr(exc, "message", None) or str(exc)
        raise TradingBotError(
            msg,
            binance_code=norm if norm is not None else getattr(exc, "code", None),
            status_code=getattr(exc, "status_code", None),
        ) from exc
