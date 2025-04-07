"""
Tests for the Hummingbot API Integration component.

Following TDD principles, these tests define the expected behavior of the Hummingbot client
before any implementation is written.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio
import json
import websockets
from datetime import datetime
import uuid

# Import the components that we will eventually create
# These imports will fail initially (red phase)
from liquid_energy.core.hummingbot_client import (
    HummingbotClient,
    OrderType,
    OrderSide,
    OrderStatus,
    MarketType,
    ConnectionStatus,
    HummingbotClientException
)

from liquid_energy.core.event_system import EventEngine, Event, EventType

# Mark all tests in this module as asyncio tests
pytestmark = pytest.mark.asyncio

class TestHummingbotClientInit:
    """Tests for HummingbotClient initialization and configuration"""
    
    def test_client_initialization(self):
        """Test that a client can be initialized with required parameters"""
        event_engine = Mock(spec=EventEngine)
        client = HummingbotClient(
            event_engine=event_engine,
            api_host="localhost",
            api_port=15888,
            api_key="test_api_key"
        )
        
        assert client.api_host == "localhost"
        assert client.api_port == 15888
        assert client.api_key == "test_api_key"
        assert client.event_engine == event_engine
        assert client.connection_status == ConnectionStatus.DISCONNECTED
    
    def test_client_initialization_with_optional_params(self):
        """Test that a client can be initialized with optional parameters"""
        event_engine = Mock(spec=EventEngine)
        client = HummingbotClient(
            event_engine=event_engine,
            api_host="localhost",
            api_port=15888,
            api_key="test_api_key",
            request_timeout=10.0,
            retry_attempts=3
        )
        
        assert client.request_timeout == 10.0
        assert client.retry_attempts == 3
    
    def test_client_initialization_with_invalid_params(self):
        """Test that initialization with invalid parameters raises appropriate exceptions"""
        event_engine = Mock(spec=EventEngine)
        
        # Invalid port
        with pytest.raises(ValueError):
            HummingbotClient(
                event_engine=event_engine,
                api_host="localhost",
                api_port=-1,  # Invalid port
                api_key="test_api_key"
            )
        
        # Invalid timeout
        with pytest.raises(ValueError):
            HummingbotClient(
                event_engine=event_engine,
                api_host="localhost",
                api_port=15888,
                api_key="test_api_key",
                request_timeout=-1.0  # Invalid timeout
            )
        
        # Invalid retry attempts
        with pytest.raises(ValueError):
            HummingbotClient(
                event_engine=event_engine,
                api_host="localhost",
                api_port=15888,
                api_key="test_api_key",
                retry_attempts=-1  # Invalid retry attempts
            )


class TestHummingbotClientConnection:
    """Tests for HummingbotClient connection management"""
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock websocket for testing"""
        mock_ws = Mock()
        mock_ws.__aenter__ = AsyncMock(return_value=mock_ws)
        mock_ws.__aexit__ = AsyncMock(return_value=None)
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(return_value=json.dumps({"status": "success"}))
        return mock_ws
    
    @pytest.fixture
    def client(self):
        """Create a client instance for testing"""
        event_engine = Mock(spec=EventEngine)
        event_engine.put = Mock()
        return HummingbotClient(
            event_engine=event_engine,
            api_host="localhost",
            api_port=15888,
            api_key="test_api_key"
        )
    
    async def test_connect_success(self, client, mock_websocket):
        """Test successful connection to Hummingbot"""
        with patch('websockets.connect', return_value=mock_websocket):
            await client.connect()
            
            assert client.connection_status == ConnectionStatus.CONNECTED
            assert client._ws == mock_websocket
            
            # Should have sent authentication message
            auth_message = json.loads(mock_websocket.send.call_args[0][0])
            assert auth_message["type"] == "authenticate"
            assert auth_message["api_key"] == "test_api_key"
    
    async def test_connect_failure_auth(self, client, mock_websocket):
        """Test failed authentication during connection"""
        # Mock authentication failure response
        mock_websocket.recv = AsyncMock(return_value=json.dumps({
            "status": "error",
            "message": "Authentication failed"
        }))
        
        with patch('websockets.connect', return_value=mock_websocket):
            with pytest.raises(HummingbotClientException):
                await client.connect()
            
            assert client.connection_status == ConnectionStatus.DISCONNECTED
    
    async def test_connect_failure_connection(self, client):
        """Test connection failure"""
        with patch('websockets.connect', side_effect=Exception("Connection failed")):
            with pytest.raises(HummingbotClientException):
                await client.connect()
            
            assert client.connection_status == ConnectionStatus.DISCONNECTED
    
    async def test_disconnect(self, client, mock_websocket):
        """Test disconnection from Hummingbot"""
        # Set up connected state
        with patch('websockets.connect', return_value=mock_websocket):
            await client.connect()
            assert client.connection_status == ConnectionStatus.CONNECTED
            
            # Now test disconnection
            await client.disconnect()
            
            assert client.connection_status == ConnectionStatus.DISCONNECTED
            assert client._ws.close.called


class TestHummingbotClientOrders:
    """Tests for order-related functionality"""
    
    @pytest.fixture
    def client(self):
        """Create a connected client instance for testing"""
        event_engine = Mock(spec=EventEngine)
        event_engine.put = Mock()
        client = HummingbotClient(
            event_engine=event_engine,
            api_host="localhost",
            api_port=15888,
            api_key="test_api_key"
        )
        client.connection_status = ConnectionStatus.CONNECTED
        client._ws = Mock()
        client._ws.send = AsyncMock()
        client._ws.recv = AsyncMock(return_value=json.dumps({"status": "success"}))
        return client
    
    async def test_create_limit_order(self, client):
        """Test creating a limit order"""
        # Setup successful order response
        order_id = str(uuid.uuid4())
        client._ws.recv = AsyncMock(return_value=json.dumps({
            "status": "success",
            "data": {
                "order_id": order_id,
                "symbol": "ETH-USD",
                "exchange": "binance",
                "price": "3000.0",
                "amount": "1.0",
                "side": "buy",
                "type": "limit",
                "status": "open"
            }
        }))
        
        result = await client.create_order(
            exchange="binance",
            market="ETH-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=3000.0,
            amount=1.0
        )
        
        # Verify the request
        sent_message = json.loads(client._ws.send.call_args[0][0])
        assert sent_message["type"] == "create_order"
        assert sent_message["exchange"] == "binance"
        assert sent_message["market"] == "ETH-USD"
        assert sent_message["side"] == "buy"
        assert sent_message["order_type"] == "limit"
        assert float(sent_message["price"]) == 3000.0
        assert float(sent_message["amount"]) == 1.0
        
        # Verify the result
        assert result["order_id"] == order_id
        assert result["symbol"] == "ETH-USD"
        assert result["status"] == "open"
        
        # Verify event was published
        order_event_call = client.event_engine.put.call_args[0][0]
        assert order_event_call.type == EventType.ORDER_UPDATE
        assert order_event_call.data["order_id"] == order_id
    
    async def test_create_market_order(self, client):
        """Test creating a market order"""
        # Setup successful order response
        order_id = str(uuid.uuid4())
        client._ws.recv = AsyncMock(return_value=json.dumps({
            "status": "success",
            "data": {
                "order_id": order_id,
                "symbol": "ETH-USD",
                "exchange": "binance",
                "price": None,  # Market orders don't specify price
                "amount": "1.0",
                "side": "sell",
                "type": "market",
                "status": "filled"  # Market orders are usually filled immediately
            }
        }))
        
        result = await client.create_order(
            exchange="binance",
            market="ETH-USD",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            amount=1.0
        )
        
        # Verify the request
        sent_message = json.loads(client._ws.send.call_args[0][0])
        assert sent_message["type"] == "create_order"
        assert sent_message["exchange"] == "binance"
        assert sent_message["market"] == "ETH-USD"
        assert sent_message["side"] == "sell"
        assert sent_message["order_type"] == "market"
        assert "price" not in sent_message  # Market orders don't need price
        assert float(sent_message["amount"]) == 1.0
        
        # Verify the result
        assert result["order_id"] == order_id
        assert result["symbol"] == "ETH-USD"
        assert result["status"] == "filled"
        
        # Verify event was published
        order_event_call = client.event_engine.put.call_args[0][0]
        assert order_event_call.type == EventType.ORDER_UPDATE
        assert order_event_call.data["order_id"] == order_id
    
    async def test_create_order_error(self, client):
        """Test error handling when creating an order"""
        # Setup error response
        client._ws.recv = AsyncMock(return_value=json.dumps({
            "status": "error",
            "message": "Insufficient funds"
        }))
        
        with pytest.raises(HummingbotClientException) as exc_info:
            await client.create_order(
                exchange="binance",
                market="ETH-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=3000.0,
                amount=1.0
            )
        
        assert "Insufficient funds" in str(exc_info.value)
        
        # Verify error event was published
        error_event_call = client.event_engine.put.call_args[0][0]
        assert error_event_call.type == EventType.ERROR
    
    async def test_cancel_order(self, client):
        """Test cancelling an order"""
        order_id = str(uuid.uuid4())
        client._ws.recv = AsyncMock(return_value=json.dumps({
            "status": "success",
            "data": {
                "order_id": order_id,
                "cancelled": True
            }
        }))
        
        result = await client.cancel_order(
            exchange="binance",
            market="ETH-USD",
            order_id=order_id
        )
        
        # Verify the request
        sent_message = json.loads(client._ws.send.call_args[0][0])
        assert sent_message["type"] == "cancel_order"
        assert sent_message["exchange"] == "binance"
        assert sent_message["market"] == "ETH-USD"
        assert sent_message["order_id"] == order_id
        
        # Verify the result
        assert result["order_id"] == order_id
        assert result["cancelled"] is True
        
        # Verify event was published
        cancel_event_call = client.event_engine.put.call_args[0][0]
        assert cancel_event_call.type == EventType.ORDER_UPDATE
        assert cancel_event_call.data["order_id"] == order_id
        assert cancel_event_call.data["status"] == "cancelled"
    
    async def test_get_order_status(self, client):
        """Test getting order status"""
        order_id = str(uuid.uuid4())
        client._ws.recv = AsyncMock(return_value=json.dumps({
            "status": "success",
            "data": {
                "order_id": order_id,
                "symbol": "ETH-USD",
                "exchange": "binance",
                "price": "3000.0",
                "amount": "1.0",
                "filled": "0.5",
                "side": "buy",
                "type": "limit",
                "status": "partially_filled"
            }
        }))
        
        result = await client.get_order_status(
            exchange="binance",
            market="ETH-USD",
            order_id=order_id
        )
        
        # Verify the request
        sent_message = json.loads(client._ws.send.call_args[0][0])
        assert sent_message["type"] == "get_order"
        assert sent_message["exchange"] == "binance"
        assert sent_message["market"] == "ETH-USD"
        assert sent_message["order_id"] == order_id
        
        # Verify the result
        assert result["order_id"] == order_id
        assert result["symbol"] == "ETH-USD"
        assert result["status"] == "partially_filled"
        assert float(result["filled"]) == 0.5


class TestHummingbotClientMarketData:
    """Tests for market data functionality"""
    
    @pytest.fixture
    def client(self):
        """Create a connected client instance for testing"""
        event_engine = Mock(spec=EventEngine)
        event_engine.put = Mock()
        client = HummingbotClient(
            event_engine=event_engine,
            api_host="localhost",
            api_port=15888,
            api_key="test_api_key"
        )
        client.connection_status = ConnectionStatus.CONNECTED
        client._ws = Mock()
        client._ws.send = AsyncMock()
        client._ws.recv = AsyncMock(return_value=json.dumps({"status": "success"}))
        return client
    
    async def test_get_order_book(self, client):
        """Test getting order book data"""
        # Setup successful response with order book data
        client._ws.recv = AsyncMock(return_value=json.dumps({
            "status": "success",
            "data": {
                "timestamp": datetime.now().timestamp(),
                "bids": [
                    ["3000.0", "1.5"],
                    ["2999.0", "2.0"]
                ],
                "asks": [
                    ["3001.0", "1.0"],
                    ["3002.0", "3.0"]
                ]
            }
        }))
        
        result = await client.get_order_book(
            exchange="binance",
            market="ETH-USD",
            depth=5
        )
        
        # Verify the request
        sent_message = json.loads(client._ws.send.call_args[0][0])
        assert sent_message["type"] == "get_order_book"
        assert sent_message["exchange"] == "binance"
        assert sent_message["market"] == "ETH-USD"
        assert sent_message["depth"] == 5
        
        # Verify the result
        assert "timestamp" in result
        assert "bids" in result
        assert "asks" in result
        assert len(result["bids"]) == 2
        assert len(result["asks"]) == 2
        assert float(result["bids"][0][0]) == 3000.0  # Price
        assert float(result["bids"][0][1]) == 1.5     # Amount
    
    async def test_get_ticker(self, client):
        """Test getting ticker data"""
        # Setup successful response with ticker data
        client._ws.recv = AsyncMock(return_value=json.dumps({
            "status": "success",
            "data": {
                "timestamp": datetime.now().timestamp(),
                "symbol": "ETH-USD",
                "exchange": "binance",
                "bid": "3000.0",
                "ask": "3001.0",
                "last": "3000.5",
                "volume": "1000.0"
            }
        }))
        
        result = await client.get_ticker(
            exchange="binance",
            market="ETH-USD"
        )
        
        # Verify the request
        sent_message = json.loads(client._ws.send.call_args[0][0])
        assert sent_message["type"] == "get_ticker"
        assert sent_message["exchange"] == "binance"
        assert sent_message["market"] == "ETH-USD"
        
        # Verify the result
        assert result["symbol"] == "ETH-USD"
        assert float(result["bid"]) == 3000.0
        assert float(result["ask"]) == 3001.0
        assert float(result["last"]) == 3000.5
        assert float(result["volume"]) == 1000.0
    
    async def test_subscribe_to_order_book(self, client):
        """Test subscribing to order book updates"""
        # Setup successful subscription response
        client._ws.recv = AsyncMock(return_value=json.dumps({
            "status": "success",
            "message": "Subscribed to order book updates for ETH-USD on binance"
        }))
        
        result = await client.subscribe_to_order_book(
            exchange="binance",
            market="ETH-USD"
        )
        
        # Verify the request
        sent_message = json.loads(client._ws.send.call_args[0][0])
        assert sent_message["type"] == "subscribe"
        assert sent_message["channel"] == "order_book"
        assert sent_message["exchange"] == "binance"
        assert sent_message["market"] == "ETH-USD"
        
        # Verify the result
        assert result["status"] == "success"
        assert "Subscribed to order book" in result["message"]
    
    async def test_subscribe_to_trades(self, client):
        """Test subscribing to trade updates"""
        # Setup successful subscription response
        client._ws.recv = AsyncMock(return_value=json.dumps({
            "status": "success",
            "message": "Subscribed to trade updates for ETH-USD on binance"
        }))
        
        result = await client.subscribe_to_trades(
            exchange="binance",
            market="ETH-USD"
        )
        
        # Verify the request
        sent_message = json.loads(client._ws.send.call_args[0][0])
        assert sent_message["type"] == "subscribe"
        assert sent_message["channel"] == "trades"
        assert sent_message["exchange"] == "binance"
        assert sent_message["market"] == "ETH-USD"
        
        # Verify the result
        assert result["status"] == "success"
        assert "Subscribed to trade updates" in result["message"]


class TestHummingbotClientAccountData:
    """Tests for account data functionality"""
    
    @pytest.fixture
    def client(self):
        """Create a connected client instance for testing"""
        event_engine = Mock(spec=EventEngine)
        event_engine.put = Mock()
        client = HummingbotClient(
            event_engine=event_engine,
            api_host="localhost",
            api_port=15888,
            api_key="test_api_key"
        )
        client.connection_status = ConnectionStatus.CONNECTED
        client._ws = Mock()
        client._ws.send = AsyncMock()
        client._ws.recv = AsyncMock(return_value=json.dumps({"status": "success"}))
        return client
    
    async def test_get_balances(self, client):
        """Test getting account balances"""
        # Setup successful response with balance data
        client._ws.recv = AsyncMock(return_value=json.dumps({
            "status": "success",
            "data": {
                "binance": {
                    "ETH": {
                        "total": "10.0",
                        "available": "8.5"
                    },
                    "USD": {
                        "total": "50000.0",
                        "available": "45000.0"
                    }
                }
            }
        }))
        
        result = await client.get_balances(exchange="binance")
        
        # Verify the request
        sent_message = json.loads(client._ws.send.call_args[0][0])
        assert sent_message["type"] == "get_balances"
        assert sent_message["exchange"] == "binance"
        
        # Verify the result
        assert "binance" in result
        assert "ETH" in result["binance"]
        assert "USD" in result["binance"]
        assert float(result["binance"]["ETH"]["total"]) == 10.0
        assert float(result["binance"]["ETH"]["available"]) == 8.5
        assert float(result["binance"]["USD"]["total"]) == 50000.0
        assert float(result["binance"]["USD"]["available"]) == 45000.0
    
    async def test_get_open_orders(self, client):
        """Test getting open orders"""
        # Setup successful response with open orders data
        order_id = str(uuid.uuid4())
        client._ws.recv = AsyncMock(return_value=json.dumps({
            "status": "success",
            "data": [
                {
                    "order_id": order_id,
                    "symbol": "ETH-USD",
                    "exchange": "binance",
                    "price": "3000.0",
                    "amount": "1.0",
                    "filled": "0.0",
                    "side": "buy",
                    "type": "limit",
                    "status": "open",
                    "created_at": datetime.now().timestamp()
                }
            ]
        }))
        
        result = await client.get_open_orders(
            exchange="binance",
            market="ETH-USD"
        )
        
        # Verify the request
        sent_message = json.loads(client._ws.send.call_args[0][0])
        assert sent_message["type"] == "get_open_orders"
        assert sent_message["exchange"] == "binance"
        assert sent_message["market"] == "ETH-USD"
        
        # Verify the result
        assert len(result) == 1
        assert result[0]["order_id"] == order_id
        assert result[0]["symbol"] == "ETH-USD"
        assert result[0]["status"] == "open"
        assert float(result[0]["price"]) == 3000.0
        assert float(result[0]["amount"]) == 1.0
    
    async def test_get_order_history(self, client):
        """Test getting order history"""
        # Setup successful response with order history data
        order_id = str(uuid.uuid4())
        client._ws.recv = AsyncMock(return_value=json.dumps({
            "status": "success",
            "data": [
                {
                    "order_id": order_id,
                    "symbol": "ETH-USD",
                    "exchange": "binance",
                    "price": "3000.0",
                    "amount": "1.0",
                    "filled": "1.0",
                    "side": "buy",
                    "type": "limit",
                    "status": "filled",
                    "created_at": (datetime.now().timestamp() - 3600),  # 1 hour ago
                    "filled_at": datetime.now().timestamp()
                }
            ]
        }))
        
        result = await client.get_order_history(
            exchange="binance",
            market="ETH-USD",
            limit=10
        )
        
        # Verify the request
        sent_message = json.loads(client._ws.send.call_args[0][0])
        assert sent_message["type"] == "get_order_history"
        assert sent_message["exchange"] == "binance"
        assert sent_message["market"] == "ETH-USD"
        assert sent_message["limit"] == 10
        
        # Verify the result
        assert len(result) == 1
        assert result[0]["order_id"] == order_id
        assert result[0]["symbol"] == "ETH-USD"
        assert result[0]["status"] == "filled"
        assert float(result[0]["price"]) == 3000.0
        assert float(result[0]["amount"]) == 1.0
        assert float(result[0]["filled"]) == 1.0


class TestHummingbotClientEventHandling:
    """Tests for handling events from Hummingbot websocket"""
    
    @pytest.fixture
    def client(self):
        """Create a client instance for testing events"""
        event_engine = Mock(spec=EventEngine)
        event_engine.put = Mock()
        client = HummingbotClient(
            event_engine=event_engine,
            api_host="localhost",
            api_port=15888,
            api_key="test_api_key"
        )
        client.connection_status = ConnectionStatus.CONNECTED
        client._ws = Mock()
        return client
    
    def test_handle_order_update_event(self, client):
        """Test handling order update events from Hummingbot"""
        order_id = str(uuid.uuid4())
        # Create an order update event from Hummingbot
        order_update = {
            "type": "order_update",
            "data": {
                "order_id": order_id,
                "symbol": "ETH-USD",
                "exchange": "binance",
                "price": "3000.0",
                "amount": "1.0",
                "filled": "0.5",
                "side": "buy",
                "order_type": "limit",
                "status": "partially_filled",
                "timestamp": datetime.now().timestamp()
            }
        }
        
        # Process the event
        client._handle_event(order_update)
        
        # Verify that an event was published to the event engine
        event_engine_call = client.event_engine.put.call_args[0][0]
        assert isinstance(event_engine_call, Event)
        assert event_engine_call.type == EventType.ORDER_UPDATE
        assert event_engine_call.data["order_id"] == order_id
        assert event_engine_call.data["status"] == "partially_filled"
        assert float(event_engine_call.data["filled"]) == 0.5
    
    def test_handle_trade_event(self, client):
        """Test handling trade events from Hummingbot"""
        trade_id = str(uuid.uuid4())
        # Create a trade event from Hummingbot
        trade_event = {
            "type": "trade",
            "data": {
                "trade_id": trade_id,
                "symbol": "ETH-USD",
                "exchange": "binance",
                "price": "3000.0",
                "amount": "1.0",
                "side": "buy",
                "timestamp": datetime.now().timestamp()
            }
        }
        
        # Process the event
        client._handle_event(trade_event)
        
        # Verify that an event was published to the event engine
        event_engine_call = client.event_engine.put.call_args[0][0]
        assert isinstance(event_engine_call, Event)
        assert event_engine_call.type == EventType.TRADE_UPDATE
        assert event_engine_call.data["trade_id"] == trade_id
        assert event_engine_call.data["symbol"] == "ETH-USD"
        assert float(event_engine_call.data["price"]) == 3000.0
    
    def test_handle_market_data_event(self, client):
        """Test handling market data events from Hummingbot"""
        # Create a market data event from Hummingbot
        market_data_event = {
            "type": "order_book_update",
            "data": {
                "symbol": "ETH-USD",
                "exchange": "binance",
                "bids": [
                    ["3000.0", "1.5"],
                    ["2999.0", "2.0"]
                ],
                "asks": [
                    ["3001.0", "1.0"],
                    ["3002.0", "3.0"]
                ],
                "timestamp": datetime.now().timestamp()
            }
        }
        
        # Process the event
        client._handle_event(market_data_event)
        
        # Verify that an event was published to the event engine
        event_engine_call = client.event_engine.put.call_args[0][0]
        assert isinstance(event_engine_call, Event)
        assert event_engine_call.type == EventType.MARKET_DATA
        assert event_engine_call.data["symbol"] == "ETH-USD"
        assert event_engine_call.data["exchange"] == "binance"
        assert len(event_engine_call.data["bids"]) == 2
        assert len(event_engine_call.data["asks"]) == 2
    
    def test_handle_error_event(self, client):
        """Test handling error events from Hummingbot"""
        # Create an error event from Hummingbot
        error_event = {
            "type": "error",
            "data": {
                "message": "Connection lost to exchange",
                "exchange": "binance",
                "timestamp": datetime.now().timestamp()
            }
        }
        
        # Process the event
        client._handle_event(error_event)
        
        # Verify that an event was published to the event engine
        event_engine_call = client.event_engine.put.call_args[0][0]
        assert isinstance(event_engine_call, Event)
        assert event_engine_call.type == EventType.ERROR
        assert "Connection lost" in event_engine_call.data["message"]
        assert event_engine_call.data["exchange"] == "binance"


# Helper for async mocks
class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)
