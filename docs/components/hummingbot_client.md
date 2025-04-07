# Hummingbot API Integration

## Overview

The Hummingbot API Integration component provides a seamless interface for connecting to and interacting with the Hummingbot trading engine. It enables the Liquid Energy trading system to execute trades, monitor markets, and manage accounts across multiple exchanges through a unified WebSocket-based API.

## Purpose and Functionality

This component serves as the bridge between the Liquid Energy trading strategies and the Hummingbot execution engine, enabling:

- Real-time market data streaming
- Order creation, cancellation, and monitoring
- Account balance and position management
- Event-driven architecture integration

## Architecture

The Hummingbot client integrates with the core event system to propagate market data, order updates, and trading signals throughout the application. It communicates with Hummingbot's WebSocket API for bidirectional real-time data exchange.

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│                 │       │                 │       │                 │
│ Trading         │       │ Hummingbot      │       │ Exchanges       │
│ Strategies      │◄─────►│ Client          │◄─────►│ (via Hummingbot)│
│                 │       │                 │       │                 │
└────────┬────────┘       └────────┬────────┘       └─────────────────┘
         │                         │
         │                         │
         ▼                         ▼
┌─────────────────────────────────────────────┐
│                                             │
│           Event-Driven Architecture         │
│                                             │
└─────────────────────────────────────────────┘
```

## Key Components

### Class Structure

1. **HummingbotClient**: Main client interface
2. **Supporting Enumerations**:
   - OrderType (LIMIT, MARKET)
   - OrderSide (BUY, SELL)
   - OrderStatus (OPEN, PARTIALLY_FILLED, FILLED, CANCELLED, FAILED)
   - MarketType (SPOT, FUTURES)
   - ConnectionStatus (DISCONNECTED, CONNECTING, CONNECTED, ERROR)
3. **Exception Classes**:
   - HummingbotClientException

## API Reference

### Initialization

```python
from liquid_energy.core import HummingbotClient, EventEngine

# Initialize the client
client = HummingbotClient(
    event_engine=event_engine,  # EventEngine instance
    api_host="localhost",       # Hummingbot API host
    api_port=15888,             # Hummingbot API port
    api_key="your_api_key",     # API key for authentication
    request_timeout=5.0,        # Optional: Timeout for requests (seconds)
    retry_attempts=3            # Optional: Number of retry attempts
)
```

### Connection Management

```python
# Connect to Hummingbot
await client.connect()

# Disconnect when done
await client.disconnect()
```

### Order Management

#### Creating Orders

```python
from liquid_energy.core import OrderType, OrderSide

# Create a limit order
limit_order = await client.create_order(
    exchange="binance",
    market="ETH-USD",
    side=OrderSide.BUY,
    order_type=OrderType.LIMIT,
    price=3000.0,
    amount=1.0
)

# Create a market order
market_order = await client.create_order(
    exchange="binance",
    market="ETH-USD",
    side=OrderSide.SELL,
    order_type=OrderType.MARKET,
    amount=1.0
)
```

#### Managing Orders

```python
# Cancel an order
cancel_result = await client.cancel_order(
    exchange="binance",
    market="ETH-USD",
    order_id="order_id_here"
)

# Check order status
order_status = await client.get_order_status(
    exchange="binance",
    market="ETH-USD",
    order_id="order_id_here"
)

# Get all open orders
open_orders = await client.get_open_orders(
    exchange="binance",
    market="ETH-USD"
)

# Get order history
order_history = await client.get_order_history(
    exchange="binance",
    market="ETH-USD",
    limit=50
)
```

### Market Data

```python
# Get order book data
order_book = await client.get_order_book(
    exchange="binance",
    market="ETH-USD",
    depth=10
)

# Get ticker information
ticker = await client.get_ticker(
    exchange="binance",
    market="ETH-USD"
)

# Subscribe to real-time order book updates
subscription = await client.subscribe_to_order_book(
    exchange="binance",
    market="ETH-USD"
)

# Subscribe to trade updates
subscription = await client.subscribe_to_trades(
    exchange="binance",
    market="ETH-USD"
)
```

### Account Information

```python
# Get account balances
balances = await client.get_balances(
    exchange="binance"
)
```

## Event Handling

The Hummingbot client automatically converts native Hummingbot events into Liquid Energy system events and publishes them to the event engine.

### Event Mapping

| Hummingbot Event Type | Liquid Energy Event Type | Description |
|-----------------------|---------------------------|-------------|
| `order_update` | `EventType.ORDER_UPDATE` | Order status changes |
| `trade` | `EventType.TRADE_UPDATE` | Completed trades |
| `order_book_update` | `EventType.MARKET_DATA` | Order book changes |
| `ticker_update` | `EventType.MARKET_DATA` | Ticker updates |
| `error` | `EventType.ERROR` | Error events |
| `info` | `EventType.INFO` | Informational events |

### Subscribing to Events

```python
from liquid_energy.core import EventListener, EventType, Event

class OrderUpdateListener(EventListener):
    def __init__(self, name):
        super().__init__(name, [EventType.ORDER_UPDATE])
    
    def handle_event(self, event: Event):
        order_id = event.data.get("order_id")
        status = event.data.get("status")
        print(f"Order {order_id} status: {status}")

# Register the listener with the event engine
listener = OrderUpdateListener("my_order_listener")
event_engine.register_listener(listener)
```

## Error Handling

### Exception Types

The client throws `HummingbotClientException` for various error conditions:

```python
try:
    await client.create_order(
        exchange="binance",
        market="ETH-USD",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        price=3000.0,
        amount=1.0
    )
except HummingbotClientException as e:
    if "Insufficient funds" in str(e):
        print("Not enough balance to place order")
    elif "Invalid order" in str(e):
        print("Order parameters are invalid")
    else:
        print(f"Order failed: {e}")
```

### Error Events

The client also dispatches `EventType.ERROR` events to the event engine:

```python
class ErrorListener(EventListener):
    def __init__(self, name):
        super().__init__(name, [EventType.ERROR])
    
    def handle_event(self, event: Event):
        print(f"Error occurred: {event.data.get('message')}")
        print(f"Source: {event.source}")

# Register the error listener
error_listener = ErrorListener("error_handler")
event_engine.register_listener(error_listener)
```

## Performance Considerations

### Connection Management

- The client maintains a single persistent WebSocket connection
- Connection failures are handled with appropriate error reporting
- Long-running connections should be monitored for health

### Concurrent Operations

- Multiple requests can be sent concurrently over the same connection
- The client manages request/response matching using message IDs
- Request timeouts prevent operations from hanging indefinitely

### Event Processing

- Events are processed asynchronously in the background
- The event loop should not be blocked by long-running handlers
- Consider using separate threads/processes for CPU-intensive event handlers

## Integration With Other Components

### Market Making Strategies

The Hummingbot client provides the execution layer for market making strategies:

```python
class SimpleMarketMaker:
    def __init__(self, client: HummingbotClient, event_engine: EventEngine):
        self.client = client
        self.event_engine = event_engine
        
    async def create_market(self, exchange, symbol, spread=0.01, amount=1.0):
        # Get current market data
        ticker = await self.client.get_ticker(exchange, symbol)
        mid_price = (float(ticker["bid"]) + float(ticker["ask"])) / 2
        
        # Create bid and ask orders
        bid_price = mid_price * (1 - spread)
        ask_price = mid_price * (1 + spread)
        
        await self.client.create_order(
            exchange=exchange,
            market=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=bid_price,
            amount=amount
        )
        
        await self.client.create_order(
            exchange=exchange,
            market=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=ask_price,
            amount=amount
        )
```

### Risk Management

```python
class RiskManager(EventListener):
    def __init__(self, name, client, max_position=10.0):
        super().__init__(name, [EventType.ORDER_UPDATE, EventType.TRADE_UPDATE])
        self.client = client
        self.max_position = max_position
        self.current_position = 0.0
        
    async def update_position(self, exchange):
        balances = await self.client.get_balances(exchange)
        # Update current position based on balances
        
    def handle_event(self, event: Event):
        if event.type == EventType.TRADE_UPDATE:
            # Update position based on trade
            amount = float(event.data.get("amount", 0))
            side = event.data.get("side")
            
            if side == "buy":
                self.current_position += amount
            else:
                self.current_position -= amount
                
            # Check if position exceeds limits
            if abs(self.current_position) > self.max_position:
                # Take risk mitigation actions
                pass
```

## Security Considerations

### API Key Management

- API keys should be stored securely and never hardcoded
- Consider using environment variables or a secure configuration system:

```python
import os
from liquid_energy.core import HummingbotClient

client = HummingbotClient(
    event_engine=event_engine,
    api_host=os.environ.get("HUMMINGBOT_HOST", "localhost"),
    api_port=int(os.environ.get("HUMMINGBOT_PORT", "15888")),
    api_key=os.environ.get("HUMMINGBOT_API_KEY")
)
```

### Connection Security

- Consider using WSS (WebSocket Secure) for production environments
- Validate server certificates for secure connections
- Implement IP whitelisting if possible

## Limitations and Future Improvements

### Current Limitations

- Limited support for advanced order types
- No built-in rate limiting for API requests
- Basic reconnection logic

### Planned Improvements

- Support for additional order types (Stop, Stop-Limit)
- Enhanced connection management with automatic reconnection
- More comprehensive error classification and handling
- Rate limiting to prevent API usage limits
- Performance optimizations for high-frequency trading

## Troubleshooting

### Common Issues

1. **Connection Failures**
   - Check if Hummingbot is running and accessible
   - Verify the host, port, and API key
   - Check network connectivity and firewalls

2. **Authentication Errors**
   - Ensure the API key is correct and authorized
   - Check if API key has the necessary permissions

3. **Timeout Errors**
   - Consider increasing the request timeout
   - Check Hummingbot system load and performance

4. **Order Placement Failures**
   - Verify exchange-specific requirements (min order size, price precision)
   - Check account balances
   - Validate market status (trading hours, market availability)

### Debugging

Enable detailed logging for troubleshooting:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("liquid_energy.core.hummingbot_client")
logger.setLevel(logging.DEBUG)
```

## Example Workflows

### Basic Market Making

```python
async def simple_market_making():
    # Initialize components
    event_engine = EventEngine()
    client = HummingbotClient(
        event_engine=event_engine,
        api_host="localhost",
        api_port=15888,
        api_key="your_api_key"
    )
    
    # Connect to Hummingbot
    await client.connect()
    
    try:
        # Subscribe to market data
        await client.subscribe_to_order_book(
            exchange="binance",
            market="ETH-USD"
        )
        
        # Get market information
        ticker = await client.get_ticker(
            exchange="binance",
            market="ETH-USD"
        )
        
        mid_price = (float(ticker["bid"]) + float(ticker["ask"])) / 2
        
        # Place market making orders
        bid_price = mid_price * 0.99  # 1% below mid
        ask_price = mid_price * 1.01  # 1% above mid
        
        # Create buy order
        buy_order = await client.create_order(
            exchange="binance",
            market="ETH-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=bid_price,
            amount=0.1
        )
        
        # Create sell order
        sell_order = await client.create_order(
            exchange="binance",
            market="ETH-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=ask_price,
            amount=0.1
        )
        
        # Wait for orders to be filled or cancelled
        await asyncio.sleep(300)  # 5 minutes
        
        # Cancel any remaining orders
        await client.cancel_order(
            exchange="binance",
            market="ETH-USD",
            order_id=buy_order["order_id"]
        )
        
        await client.cancel_order(
            exchange="binance",
            market="ETH-USD",
            order_id=sell_order["order_id"]
        )
        
    finally:
        # Disconnect when done
        await client.disconnect()
```

## Conclusion

The Hummingbot client provides a robust interface for executing trades and accessing market data through the Hummingbot trading engine. By integrating with the event-driven architecture, it enables building sophisticated trading strategies that can respond to real-time market conditions.
