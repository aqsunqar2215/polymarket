from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, start_http_server

orders_placed_counter = Counter(
    "pm_mm_orders_placed_total", "Total orders placed", ["side", "outcome"]
)
orders_filled_counter = Counter(
    "pm_mm_orders_filled_total", "Total orders filled", ["side", "outcome"]
)
orders_cancelled_counter = Counter(
    "pm_mm_orders_cancelled_total", "Total orders cancelled"
)
inventory_gauge = Gauge(
    "pm_mm_inventory", "Current inventory positions", ["type"]
)
exposure_gauge = Gauge("pm_mm_exposure_usd", "Current net exposure in USD")
spread_gauge = Gauge("pm_mm_spread_bps", "Current spread in basis points")
profit_gauge = Gauge("pm_mm_profit_usd", "Cumulative profit in USD")
quote_latency_histogram = Histogram(
    "pm_mm_quote_latency_ms",
    "Quote generation and placement latency in milliseconds",
    buckets=[10, 50, 100, 250, 500, 1000],
)


def start_metrics_server(host: str, port: int) -> None:
    start_http_server(port, addr=host)


def record_order_placed(side: str, outcome: str) -> None:
    orders_placed_counter.labels(side=side, outcome=outcome).inc()


def record_order_filled(side: str, outcome: str) -> None:
    orders_filled_counter.labels(side=side, outcome=outcome).inc()


def record_order_cancelled() -> None:
    orders_cancelled_counter.inc()


def record_inventory(inventory_type: str, value: float) -> None:
    inventory_gauge.labels(type=inventory_type).set(value)


def record_exposure(exposure_usd: float) -> None:
    exposure_gauge.set(exposure_usd)


def record_spread(spread_bps: float) -> None:
    spread_gauge.set(spread_bps)


def record_profit(profit_usd: float) -> None:
    profit_gauge.set(profit_usd)


def record_quote_latency(latency_ms: float) -> None:
    quote_latency_histogram.observe(latency_ms)

