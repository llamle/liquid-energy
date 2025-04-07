# Event-Driven Architecture

## Overview

The event-driven architecture is the foundation of the Liquid Energy trading system. It enables decoupled components to communicate through events, providing a flexible and extensible framework for market data processing, strategy execution, and trade management.

## Components

The event system consists of four main components:

1. **EventType**: An enumeration of possible event types in the system
2. **Event**: A class representing an event with its data and metadata
3. **EventListener**: An interface for components that can handle events
4. **EventEngine**: The central event processing and distribution system

## Design Philosophy

The event system follows these design principles:

- **Decoupling**: Components communicate indirectly through events, reducing dependencies
- **Single Responsibility**: Each component has a focused purpose
- **Extensibility**: New event types and listeners can be added without modifying existing code
- **Reliability**: Events are processed reliably even if individual handlers fail
- **Performance**: Efficient event distribution to minimize latency

## API Reference

### EventType

```python
class EventType(enum.Enum):
    """
    Enumeration of possible event types in the system.
    """
    MARKET_DATA = 1    # Market data updates (prices, volumes)
    ORDER_UPDATE = 2   # Order status changes
    TRADE_UPDATE = 3   # Completed trades
    STRATEGY_UPDATE = 4 # Strategy state changes
    ERROR = 5          # Error events
    INFO = 6           # Informational events
    SYSTEM = 7         # System-level events
```

#### Usage

```python
from liquid_energy.core import EventType

# Create events with specific types
market_event = Event(EventType.MARKET_DATA, {"price": 100.0})
order_event = Event(EventType.ORDER_UPDATE, {"order_id": "12345"})
```

### Event

```python
class Event:
    """
    Represents an event in the system with its data and metadata.
    """
    
    def __init__(
        self, 
        event_type: EventType, 
        data: Dict[str, Any], 
        source: Optional[str] = None
    ):
        """
        Initialize a new event.
        
        Args:
            event_type: Type of the event from EventType enum
            data: Dictionary containing event data
            source: Optional identifier of the event source
        """
```

#### Attributes

- **type**: The EventType of this event
- **data**: Dictionary containing the event payload
- **timestamp**: When the event was created
- **source**: Optional identifier of the event source

#### Usage

```python
from liquid_energy.core import Event, EventType

# Create a market data event
event = Event(
    event_type=EventType.MARKET_DATA,
    data={"symbol": "ETH-USD", "price": 3500.25, "volume": 10.5},
    source="exchange_connector"
)

# Access event attributes
print(f"Event type: {event.type}")
print(f"Event data: {event.data}")
print(f"Event time: {event.timestamp}")
print(f"Event source: {event.source}")
```

### EventListener

```python
class EventListener:
    """
    Interface for components that can handle events.
    """
    
    def __init__(self, name: str, event_types: List[EventType]):
        """
        Initialize a new event listener.
        
        Args:
            name: Unique name/identifier for the listener
            event_types: List of event types this listener can handle
        """
```

#### Methods

- **handle_event(event)**: Process an event (to be implemented by subclasses)
- **can_handle_event_type(event_type)**: Check if this listener can handle a specific event type

#### Creating Custom Listeners

```python
from liquid_energy.core import EventListener, EventType, Event

class PriceMonitor(EventListener):
    """
    Example listener that monitors price events.
    """
    
    def __init__(self, name: str):
        super().__init__(name, [EventType.MARKET_DATA])
        self.last_prices = {}
    
    def handle_event(self, event: Event) -> None:
        """Process market data events."""
        if "symbol" in event.data and "price" in event.data:
            symbol = event.data["symbol"]
            price = event.data["price"]
            self.last_prices[symbol] = price
            print(f"Price update for {symbol}: {price}")
```

### EventEngine

```python
class EventEngine:
    """
    Central event processing and distribution system.
    """
    
    def __init__(self):
        """
        Initialize a new event engine.
        """
```

#### Methods

- **register_listener(listener)**: Register a listener with the engine
- **unregister_listener(listener)**: Unregister a listener from the engine
- **get_listeners()**: Get all registered listeners
- **put(event)**: Put an event in the queue for processing
- **is_running()**: Check if the engine is running
- **start()**: Start the event processing thread
- **stop()**: Stop the event processing thread

#### Usage Example

```python
from liquid_energy.core import EventEngine, Event, EventType
from my_components import PriceMonitor, OrderManager

# Initialize components
engine = EventEngine()
price_monitor = PriceMonitor("price_monitor")
order_manager = OrderManager("order_manager")

# Register listeners
engine.register_listener(price_monitor)
engine.register_listener(order_manager)

# Start the engine
engine.start()

# Create and put events
market_event = Event(
    EventType.MARKET_DATA, 
    {"symbol": "ETH-USD", "price": 3500.25}
)
engine.put(market_event)

# When done, stop the engine
engine.stop()
```

## Integration With Other Components

### Connecting to Market Data Sources

The event system can be used to distribute market data from various sources:

```python
class MarketDataConnector:
    """
    Connects to a market data source and publishes events.
    """
    
    def __init__(self, event_engine: EventEngine, exchange_name: str):
        self.event_engine = event_engine
        self.exchange_name = exchange_name
    
    def on_market_data_received(self, data: dict):
        """
        Called when market data is received from the exchange.
        """
        event = Event(
            EventType.MARKET_DATA,
            data,
            source=self.exchange_name
        )
        self.event_engine.put(event)
```

### Implementing Trading Strategies

Strategies can listen for specific events and generate orders:

```python
class SimpleStrategy(EventListener):
    """
    Example of a simple trading strategy.
    """
    
    def __init__(self, name: str, event_engine: EventEngine):
        super().__init__(name, [EventType.MARKET_DATA])
        self.event_engine = event_engine
    
    def handle_event(self, event: Event) -> None:
        """Process market data and generate trading signals."""
        if event.type == EventType.MARKET_DATA:
            # Analysis and decision logic...
            
            # Generate an order
            order_event = Event(
                EventType.ORDER_UPDATE,
                {
                    "action": "create",
                    "symbol": event.data["symbol"],
                    "side": "buy",
                    "quantity": 1.0,
                    "price": event.data["price"] * 0.99  # Bid 1% below market
                },
                source=self.name
            )
            self.event_engine.put(order_event)
```

## Performance Considerations

### High-Frequency Event Processing

For high-frequency trading applications, consider these optimizations:

1. **Batch Processing**: Batch similar events together to reduce processing overhead
2. **Event Prioritization**: Implement priority queues for critical events
3. **Thread Pool**: Use a thread pool for parallel event processing
4. **Memory Management**: Reuse event objects to reduce garbage collection

### Memory Usage

Monitor memory usage, especially with high-volume data:

```python
def monitor_memory_usage(event_engine: EventEngine) -> None:
    """Monitor memory usage of the event engine."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    while event_engine.is_running():
        memory_info = process.memory_info()
        print(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
        time.sleep(60)  # Check every minute
```

## Error Handling

### Graceful Degradation

The system is designed to continue functioning even if individual components fail:

```python
def handle_event(self, event: Event) -> None:
    """
    Handle an event with proper error recovery.
    """
    try:
        # Normal processing...
        self.process_event_data(event)
    except Exception as e:
        # Log the error
        logger.error(f"Error processing event: {e}", exc_info=True)
        
        # Create an error event
        error_event = Event(
            EventType.ERROR,
            {
                "original_event_type": event.type,
                "error_message": str(e),
                "component": self.name
            },
            source=self.name
        )
        self.event_engine.put(error_event)
```

## Advanced Usage

### Custom Event Types

Extend the system with custom event types:

```python
# Add to the EventType enum
class EventType(enum.Enum):
    # Existing types...
    
    # Custom types
    ML_PREDICTION = 100
    ANOMALY_DETECTED = 101
    RISK_ALERT = 102
```

### Event Filters

Implement event filtering for more specific event handling:

```python
class FilteredListener(EventListener):
    """
    Listener that filters events based on criteria.
    """
    
    def __init__(self, name: str, event_types: List[EventType], filter_func):
        super().__init__(name, event_types)
        self.filter_func = filter_func
    
    def handle_event(self, event: Event) -> None:
        """Only handle events that pass the filter."""
        if self.filter_func(event):
            self.process_filtered_event(event)
    
    def process_filtered_event(self, event: Event) -> None:
        """Process events that passed the filter."""
        pass  # Implement in subclasses
```

## Testing

### Unit Testing

```python
def test_event_distribution():
    """Test that events are distributed to the correct listeners."""
    engine = EventEngine()
    
    # Create mock listeners
    listener1 = Mock(spec=EventListener)
    listener1.name = "listener1"
    listener1.event_types = [EventType.MARKET_DATA]
    listener1.can_handle_event_type = lambda event_type: event_type in listener1.event_types
    
    # Register listeners
    engine.register_listener(listener1)
    
    # Create and put an event
    event = Event(EventType.MARKET_DATA, {"price": 100.0})
    engine.put(event)
    
    # Start and let it process
    engine.start()
    time.sleep(0.1)
    engine.stop()
    
    # Verify
    listener1.handle_event.assert_called_once_with(event)
```

### Integration Testing

```python
def test_market_data_flow():
    """Test the flow of market data through the system."""
    # Set up components
    engine = EventEngine()
    connector = MarketDataConnector(engine, "test_exchange")
    strategy = SimpleStrategy("test_strategy", engine)
    
    # Register listeners
    engine.register_listener(strategy)
    
    # Start the engine
    engine.start()
    
    # Simulate market data
    connector.on_market_data_received({
        "symbol": "ETH-USD",
        "price": 3500.25,
        "volume": 10.5
    })
    
    # Give it time to process
    time.sleep(0.1)
    
    # Stop the engine
    engine.stop()
    
    # Verify results
    # (Check strategy state or mock order creation)
```

## Conclusion

The event-driven architecture provides a robust foundation for the Liquid Energy trading system. By decoupling components through events, we achieve a flexible and extensible system that can evolve with changing requirements.
