# Polymarket Market Maker Bot

Production-grade **Polymarket CLOB market-making bot** with optimized inventory management, spread farming, intelligent cancel/replace cycles, and automated risk controls.  
Designed for professional market makers seeking balanced exposure, efficient quote placement, and maximum spread capture on Polymarket prediction markets.

<p>
  <a href="mailto:xsui46941@gmail.com">
    <img src="https://img.shields.io/badge/Email-xsui46941%40gmail.com-ef4444?style=flat&logo=gmail&logoColor=white" />
  </a>
  <a href="https://t.me/lorine93s">
    <img src="https://img.shields.io/badge/Telegram-@lorine93s-2AABEE?style=flat&logo=telegram&logoColor=white" />
  </a>
  <a href="https://twitter.com/kakamajo_btc">
    <img src="https://img.shields.io/badge/Twitter-@kakamajo__btc-1DA1F2?style=flat&logo=twitter&logoColor=white" />
  </a>
</p>

## What This Bot Does

The Polymarket Market Maker Bot provides:

- **Real-time market making** on Polymarket CLOB (Central Limit Order Book)
- **Balanced inventory management** with mirrored YES/NO exposure control
- **Intelligent quote placement** at top-of-book for maximum spread capture
- **Optimized cancel/replace cycles** tuned for 500ms taker delay
- **Passive order execution** to earn maker rebates and avoid crossing
- **Risk management** with exposure limits, position size caps, and inventory skew checks
- **Auto-redeem** for settled markets and profitable positions
- **Gas batching** to minimize on-chain transaction costs
- **Real-time orderbook tracking** via WebSocket for low-latency updates

## Core Features

### Inventory Balance & Exposure Control

- **Mirrored YES/NO positioning** – Maintains balanced exposure across both sides
- **Net exposure limits** – Configurable min/max exposure in USD
- **Inventory skew detection** – Automatically adjusts quote sizes when inventory becomes unbalanced
- **Automatic rebalancing** – Smart quote sizing to reduce runaway inventory
- **Target inventory balance** – Maintains desired net exposure level

### Spread Farming Efficiency

- **Top-of-book quoting** – Places orders at best bid/ask for maximum fill probability
- **Passive order execution** – All orders are maker orders to earn rebates
- **Queue positioning** – Optimized order placement for better queue position
- **Missed fill reduction** – Fast cancel/replace cycles to capture spread opportunities
- **Anti-crossing logic** – Prevents accidental taker orders

### Cancel/Replace Cadence

- **Low-latency refresh cycles** – Configurable quote refresh rate (default: 1000ms)
- **500ms taker delay optimization** – Timing logic tuned for Polymarket's 500ms delay
- **Batch cancellations** – Groups cancel requests to reduce API calls and gas costs
- **Stale order detection** – Automatically cancels orders exceeding lifetime threshold
- **Smooth quote transitions** – No gaps or overlaps during refresh cycles

### Market Discovery & Real-Time Updates

- **15m/1h window discovery** – Automatically discovers markets within discovery windows
- **WebSocket orderbook feeds** – Real-time L2 orderbook updates for instant quote adjustments
- **Trade feed monitoring** – Tracks fills and adjusts inventory automatically
- **Market info caching** – Efficient market metadata retrieval

### Risk Management

- **Exposure limits** – Hard caps on net exposure in USD
- **Position size limits** – Maximum single order size
- **Inventory skew limits** – Prevents excessive position concentration
- **Stop-loss protection** – Optional percentage-based stop-loss
- **Pre-trade validation** – All orders validated before placement

### Auto-Redeem & Gas Optimization

- **Automatic redemption** – Redeems settled positions above threshold
- **Gas batching** – Groups multiple operations to reduce gas costs
- **Configurable gas price** – Customizable gas price in Gwei
- **Efficient order lifecycle** – Minimizes on-chain operations

### Performance Monitoring

- **Prometheus metrics** – Real-time metrics for orders, inventory, exposure, and profit
- **Structured JSON logging** – Full audit trail of all operations
- **Fill rate tracking** – Monitors passive fill rates
- **Latency metrics** – Quote generation and placement latency tracking

## Technical Architecture

```
┌─────────────────────┐      ┌──────────────────────┐      ┌──────────────────┐
│ Polymarket CLOB API │      │ Market Maker Bot     │      │ Inventory Mgr    │
│ (REST + WebSocket)  │ <--> │ (Quote Engine)       │ <--> │ (Balance Ctrl)   │
└─────────────────────┘      └──────────────────────┘      └──────────────────┘
         │                           │                            │
         │                           v                            │
         │                  ┌──────────────────┐                 │
         │                  │ Order Executor   │                 │
         │                  │ (Cancel/Replace) │                 │
         │                  └──────────────────┘                 │
         │                           │                            │
         v                           v                            v
┌─────────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ WebSocket Feed      │      │ Risk Manager     │      │ Auto Redeem      │
│ (Orderbook/Trades)  │      │ (Validations)    │      │ (Settlements)    │
└─────────────────────┘      └──────────────────┘      └──────────────────┘
```

### Key Modules

- `src/config.py` – Pydantic settings for all bot parameters (exposure, spreads, timing, etc.)
- `src/polymarket/rest_client.py` – REST API client for market data, orders, balances
- `src/polymarket/websocket_client.py` – WebSocket client for real-time orderbook/trade feeds
- `src/polymarket/order_signer.py` – Ethereum order signing for authenticated requests
- `src/inventory/inventory_manager.py` – Inventory tracking and balanced exposure management
- `src/market_maker/quote_engine.py` – Quote generation with spread calculation and sizing
- `src/execution/order_executor.py` – Order placement, cancellation, and batching
- `src/risk/risk_manager.py` – Pre-trade validations and risk checks
- `src/services/auto_redeem.py` – Automatic position redemption for settled markets
- `src/main.py` – Main orchestrator for market-making loop and lifecycle

## Getting Started

### 1. Requirements

- Python **3.11+**
- **Ethereum private key** with funds on Polygon network
- **Polygon RPC endpoint** (public or private)
- Polymarket account with sufficient balance for trading
- Understanding of market-making risks and Polymarket mechanics

### 2. Installation

```bash
git clone https://github.com/your-org/polymarket-market-maker-bot.git
cd polymarket-market-maker-bot
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file:

```env
ENVIRONMENT=production
LOG_LEVEL=INFO

# Polymarket API
POLYMARKET_API_URL=https://clob.polymarket.com
POLYMARKET_WS_URL=wss://clob-ws.polymarket.com

# Authentication (REQUIRED)
PRIVATE_KEY=0x...
PUBLIC_ADDRESS=0x...

# Market Configuration
MARKET_ID=0x...

# Market Discovery
MARKET_DISCOVERY_ENABLED=true
DISCOVERY_WINDOW_MINUTES=15

# Quoting Parameters
DEFAULT_SIZE=100.0
MIN_SPREAD_BPS=10
QUOTE_STEP_BPS=5
OVERSIZE_THRESHOLD=1.5

# Inventory Management
MAX_EXPOSURE_USD=10000.0
MIN_EXPOSURE_USD=-10000.0
TARGET_INVENTORY_BALANCE=0.0
INVENTORY_SKEW_LIMIT=0.3

# Cancel/Replace Logic
CANCEL_REPLACE_INTERVAL_MS=500
TAKER_DELAY_MS=500
BATCH_CANCELLATIONS=true

# Risk Management
MAX_POSITION_SIZE_USD=5000.0
STOP_LOSS_PCT=10.0

# Auto-Redeem
AUTO_REDEEM_ENABLED=true
REDEEM_THRESHOLD_USD=1.0

# Gas Optimization
GAS_BATCHING_ENABLED=true
GAS_PRICE_GWEI=20.0

# Performance Tuning
QUOTE_REFRESH_RATE_MS=1000
ORDER_LIFETIME_MS=3000

# Metrics and Logging
METRICS_HOST=0.0.0.0
METRICS_PORT=9305

# Polygon RPC
RPC_URL=https://polygon-rpc.com
```

### 4. Run the Bot

```bash
python -m src.main
```

The bot will:
- Discover and connect to the specified Polymarket market
- Establish WebSocket connection for real-time orderbook updates
- Start the cancel/replace cycle with optimized quote placement
- Monitor inventory and adjust quotes for balanced exposure
- Execute auto-redeem for settled positions
- Log all operations and expose Prometheus metrics

### 5. Docker Deployment

```bash
docker compose up --build -d
```

View logs:
```bash
docker compose logs -f market-maker-bot
```

## Parameter Tuning Guide

### Inventory Balance

- **MAX_EXPOSURE_USD / MIN_EXPOSURE_USD**: Set based on your capital. Smaller values = tighter control.
- **INVENTORY_SKEW_LIMIT**: 0.3 = 30% max skew. Lower = more balanced but fewer opportunities.
- **TARGET_INVENTORY_BALANCE**: 0.0 for neutral, positive for bullish bias, negative for bearish.

### Spread Farming

- **MIN_SPREAD_BPS**: Minimum spread to quote (10 bps = 0.1%). Lower = more quotes but tighter spreads.
- **QUOTE_STEP_BPS**: Stepping between price levels (5 bps = 0.05%).
- **DEFAULT_SIZE**: Base order size in USD. Adjust based on market depth.

### Cancel/Replace Timing

- **CANCEL_REPLACE_INTERVAL_MS**: 500ms matches taker delay. Faster = more responsive but more API calls.
- **QUOTE_REFRESH_RATE_MS**: 1000ms for smooth quote updates. Lower = faster refresh but higher gas costs.
- **ORDER_LIFETIME_MS**: 3000ms before canceling stale orders. Adjust based on market conditions.

### Performance Optimization

- **BATCH_CANCELLATIONS**: `true` to group cancel requests and reduce gas costs.
- **GAS_BATCHING_ENABLED**: `true` to batch on-chain operations.
- **AUTO_REDEEM_ENABLED**: `true` to automatically redeem settled positions.

## Monitoring & Observability

### Prometheus Metrics

Access metrics at: `http://localhost:9305/metrics`

Key metrics:
- `pm_mm_orders_placed_total` – Total orders placed by side and outcome
- `pm_mm_orders_filled_total` – Total orders filled (passive fills)
- `pm_mm_inventory` – Current YES/NO inventory positions
- `pm_mm_exposure_usd` – Net exposure in USD
- `pm_mm_spread_bps` – Current spread in basis points
- `pm_mm_profit_usd` – Cumulative profit in USD
- `pm_mm_quote_latency_ms` – Quote generation and placement latency

### Structured Logging

All events logged as JSON:
- Order placement and cancellation events
- Inventory updates and rebalancing
- Risk check failures
- WebSocket connection status
- Auto-redeem operations

Example log:
```json
{
  "event": "quote_placed",
  "outcome": "YES",
  "side": "BUY",
  "price": "0.65",
  "size": "100.0",
  "order_id": "0x...",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Performance Benchmarks

Expected performance characteristics:

- **Quote refresh latency**: < 100ms
- **Cancel/replace cycle**: 500-1000ms
- **WebSocket latency**: < 50ms
- **Fill rate**: 60-80% passive (maker) fills
- **Inventory skew**: Maintained below 30%
- **Gas efficiency**: 30-50% reduction via batching

## SEO: Who Is This Bot For?

This project is designed for people searching for:

- **Polymarket market maker bot**
- **Polymarket trading bot**
- **Polymarket copy trading bot**
- **CLOB market making**
- **Polymarket automated trading**
- **Prediction market bot**
- **Polymarket liquidity provider**

Perfect for:

- **Professional market makers** seeking to provide liquidity on Polymarket
- **Traders** looking to automate spread capture and inventory management
- **Quantitative traders** who want optimized cancel/replace cycles
- **DeFi enthusiasts** interested in prediction market market-making

## Risk Management Best Practices

1. **Start Small**: Begin with low `DEFAULT_SIZE` and `MAX_EXPOSURE_USD` values
2. **Monitor Inventory**: Watch inventory skew and adjust limits as needed
3. **Set Exposure Limits**: Use conservative exposure limits to prevent runaway positions
4. **Test on Testnet**: Test thoroughly before deploying with real funds
5. **Monitor Gas Costs**: Gas batching helps, but monitor costs during high network activity
6. **Review Logs**: Regularly review logs for risk check failures and edge cases

## Common Issues & Troubleshooting

### Orders Not Filling

- **Check spread**: Increase `MIN_SPREAD_BPS` if spreads are too tight
- **Verify orderbook**: Ensure WebSocket connection is active
- **Review queue position**: Orders may be too far from best bid/ask

### High Inventory Skew

- **Reduce exposure limits**: Lower `MAX_EXPOSURE_USD` / `MIN_EXPOSURE_USD`
- **Adjust quote sizing**: Bot automatically reduces sizes when skewed
- **Enable rebalancing**: Check inventory skew limits are configured

### Excessive Gas Costs

- **Enable batching**: Set `BATCH_CANCELLATIONS=true` and `GAS_BATCHING_ENABLED=true`
- **Reduce refresh rate**: Increase `QUOTE_REFRESH_RATE_MS` to fewer updates
- **Monitor network**: Use private RPC during high gas periods

### WebSocket Disconnections

- **Automatic reconnection**: Bot automatically reconnects on disconnect
- **Check network**: Ensure stable network connection
- **Review logs**: Check for connection errors in logs

## Future Enhancements

- **Multi-market support**: Quote on multiple markets simultaneously
- **Advanced strategies**: Dynamic spread adjustment based on volatility
- **ML-based sizing**: Machine learning for optimal order sizing
- **Portfolio-level risk**: Cross-market exposure limits
- **Copy trading**: Replicate successful market maker strategies

## License

Use at your own risk. Market-making involves capital risk and requires understanding of prediction markets.  
Ensure compliance with local regulations and Polymarket terms of service before using in production.

## Safety & Compliance

- This bot executes real trades on Polymarket. Test thoroughly before deploying with real funds.
- Market-making involves inventory risk. Monitor exposure and inventory skew continuously.
- Gas costs can be significant during high network activity. Monitor and optimize accordingly.
- Review Polymarket's terms of service and ensure compliance with automated trading policies.
- Maintain audit logs and monitor all operations for compliance purposes.

