"""Input validation invoked only from cli.py."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Final

_SYM_RE: Final[str] = r"^[A-Z0-9]{6,}$"

ALLOWED_SIDES = frozenset({"BUY", "SELL"})
ALLOWED_ORDER_TYPES = frozenset({"MARKET", "LIMIT"})


def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper()


def validate_symbol(symbol: str) -> str:
    s = normalize_symbol(symbol)
    if not re.match(_SYM_RE, s):
        raise ValueError(
            "Symbol must be alphanumeric uppercase futures pair "
            "(e.g. BTCUSDT), minimum length conventions apply."
        )
    return s


def validate_side(side: str) -> str:
    s = side.strip().upper()
    if s not in ALLOWED_SIDES:
        raise ValueError("Side must be BUY or SELL.")
    return s


def validate_order_type(order_type: str) -> str:
    o = order_type.strip().upper()
    if o not in ALLOWED_ORDER_TYPES:
        raise ValueError("Order type must be MARKET or LIMIT.")
    return o


def validate_quantity(quantity: str) -> Decimal:
    q = quantity.strip()
    try:
        dec = Decimal(q)
    except InvalidOperation as exc:
        raise ValueError("Quantity must be a positive decimal.") from exc
    if dec <= 0:
        raise ValueError("Quantity must be positive.")
    return dec


def validate_limit_price(price: str) -> Decimal:
    p = price.strip()
    try:
        dec = Decimal(p)
    except InvalidOperation as exc:
        raise ValueError("Price must be a positive decimal.") from exc
    if dec <= 0:
        raise ValueError("Limit price must be positive.")
    return dec


def validate_market_vs_limit_combo(order_type: str, price_provided: str | None) -> None:
    o = validate_order_type(order_type)
    if o == "MARKET" and price_provided:
        stripped = price_provided.strip()
        if stripped:
            raise ValueError("Price must not be set for MARKET orders.")
    if o == "LIMIT" and not price_provided:
        raise ValueError("LIMIT orders require --price.")
    if o == "LIMIT" and price_provided:
        stripped = price_provided.strip()
        if not stripped:
            raise ValueError("LIMIT orders require --price.")


def validate_qty_step(qty_dec: Decimal, step_size_str: str, min_qty_str: str) -> None:
    """Align qty to LOT_SIZE filters (pure; metadata from exchangeInfo via CLI)."""

    step = Decimal(step_size_str)
    min_qty = Decimal(min_qty_str)

    if qty_dec < min_qty:
        raise ValueError(f"Quantity below exchange minimum ({min_qty}).")

    if step <= 0:
        return

    remainder = qty_dec % step
    if remainder != 0:
        raise ValueError(f"Quantity must be a multiple of step size ({step}).")


def validate_price_tick(price_dec: Decimal, tick_str: str) -> None:
    tick = Decimal(tick_str)
    if tick <= 0:
        return
    multiples = price_dec / tick
    if multiples != multiples.to_integral_exact():
        raise ValueError(f"Price must align with tick size ({tick}).")
