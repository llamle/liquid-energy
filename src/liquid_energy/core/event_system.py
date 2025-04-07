"""
Core event-driven architecture for the Liquid Energy trading system.

This module implements an event-driven system that enables decoupled components to 
communicate through events, providing a flexible and extensible framework for
market data processing, strategy execution, and trade management.
"""

import enum
import queue
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set


class EventType(enum.Enum):
    """
    Enumeration of possible event types in the system.
    """
    MARKET_DATA = 1
    ORDER_UPDATE = 2
    TRADE_UPDATE = 3
    STRATEGY_UPDATE = 4
    ERROR = 5
    INFO = 6
    SYSTEM = 7
    
    def __str__(self) -> str:
        """
        String representation of the event type.
        """
        return self.name


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
        self.type = event_type
        self.data = data.copy()  # Create a copy to ensure immutability
        self.timestamp = datetime.now()
        self.source = source

    def __eq__(self, other):
        """
        Compare events for equality based on type and data.
        
        Args:
            other: Another event to compare with
            
        Returns:
            bool: True if events are equal, False otherwise
        """
        if not isinstance(other, Event):
            return False
        
        return (
            self.type == other.type and 
            self.data == other.data
        )
    
    def __str__(self) -> str:
        """
        String representation of the event.
        
        Returns:
            str: String representation including type, data, timestamp, and source
        """
        source_str = f", source: {self.source}" if self.source else ""
        return f"Event(type: {self.type}, data: {self.data}, time: {self.timestamp}{source_str})"


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
        self.name = name
        self.event_types = set(event_types)
    
    def can_handle_event_type(self, event_type: EventType) -> bool:
        """
        Check if this listener can handle a specific event type.
        
        Args:
            event_type: The event type to check
            
        Returns:
            bool: True if this listener can handle the event type, False otherwise
        """
        return event_type in self.event_types
    
    def handle_event(self, event: Event) -> None:
        """
        Handle an event. Must be implemented by subclasses.
        
        Args:
            event: The event to handle
        """
        # Default implementation does nothing
        pass


class EventEngine:
    """
    Central event processing and distribution system.
    """
    
    def __init__(self):
        """
        Initialize a new event engine.
        """
        self._listeners: List[EventListener] = []
        self._event_queue = queue.Queue()
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
    
    def register_listener(self, listener: EventListener) -> None:
        """
        Register a listener with the engine.
        
        Args:
            listener: The listener to register
        """
        with self._lock:
            self._listeners.append(listener)
    
    def unregister_listener(self, listener: EventListener) -> None:
        """
        Unregister a listener from the engine.
        
        Args:
            listener: The listener to unregister
        """
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)
    
    def get_listeners(self) -> List[EventListener]:
        """
        Get all registered listeners.
        
        Returns:
            List[EventListener]: List of all registered listeners
        """
        with self._lock:
            return self._listeners.copy()
    
    def put(self, event: Event) -> None:
        """
        Put an event in the queue for processing.
        
        Args:
            event: The event to process
        """
        self._event_queue.put(event)
    
    def is_running(self) -> bool:
        """
        Check if the engine is running.
        
        Returns:
            bool: True if the engine is running, False otherwise
        """
        return self._running
    
    def start(self) -> None:
        """
        Start the event processing thread.
        """
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._process_events)
        self._thread.daemon = True
        self._thread.start()
    
    def stop(self) -> None:
        """
        Stop the event processing thread.
        """
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
    
    def _process_events(self) -> None:
        """
        Process events from the queue and distribute them to listeners.
        """
        while self._running:
            try:
                # Try to get an event from the queue with a timeout
                # This allows for checking the running state periodically
                try:
                    event = self._event_queue.get(block=True, timeout=0.1)
                except queue.Empty:
                    continue
                
                # Distribute the event to appropriate listeners
                self._distribute_event(event)
                
                # Mark the task as done
                self._event_queue.task_done()
                
            except Exception as e:
                # Log any exceptions but keep the thread running
                print(f"Error in event processing: {e}")
    
    def _distribute_event(self, event: Event) -> None:
        """
        Distribute an event to all appropriate listeners.
        
        Args:
            event: The event to distribute
        """
        # Get a copy of the listeners to avoid issues with concurrent modifications
        listeners = self.get_listeners()
        
        for listener in listeners:
            if listener.can_handle_event_type(event.type):
                try:
                    listener.handle_event(event)
                except Exception as e:
                    # Log any exceptions in listeners but continue processing
                    print(f"Error in listener {listener.name}: {e}")
