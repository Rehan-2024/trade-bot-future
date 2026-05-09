#!/usr/bin/env python3
"""Binance USDT-M Futures Testnet CLI (Typer + Rich)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from bot.client import BinanceFuturesClient, TradingBotError
from bot.logging_config import setup_logging
from bot.orders import OrderResult, place_limit_order, place_market_order
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

app = typer.Typer(help="USDT-M futures testnet order CLI.", no_args_is_help=True)
console = Console()


@app.callback()
def _global_init() -> None:
    """Load `.env` and attach logging handlers before each subcommand."""

    load_dotenv(Path(__file__).resolve().parent / ".env")
    load_dotenv()
    setup_logging()


def _fail_validation(message: str) -> None:
    console.print(Panel.fit(f"[bold red]Validation[/bold red]\n{message}", border_style="red"))
    raise typer.Exit(code=1)


def _fail_api(exc: TradingBotError) -> None:
    hint = ""
    if exc.binance_code == -1021:
        hint = (
            "\n[System clock drift — synchronize time (must be within ~1000ms of Binance server)]"
        )
    console.print(
        Panel.fit(
            f"[bold red]API / Network[/bold red]\n{exc}{hint}",
            border_style="red",
        )
    )
    raise typer.Exit(code=2)


def _qty_price_display_strings(qty_dec: Decimal, px_dec: Decimal | None) -> tuple[str, str | None]:
    """Human-friendly qty/price strings (matches interactive formatting)."""

    qty_display = format(qty_dec, "f").rstrip("0").rstrip(".") or "0"
    price_display = format(px_dec, "f").rstrip("0").rstrip(".") if px_dec is not None else None
    return qty_display, price_display


def _render_order_preview(
    symbol: str,
    side: str,
    order_type: str,
    qty_display: str,
    price_display: str | None,
    *,
    title: str = "Order preview (testnet)",
) -> None:
    tbl = Table(title=title, show_header=False)
    tbl.add_column("Field", style="cyan")
    tbl.add_column("Value")
    tbl.add_row("Symbol", symbol)
    tbl.add_row("Side", side)
    tbl.add_row("Type", order_type)
    tbl.add_row("Quantity", qty_display)
    tbl.add_row("Price", price_display or "—")
    console.print(tbl)


def _maybe_apply_exchange_filters(
    api: BinanceFuturesClient,
    symbol: str,
    qty: Decimal,
    price: Decimal | None,
) -> None:
    try:
        meta = api.get_symbol_filters(symbol)
        validate_qty_step(qty, meta["step_size"], meta["min_qty"])
        if price is not None and meta.get("tick_size"):
            validate_price_tick(price, meta["tick_size"])
    except ValueError as ve:
        _fail_validation(str(ve))
    except TradingBotError as exc:
        console.print(
            "[yellow]Warning: skipped exchange filter enforcement "
            f"({exc}). Precision errors may surface at Binance.[/yellow]"
        )


def _render_success(result: OrderResult) -> None:
    tbl = Table(title="Order result", header_style="bold green")
    tbl.add_column("Field")
    tbl.add_column("Value")
    tbl.add_row("Order ID", str(result.order_id))
    tbl.add_row("Symbol", result.symbol)
    tbl.add_row("Side", result.side)
    tbl.add_row("Type", result.order_type)
    tbl.add_row("Status", result.status)
    tbl.add_row("Orig qty", result.orig_qty)
    tbl.add_row("Executed qty", result.executed_qty)
    tbl.add_row("Price", result.price or "—")
    tbl.add_row("Avg price", result.avg_price or "—")
    console.print(tbl)


@app.command()
def place(
    symbol: str = typer.Option(..., help="Symbol, e.g. BTCUSDT"),
    side: str = typer.Option(..., help="BUY or SELL"),
    order_type: str = typer.Option("MARKET", "--type", help="MARKET or LIMIT"),
    qty: str = typer.Option(..., help="Order quantity"),
    price: str | None = typer.Option(None, help="Limit price (required for LIMIT)"),
) -> None:
    """Place market/limit: print request summary, submit (no confirmation prompt)."""

    try:
        sym = validate_symbol(symbol)
        sde = validate_side(side)
        oty = validate_order_type(order_type)
        validate_market_vs_limit_combo(oty, price)
        qty_dec = validate_quantity(qty)
        px_dec: Decimal | None = validate_limit_price(price) if oty == "LIMIT" else None
    except ValueError as exc:
        _fail_validation(str(exc))

    qty_display, price_display = _qty_price_display_strings(qty_dec, px_dec)
    _render_order_preview(
        sym,
        sde,
        oty,
        qty_display,
        price_display,
        title="Order request summary (testnet)",
    )

    api = BinanceFuturesClient()
    _maybe_apply_exchange_filters(api, sym, qty_dec, px_dec)

    try:
        if oty == "MARKET":
            result = place_market_order(api, symbol=sym, side=sde, quantity=qty_dec)
        else:
            assert px_dec is not None
            result = place_limit_order(api, symbol=sym, side=sde, quantity=qty_dec, price=px_dec)
    except TradingBotError as exc:
        _fail_api(exc)

    _render_success(result)


def _prompt_symbol() -> str:
    while True:
        raw = Prompt.ask("Symbol (e.g. BTCUSDT)")
        try:
            return validate_symbol(raw)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")


def _prompt_side() -> str:
    while True:
        raw = Prompt.ask("Side (BUY / SELL)")
        try:
            return validate_side(raw)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")


def _prompt_order_type() -> str:
    while True:
        raw = Prompt.ask("Order type (MARKET / LIMIT)")
        try:
            return validate_order_type(raw)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")


def _prompt_qty() -> Decimal:
    while True:
        raw = Prompt.ask("Quantity")
        try:
            return validate_quantity(raw)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")


def _prompt_limit_price() -> Decimal:
    while True:
        raw = Prompt.ask("Limit price")
        try:
            return validate_limit_price(raw)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")


@app.command()
def interactive() -> None:
    """Wizard with per-field retries and Rich confirmation before placing."""

    console.print("[bold]Interactive order wizard (testnet)[/bold]")

    sym = _prompt_symbol()
    sde = _prompt_side()
    oty = _prompt_order_type()
    qty_dec = _prompt_qty()
    px_dec: Decimal | None = _prompt_limit_price() if oty == "LIMIT" else None

    limit_price_hint: str | None = str(px_dec) if oty == "LIMIT" else None

    try:
        validate_market_vs_limit_combo(oty, limit_price_hint)
    except ValueError as exc:
        _fail_validation(str(exc))

    qty_display, price_display = _qty_price_display_strings(qty_dec, px_dec)

    _render_order_preview(sym, sde, oty, qty_display, price_display)

    if not Confirm.ask("Confirm and place?", default=False):
        console.print("Cancelled.")
        raise typer.Exit(code=0)

    api = BinanceFuturesClient()
    _maybe_apply_exchange_filters(api, sym, qty_dec, px_dec)

    try:
        if oty == "MARKET":
            result = place_market_order(api, symbol=sym, side=sde, quantity=qty_dec)
        else:
            assert px_dec is not None
            result = place_limit_order(api, symbol=sym, side=sde, quantity=qty_dec, price=px_dec)
    except TradingBotError as exc:
        _fail_api(exc)

    _render_success(result)


@app.command("account")
def account_cmd() -> None:
    """Show futures assets with non-zero wallet balance (testnet)."""

    api = BinanceFuturesClient()
    try:
        acct = api.get_futures_account()
    except TradingBotError as exc:
        _fail_api(exc)

    assets = []
    for row in acct.get("assets", []):
        wb = float(row.get("walletBalance") or 0)
        if wb != 0.0:
            assets.append(row)

    tbl = Table(title="Futures account snapshot (testnet)")
    tbl.add_column("Asset")
    tbl.add_column("Wallet balance")

    if not assets:
        tbl.add_row("(no non-zero balances)", "")
    else:
        for asset in sorted(assets, key=lambda a: str(a.get("asset", ""))):
            tbl.add_row(str(asset.get("asset")), str(asset.get("walletBalance")))
    console.print(tbl)


if __name__ == "__main__":
    app()
