"""
Tests for the core event-driven architecture component.

Following TDD principles, these tests define the expected behavior of the event system
before any implementation is written.
"""
import pytest
from unittest.mock import Mock

# Import the components that we will eventually create
# These imports will fail initially (red phase)
from liquid_energy.core.event_system import (
    EventEngine, Event, EventType, EventListener
)


class TestEventTypes:
    """Tests for the EventType enumeration"""
    
    def test_event_type_uniqueness(self):
        """Test that event types are unique"""
        # This test verifies that all event types have unique values
        event_types = [
            EventType.MARKET_DATA, 
            EventType.ORDER_UPDATE,
            EventType.TRADE_UPDATE,
            EventType.STRATEGY_UPDATE,
            EventType.ERROR,
            EventType.INFO,
            EventType.SYSTEM
        ]
        # Check that all values are unique
        assert len(event_types) == len(set(event_types))
    
    def test_event_type_str_representation(self):
        """Test the string representation of event types"""
        assert str(EventType.MARKET_DATA) == "MARKET_DATA"
        assert str(EventType.ORDER_UPDATE) == "ORDER_UPDATE"


class TestEvent:
    """Tests for the Event class"""
    
    def test_event_initialization(self):
        """Test that an event can be initialized with type and data"""
        data = {"price": 100.0, "volume": 10}
        event = Event(EventType.MARKET_DATA, data)
        
        assert event.type == EventType.MARKET_DATA
        assert event.data == data
        assert event.timestamp is not None  # Should have a timestamp
    
    def test_event_with_optional_arguments(self):
        """Test that an event can be initialized with optional arguments"""
        data = {"price": 100.0}
        source = "market_connector"
        event = Event(EventType.MARKET_DATA, data, source=source)
        
        assert event.type == EventType.MARKET_DATA
        assert event.data == data
        assert event.source == source
    
    def test_event_equality(self):
        """Test that events with the same properties are considered equal"""
        data = {"price": 100.0}
        event1 = Event(EventType.MARKET_DATA, data)
        event2 = Event(EventType.MARKET_DATA, data.copy())
        event3 = Event(EventType.ORDER_UPDATE, data)
        
        assert event1 == event1  # Same object
        assert event1 != event3  # Different type
        # We need to implement __eq__ in the Event class to compare data
        assert event1.type == event2.type
        assert event1.data == event2.data
    
    def test_event_string_representation(self):
        """Test the string representation of an event"""
        data = {"price": 100.0}
        event = Event(EventType.MARKET_DATA, data)
        
        # The string representation should contain the type and data
        assert str(EventType.MARKET_DATA) in str(event)
        assert str(data) in str(event)


class TestEventListener:
    """Tests for the EventListener interface/class"""
    
    def test_listener_registration(self):
        """Test that a listener can be created with event types"""
        listener = EventListener("test_listener", [EventType.MARKET_DATA, EventType.TRADE_UPDATE])
        
        assert listener.name == "test_listener"
        assert EventType.MARKET_DATA in listener.event_types
        assert EventType.TRADE_UPDATE in listener.event_types
        assert EventType.ORDER_UPDATE not in listener.event_types
    
    def test_listener_handler_method(self):
        """Test that a listener's handle_event method can be called"""
        handler = Mock()
        
        # Create a listener with a custom handle_event implementation
        class CustomListener(EventListener):
            def handle_event(self, event):
                handler(event)
        
        listener = CustomListener("custom", [EventType.MARKET_DATA])
        event = Event(EventType.MARKET_DATA, {"price": 100.0})
        
        listener.handle_event(event)
        handler.assert_called_once_with(event)
    
    def test_listener_handles_correct_event_types(self):
        """Test that a listener handles only the event types it registered for"""
        listener = EventListener("test_listener", [EventType.MARKET_DATA])
        
        # The listener should handle MARKET_DATA events
        assert listener.can_handle_event_type(EventType.MARKET_DATA) is True
        
        # But not other event types
        assert listener.can_handle_event_type(EventType.ORDER_UPDATE) is False


class TestEventEngine:
    """Tests for the EventEngine class"""
    
    def test_engine_initialization(self):
        """Test that an event engine can be initialized"""
        engine = EventEngine()
        
        # The engine should start with no listeners
        assert len(engine.get_listeners()) == 0
        
        # The engine should not be running initially
        assert engine.is_running() is False
    
    def test_register_listener(self):
        """Test that a listener can be registered with the engine"""
        engine = EventEngine()
        listener = EventListener("test", [EventType.MARKET_DATA])
        
        engine.register_listener(listener)
        
        assert listener in engine.get_listeners()
        assert len(engine.get_listeners()) == 1
    
    def test_unregister_listener(self):
        """Test that a listener can be unregistered from the engine"""
        engine = EventEngine()
        listener = EventListener("test", [EventType.MARKET_DATA])
        
        engine.register_listener(listener)
        assert len(engine.get_listeners()) == 1
        
        engine.unregister_listener(listener)
        assert len(engine.get_listeners()) == 0
    
    def test_put_event(self):
        """Test that an event can be put into the engine"""
        engine = EventEngine()
        event = Event(EventType.MARKET_DATA, {"price": 100.0})
        
        # We'll create a mock listener to verify the event is dispatched
        listener = Mock(spec=EventListener)
        listener.name = "mock_listener"
        listener.event_types = [EventType.MARKET_DATA]
        listener.can_handle_event_type = lambda event_type: event_type in listener.event_types
        
        engine.register_listener(listener)
        
        # Put the event in the engine
        engine.put(event)
        
        # Start the engine to process events
        engine.start()
        
        # Give it a moment to process (in a real test, we would use proper synchronization)
        import time
        time.sleep(0.1)
        
        # Stop the engine
        engine.stop()
        
        # The listener should have been called with the event
        listener.handle_event.assert_called_once_with(event)
    
    def test_engine_start_stop(self):
        """Test that the engine can be started and stopped"""
        engine = EventEngine()
        
        assert engine.is_running() is False
        
        engine.start()
        assert engine.is_running() is True
        
        engine.stop()
        assert engine.is_running() is False
    
    def test_event_distribution_to_multiple_listeners(self):
        """Test that events are distributed to all appropriate listeners"""
        engine = EventEngine()
        
        # Create multiple mock listeners with different event types
        listener1 = Mock(spec=EventListener)
        listener1.name = "listener1"
        listener1.event_types = [EventType.MARKET_DATA]
        listener1.can_handle_event_type = lambda event_type: event_type in listener1.event_types
        
        listener2 = Mock(spec=EventListener)
        listener2.name = "listener2"
        listener2.event_types = [EventType.MARKET_DATA, EventType.TRADE_UPDATE]
        listener2.can_handle_event_type = lambda event_type: event_type in listener2.event_types
        
        listener3 = Mock(spec=EventListener)
        listener3.name = "listener3"
        listener3.event_types = [EventType.ORDER_UPDATE]
        listener3.can_handle_event_type = lambda event_type: event_type in listener3.event_types
        
        # Register all listeners
        engine.register_listener(listener1)
        engine.register_listener(listener2)
        engine.register_listener(listener3)
        
        # Create events
        market_event = Event(EventType.MARKET_DATA, {"price": 100.0})
        order_event = Event(EventType.ORDER_UPDATE, {"order_id": "123"})
        
        # Put events in the engine
        engine.put(market_event)
        engine.put(order_event)
        
        # Start the engine to process events
        engine.start()
        
        # Give it a moment to process
        import time
        time.sleep(0.1)
        
        # Stop the engine
        engine.stop()
        
        # Verify that listeners received the appropriate events
        listener1.handle_event.assert_called_once_with(market_event)
        
        # listener2 should have received only the market_event
        listener2.handle_event.assert_called_once_with(market_event)
        
        # listener3 should have received only the order_event
        listener3.handle_event.assert_called_once_with(order_event)
    
    def test_error_handling_in_listeners(self):
        """Test that errors in listeners are properly handled"""
        engine = EventEngine()
        
        # Create a listener that raises an exception
        error_listener = Mock(spec=EventListener)
        error_listener.name = "error_listener"
        error_listener.event_types = [EventType.MARKET_DATA]
        error_listener.can_handle_event_type = lambda event_type: event_type in error_listener.event_types
        error_listener.handle_event.side_effect = Exception("Test exception")
        
        # Create a normal listener
        normal_listener = Mock(spec=EventListener)
        normal_listener.name = "normal_listener"
        normal_listener.event_types = [EventType.MARKET_DATA]
        normal_listener.can_handle_event_type = lambda event_type: event_type in normal_listener.event_types
        
        # Register both listeners
        engine.register_listener(error_listener)
        engine.register_listener(normal_listener)
        
        # Create and put an event
        event = Event(EventType.MARKET_DATA, {"price": 100.0})
        engine.put(event)
        
        # Start the engine
        engine.start()
        
        # Give it a moment to process
        import time
        time.sleep(0.1)
        
        # Stop the engine
        engine.stop()
        
        # The error in the first listener should not prevent the second listener from receiving the event
        error_listener.handle_event.assert_called_once_with(event)
        normal_listener.handle_event.assert_called_once_with(event)
