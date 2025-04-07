"""
Hummingbot API Integration for Liquid Energy trading system.

This module provides a client interface for interacting with the Hummingbot trading engine
via its WebSocket API, enabling order management, market data access, and account operations.
"""

import asyncio
import enum
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple, cast

import websockets
from websockets.client import WebSocketClientProtocol

from liquid_energy.core.event_system import EventEngine, Event, EventType


logger = logging.getLogger(__name__)


class OrderType(enum.Enum):
    """
    Enumeration of supported order types.
    """
    LIMIT = "limit"
    MARKET = "market"
    
    def __str__(self) -> str:
        """String representation of the order type."""
        return self.value


class OrderSide(enum.Enum):
    """
    Enumeration of order sides.
    """
    BUY = "buy"
    SELL = "sell"
    
    def __str__(self) -> str:
        """String representation of the order side."""
        return self.value


class OrderStatus(enum.Enum):
    """
    Enumeration of possible order statuses.
    """
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"
    
    def __str__(self) -> str:
        """String representation of the order status."""
        return self.value


class MarketType(enum.Enum):
    """
    Enumeration of market types.
    """
    SPOT = "spot"
    FUTURES = "futures"
    
    def __str__(self) -> str:
        """String representation of the market type."""
        return self.value


class ConnectionStatus(enum.Enum):
    """
    Enumeration of connection statuses.
    """
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class HummingbotClientException(Exception):
    """
    Exception raised for errors in the Hummingbot client.
    """
    pass


class HummingbotClient:
    """
    Client for interacting with the Hummingbot trading engine via WebSocket API.
    """
    
    def __init__(
        self,
        event_engine: EventEngine,
        api_host: str,
        api_port: int,
        api_key: str,
        request_timeout: float = 5.0,
        retry_attempts: int = 3
    ):
        """
        Initialize a new Hummingbot client.
        
        Args:
            event_engine: The event engine for publishing events
            api_host: Hostname of the Hummingbot API server
            api_port: Port of the Hummingbot API server
            api_key: API key for authentication
            request_timeout: Timeout for API requests in seconds
            retry_attempts: Number of retry attempts for failed operations
            
        Raises:
            ValueError: If any parameter is invalid
        """
        # Validate parameters
        if not api_host:
            raise ValueError("API host cannot be empty")
        
        if not isinstance(api_port, int) or api_port <= 0 or api_port > 65535:
            raise ValueError("API port must be a valid port number (1-65535)")
            
        if not api_key:
            raise ValueError("API key cannot be empty")
            
        if request_timeout <= 0:
            raise ValueError("Request timeout must be positive")
            
        if retry_attempts < 0:
            raise ValueError("Retry attempts cannot be negative")
        
        # Initialize instance variables
        self.event_engine = event_engine
        self.api_host = api_host
        self.api_port = api_port
        self.api_key = api_key
        self.request_timeout = request_timeout
        self.retry_attempts = retry_attempts
        
        # Connection state
        self.connection_status = ConnectionStatus.DISCONNECTED
        self._ws: Optional[WebSocketClientProtocol] = None
        self._message_id = 0
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._event_processor_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> None:
        """
        Connect to the Hummingbot WebSocket API.
        
        Raises:
            HummingbotClientException: If connection or authentication fails
        """
        if self.connection_status == ConnectionStatus.CONNECTED:
            logger.info("Already connected to Hummingbot")
            return
        
        uri = f"ws://{self.api_host}:{self.api_port}/ws"
        logger.info(f"Connecting to Hummingbot at {uri}")
        
        try:
            self.connection_status = ConnectionStatus.CONNECTING
            self._ws = await websockets.connect(uri)
            
            # Authenticate with API key
            auth_response = await self._send_request({
                "type": "authenticate",
                "api_key": self.api_key
            })
            
            if auth_response.get("status") != "success":
                error_msg = auth_response.get("message", "Authentication failed")
                raise HummingbotClientException(
                    f"Hummingbot authentication failed: {error_msg}"
                )
            
            # Start event processor
            self.connection_status = ConnectionStatus.CONNECTED
            self._event_processor_task = asyncio.create_task(self._process_events())
            
            logger.info("Successfully connected to Hummingbot")
            
        except Exception as e:
            self.connection_status = ConnectionStatus.ERROR
            await self._cleanup()
            raise HummingbotClientException(
                f"Failed to connect to Hummingbot: {str(e)}"
            )
    
    async def disconnect(self) -> None:
        """
        Disconnect from the Hummingbot WebSocket API.
        """
        logger.info("Disconnecting from Hummingbot")
        
        if self._event_processor_task:
            self._event_processor_task.cancel()
            try:
                await self._event_processor_task
            except asyncio.CancelledError:
                pass
            self._event_processor_task = None
        
        await self._cleanup()
        self.connection_status = ConnectionStatus.DISCONNECTED
        logger.info("Disconnected from Hummingbot")
    
    async def _cleanup(self) -> None:
        """
        Clean up resources.
        """
        if self._ws:
            try:
                await self._ws.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket connection: {e}")
            self._ws = None
    
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a request to Hummingbot and wait for the response.
        
        Args:
            request: Request message to send
            
        Returns:
            Dict[str, Any]: Response from Hummingbot
            
        Raises:
            HummingbotClientException: If the request fails
        """
        if not self._ws:
            raise HummingbotClientException("Not connected to Hummingbot")
        
        # Add request ID if not present
        if "id" not in request:
            self._message_id += 1
            request["id"] = str(self._message_id)
        
        request_id = request["id"]
        request_json = json.dumps(request)
        
        # Set up future for the response
        response_future: asyncio.Future = asyncio.Future()
        self._pending_requests[request_id] = response_future
        
        try:
            # Send the request
            await self._ws.send(request_json)
            
            # Wait for the response with timeout
            response = await asyncio.wait_for(
                response_future, 
                timeout=self.request_timeout
            )
            
            return cast(Dict[str, Any], response)
            
        except asyncio.TimeoutError:
            raise HummingbotClientException(
                f"Request timed out after {self.request_timeout} seconds"
            )
        except Exception as e:
            raise HummingbotClientException(f"Request failed: {str(e)}")
        finally:
            # Clean up
            if request_id in self._pending_requests:
                del self._pending_requests[request_id]
    
    async def _process_events(self) -> None:
        """
        Process incoming WebSocket events from Hummingbot.
        """
        try:
            while True:
                if not self._ws:
                    logger.error("WebSocket disconnected, stopping event processor")
                    break
                
                try:
                    # Wait for a message
                    message_str = await self._ws.recv()
                    message = json.loads(message_str)
                    
                    # Check if this is a response to a pending request
                    if "id" in message and message["id"] in self._pending_requests:
                        # Resolve the pending request
                        future = self._pending_requests[message["id"]]
                        if not future.done():
                            future.set_result(message)
                    else:
                        # This is an event, not a response
                        self._handle_event(message)
                        
                except json.JSONDecodeError:
                    logger.error(f"Received invalid JSON: {message_str}")
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")
        
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            logger.info("Event processor task cancelled")
        except Exception as e:
            logger.error(f"Unexpected error in event processor: {e}")
            # Set connection status to error and clean up
            self.connection_status = ConnectionStatus.ERROR
            asyncio.create_task(self._cleanup())
    
    def _handle_event(self, event: Dict[str, Any]) -> None:
        """
        Handle an event received from Hummingbot.
        
        Args:
            event: The event message from Hummingbot
        """
        event_type = event.get("type")
        data = event.get("data", {})
        
        if event_type == "order_update":
            # Convert to ORDER_UPDATE event
            self.event_engine.put(Event(
                EventType.ORDER_UPDATE,
                data,
                source="hummingbot"
            ))
        elif event_type == "trade":
            # Convert to TRADE_UPDATE event
            self.event_engine.put(Event(
                EventType.TRADE_UPDATE,
                data,
                source="hummingbot"
            ))
        elif event_type in ["order_book_update", "ticker_update"]:
            # Convert to MARKET_DATA event
            self.event_engine.put(Event(
                EventType.MARKET_DATA,
                data,
                source="hummingbot"
            ))
        elif event_type == "error":
            # Convert to ERROR event
            self.event_engine.put(Event(
                EventType.ERROR,
                data,
                source="hummingbot"
            ))
        elif event_type == "info":
            # Convert to INFO event
            self.event_engine.put(Event(
                EventType.INFO,
                data,
                source="hummingbot"
            ))
        else:
            logger.warning(f"Received unknown event type: {event_type}")
    
    async def create_order(
        self,
        exchange: str,
        market: str,
        side: OrderSide,
        order_type: OrderType,
        amount: float,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Create a new order.
        
        Args:
            exchange: Exchange identifier
            market: Market symbol
            side: Order side (buy/sell)
            order_type: Type of order (limit/market)
            amount: Order amount
            price: Order price (required for limit orders)
            
        Returns:
            Dict[str, Any]: Order details
            
        Raises:
            HummingbotClientException: If the order creation fails
        """
        if order_type == OrderType.LIMIT and price is None:
            raise ValueError("Price is required for limit orders")
        
        # Prepare request
        request: Dict[str, Any] = {
            "type": "create_order",
            "exchange": exchange,
            "market": market,
            "side": str(side),
            "order_type": str(order_type),
            "amount": str(amount)
        }
        
        # Add price for limit orders
        if order_type == OrderType.LIMIT and price is not None:
            request["price"] = str(price)
        
        try:
            response = await self._send_request(request)
            
            if response.get("status") != "success":
                error_msg = response.get("message", "Unknown error")
                raise HummingbotClientException(f"Failed to create order: {error_msg}")
            
            order_data = response.get("data", {})
            
            # Publish order update event
            self.event_engine.put(Event(
                EventType.ORDER_UPDATE,
                order_data,
                source="hummingbot"
            ))
            
            return order_data
            
        except HummingbotClientException:
            # Publish error event
            self.event_engine.put(Event(
                EventType.ERROR,
                {
                    "message": (
                        f"Failed to create {order_type} {side} order " +
                        f"for {market} on {exchange}"
                    ),
                    "exchange": exchange,
                    "market": market
                },
                source="hummingbot_client"
            ))
            raise
    
    async def cancel_order(
        self,
        exchange: str,
        market: str,
        order_id: str
    ) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            exchange: Exchange identifier
            market: Market symbol
            order_id: ID of the order to cancel
            
        Returns:
            Dict[str, Any]: Cancellation result
            
        Raises:
            HummingbotClientException: If the cancellation fails
        """
        # Prepare request
        request = {
            "type": "cancel_order",
            "exchange": exchange,
            "market": market,
            "order_id": order_id
        }
        
        try:
            response = await self._send_request(request)
            
            if response.get("status") != "success":
                error_msg = response.get("message", "Unknown error")
                raise HummingbotClientException(f"Failed to cancel order: {error_msg}")
            
            cancel_data = response.get("data", {})
            
            # Publish order update event
            self.event_engine.put(Event(
                EventType.ORDER_UPDATE,
                {
                    "order_id": order_id,
                    "status": "cancelled",
                    "exchange": exchange,
                    "market": market
                },
                source="hummingbot"
            ))
            
            return cancel_data
            
        except HummingbotClientException:
            # Publish error event
            self.event_engine.put(Event(
                EventType.ERROR,
                {
                    "message": (
                        f"Failed to cancel order {order_id} " +
                        f"for {market} on {exchange}"
                    ),
                    "exchange": exchange,
                    "market": market,
                    "order_id": order_id
                },
                source="hummingbot_client"
            ))
            raise
    
    async def get_order_status(
        self,
        exchange: str,
        market: str,
        order_id: str
    ) -> Dict[str, Any]:
        """
        Get the status of an order.
        
        Args:
            exchange: Exchange identifier
            market: Market symbol
            order_id: ID of the order
            
        Returns:
            Dict[str, Any]: Order details
            
        Raises:
            HummingbotClientException: If the request fails
        """
        # Prepare request
        request = {
            "type": "get_order",
            "exchange": exchange,
            "market": market,
            "order_id": order_id
        }
        
        response = await self._send_request(request)
        
        if response.get("status") != "success":
            error_msg = response.get("message", "Unknown error")
            raise HummingbotClientException(f"Failed to get order status: {error_msg}")
        
        return response.get("data", {})
    
    async def get_order_book(
        self,
        exchange: str,
        market: str,
        depth: int = 10
    ) -> Dict[str, Any]:
        """
        Get the current order book for a market.
        
        Args:
            exchange: Exchange identifier
            market: Market symbol
            depth: Depth of the order book to retrieve
            
        Returns:
            Dict[str, Any]: Order book data
            
        Raises:
            HummingbotClientException: If the request fails
        """
        # Prepare request
        request = {
            "type": "get_order_book",
            "exchange": exchange,
            "market": market,
            "depth": depth
        }
        
        response = await self._send_request(request)
        
        if response.get("status") != "success":
            error_msg = response.get("message", "Unknown error")
            raise HummingbotClientException(f"Failed to get order book: {error_msg}")
        
        return response.get("data", {})
    
    async def get_ticker(
        self,
        exchange: str,
        market: str
    ) -> Dict[str, Any]:
        """
        Get the current ticker information for a market.
        
        Args:
            exchange: Exchange identifier
            market: Market symbol
            
        Returns:
            Dict[str, Any]: Ticker data
            
        Raises:
            HummingbotClientException: If the request fails
        """
        # Prepare request
        request = {
            "type": "get_ticker",
            "exchange": exchange,
            "market": market
        }
        
        response = await self._send_request(request)
        
        if response.get("status") != "success":
            error_msg = response.get("message", "Unknown error")
            raise HummingbotClientException(f"Failed to get ticker: {error_msg}")
        
        return response.get("data", {})
    
    async def subscribe_to_order_book(
        self,
        exchange: str,
        market: str
    ) -> Dict[str, Any]:
        """
        Subscribe to order book updates for a market.
        
        Args:
            exchange: Exchange identifier
            market: Market symbol
            
        Returns:
            Dict[str, Any]: Subscription result
            
        Raises:
            HummingbotClientException: If the subscription fails
        """
        # Prepare request
        request = {
            "type": "subscribe",
            "channel": "order_book",
            "exchange": exchange,
            "market": market
        }
        
        response = await self._send_request(request)
        
        if response.get("status") != "success":
            error_msg = response.get("message", "Unknown error")
            raise HummingbotClientException(
                f"Failed to subscribe to order book: {error_msg}"
            )
        
        return response
    
    async def subscribe_to_trades(
        self,
        exchange: str,
        market: str
    ) -> Dict[str, Any]:
        """
        Subscribe to trade updates for a market.
        
        Args:
            exchange: Exchange identifier
            market: Market symbol
            
        Returns:
            Dict[str, Any]: Subscription result
            
        Raises:
            HummingbotClientException: If the subscription fails
        """
        # Prepare request
        request = {
            "type": "subscribe",
            "channel": "trades",
            "exchange": exchange,
            "market": market
        }
        
        response = await self._send_request(request)
        
        if response.get("status") != "success":
            error_msg = response.get("message", "Unknown error")
            raise HummingbotClientException(
                f"Failed to subscribe to trades: {error_msg}"
            )
        
        return response
    
    async def get_balances(
        self,
        exchange: str
    ) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        Get account balances.
        
        Args:
            exchange: Exchange identifier
            
        Returns:
            Dict[str, Dict[str, Dict[str, str]]]: Balances data
            
        Raises:
            HummingbotClientException: If the request fails
        """
        # Prepare request
        request = {
            "type": "get_balances",
            "exchange": exchange
        }
        
        response = await self._send_request(request)
        
        if response.get("status") != "success":
            error_msg = response.get("message", "Unknown error")
            raise HummingbotClientException(f"Failed to get balances: {error_msg}")
        
        return response.get("data", {})
    
    async def get_open_orders(
        self,
        exchange: str,
        market: str
    ) -> List[Dict[str, Any]]:
        """
        Get open orders for a market.
        
        Args:
            exchange: Exchange identifier
            market: Market symbol
            
        Returns:
            List[Dict[str, Any]]: List of open orders
            
        Raises:
            HummingbotClientException: If the request fails
        """
        # Prepare request
        request = {
            "type": "get_open_orders",
            "exchange": exchange,
            "market": market
        }
        
        response = await self._send_request(request)
        
        if response.get("status") != "success":
            error_msg = response.get("message", "Unknown error")
            raise HummingbotClientException(f"Failed to get open orders: {error_msg}")
        
        return response.get("data", [])
    
    async def get_order_history(
        self,
        exchange: str,
        market: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get order history for a market.
        
        Args:
            exchange: Exchange identifier
            market: Market symbol
            limit: Maximum number of orders to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of historical orders
            
        Raises:
            HummingbotClientException: If the request fails
        """
        # Prepare request
        request = {
            "type": "get_order_history",
            "exchange": exchange,
            "market": market,
            "limit": limit
        }
        
        response = await self._send_request(request)
        
        if response.get("status") != "success":
            error_msg = response.get("message", "Unknown error")
            raise HummingbotClientException(f"Failed to get order history: {error_msg}")
        
        return response.get("data", [])
