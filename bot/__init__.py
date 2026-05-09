"""USDT-M futures testnet trading bot package."""

from bot.client import CLOCK_SYNC_MESSAGE, BinanceFuturesClient, TradingBotError
from bot.logging_config import setup_logging
from bot.orders import OrderResult, map_order_response, place_limit_order, place_market_order

__all__ = [
    "BinanceFuturesClient",
    "CLOCK_SYNC_MESSAGE",
    "OrderResult",
    "TradingBotError",
    "map_order_response",
    "place_limit_order",
    "place_market_order",
    "setup_logging",
]
