"""Order orchestration and OrderResult mapping (trusts CLI-validated inputs)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol

LOGGER = logging.getLogger(__name__)


class OrderClientProto(Protocol):
    def create_futures_order(self, **params: Any) -> dict[str, Any]: ...


@dataclass(frozen=True)
class OrderResult:
    order_id: int | None
    symbol: str
    side: str
    order_type: str
    status: str
    orig_qty: str
    executed_qty: str
    price: str
    avg_price: str


def map_order_response(raw: dict[str, Any]) -> OrderResult:
    def _pick(*keys: str, default: str = "") -> str:
        for k in keys:
            val = raw.get(k)
            if val is None:
                continue
            return str(val)
        return default

    order_id_raw = raw.get("orderId")
    order_id: int | None
    try:
        order_id = int(order_id_raw) if order_id_raw is not None else None
    except (TypeError, ValueError):
        order_id = None

    LOGGER.debug(
        "Mapped order snapshot: symbol=%s side=%s status=%s orderId=%s",
        raw.get("symbol"),
        raw.get("side"),
        raw.get("status"),
        order_id,
    )

    return OrderResult(
        order_id=order_id,
        symbol=str(raw.get("symbol", "")),
        side=str(raw.get("side", "")),
        order_type=str(raw.get("type", raw.get("orderType", ""))),
        status=str(raw.get("status", "")),
        orig_qty=_pick("origQty", "quantity"),
        executed_qty=_pick("executedQty"),
        price=_pick("price"),
        avg_price=_pick("avgPrice", "avg_price"),
    )


def place_market_order(
    client: OrderClientProto,
    *,
    symbol: str,
    side: str,
    quantity: Decimal | str,
) -> OrderResult:
    qty_str = format_decimal_for_order(quantity)
    params = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": qty_str,
    }
    LOGGER.debug("place_market_order params (sanitized): %s", {**params})
    raw = client.create_futures_order(**params)
    return map_order_response(raw)


def place_limit_order(
    client: OrderClientProto,
    *,
    symbol: str,
    side: str,
    quantity: Decimal | str,
    price: Decimal | str,
) -> OrderResult:
    qty_str = format_decimal_for_order(quantity)
    px_str = format_decimal_for_order(price)
    params = {
        "symbol": symbol,
        "side": side,
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": qty_str,
        "price": px_str,
    }
    LOGGER.debug("place_limit_order params (sanitized): %s", {**params})
    raw = client.create_futures_order(**params)
    return map_order_response(raw)


def format_decimal_for_order(val: Decimal | str) -> str:
    """Strip trailing zeros for cleaner API payloads while preserving precision."""

    dec = Decimal(str(val))
    s = format(dec.normalize(), "f")
    return s.rstrip("0").rstrip(".") if "." in s else s
