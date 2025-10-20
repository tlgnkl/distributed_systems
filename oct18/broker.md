

## Упрощенный сервер брокера

```python
# simple_server.py
import asyncio
import json

class SimpleBroker:
    def __init__(self):
        self.queues = {}  # топик -> список сообщений
        self.subscribers = {}  # топик -> список подключений
        
    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"Новый клиент: {addr}")
        
        try:
            while True:
                data = await reader.read(100)
                if not data:
                    break
                    
                message = json.loads(data.decode())
                await self.process_message(message, writer)
                
        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            writer.close()
    
    async def process_message(self, message, writer):
        action = message.get('action')
        topic = message.get('topic')
        
        if action == 'publish':
            # Сохраняем сообщение
            if topic not in self.queues:
                self.queues[topic] = []
            self.queues[topic].append(message['message'])
            
            # Отправляем всем подписчикам
            if topic in self.subscribers:
                for sub_writer in self.subscribers[topic]:
                    try:
                        response = {'type': 'message', 'data': message['message']}
                        sub_writer.write(json.dumps(response).encode())
                        await sub_writer.drain()
                    except:
                        pass
            
            response = {'status': 'ok'}
            
        elif action == 'subscribe':
            # Добавляем в подписчики
            if topic not in self.subscribers:
                self.subscribers[topic] = []
            self.subscribers[topic].append(writer)
            
            # Отправляем старые сообщения
            if topic in self.queues:
                for msg in self.queues[topic]:
                    response = {'type': 'message', 'data': msg}
                    writer.write(json.dumps(response).encode())
                    await writer.drain()
            
            response = {'status': 'subscribed'}
            
        elif action == 'get':
            # Получаем одно сообщение
            if topic in self.queues and self.queues[topic]:
                msg = self.queues[topic].pop(0)
                response = {'status': 'ok', 'data': msg}
            else:
                response = {'status': 'no_messages'}
        
        else:
            response = {'status': 'error', 'message': 'Unknown action'}
        
        # Отправляем ответ
        writer.write(json.dumps(response).encode())
        await writer.drain()

async def main():
    broker = SimpleBroker()
    server = await asyncio.start_server(
        broker.handle_client, 'localhost', 8888
    )
    
    print("Сервер запущен на localhost:8888")
    
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
```

## Упрощенный клиент

```python
# simple_client.py
import asyncio
import json

class SimpleClient:
    def __init__(self):
        self.reader = None
        self.writer = None
    
    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(
            'localhost', 8888
        )
        print("Подключились к серверу")
    
    async def send_message(self, action, topic, message=None):
        data = {'action': action, 'topic': topic}
        if message:
            data['message'] = message
        
        self.writer.write(json.dumps(data).encode())
        await self.writer.drain()
        
        # Ждем ответ
        response_data = await self.reader.read(100)
        return json.loads(response_data.decode())
    
    async def listen_messages(self):
        """Слушаем входящие сообщения"""
        try:
            while True:
                data = await self.reader.read(100)
                if data:
                    message = json.loads(data.decode())
                    if message.get('type') == 'message':
                        print(f"Получено сообщение: {message['data']}")
        except:
            pass

# Примеры использования
async def example_producer():
    """Простой производитель"""
    client = SimpleClient()
    await client.connect()
    
    for i in range(3):
        message = f"Привет мир #{i}"
        result = await client.send_message('publish', 'test', message)
        print(f"Отправили: {message} -> {result}")
        await asyncio.sleep(1)
    
    client.writer.close()

async def example_consumer():
    """Простой потребитель"""
    client = SimpleClient()
    await client.connect()
    
    # Подписываемся
    await client.send_message('subscribe', 'test')
    print("Подписались на топик 'test'")
    
    # Слушаем сообщения
    await client.listen_messages()

async def example_get():
    """Получение одного сообщения"""
    client = SimpleClient()
    await client.connect()
    
    result = await client.send_message('get', 'test')
    print(f"Получили сообщение: {result}")
    
    client.writer.close()

# Запуск примеров
async def main():
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'producer':
            await example_producer()
        elif sys.argv[1] == 'consumer':
            await example_consumer()
        elif sys.argv[1] == 'get':
            await example_get()
    else:
        print("Использование:")
        print("  python simple_client.py producer - отправить сообщения")
        print("  python simple_client.py consumer - получать сообщения")
        print("  python simple_client.py get - получить одно сообщение")

if __name__ == "__main__":
    asyncio.run(main())
```

## Самый простой пример "в одном файле"

```python
# simplest_broker.py
import asyncio
import json

# Хранилище сообщений
messages = {'test': []}
subscribers = {'test': []}

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"Клиент подключен: {addr}")
    
    try:
        while True:
            data = await reader.read(100)
            if not data:
                break
            
            # Парсим сообщение
            msg = json.loads(data.decode())
            action = msg.get('action')
            
            if action == 'send':
                # Сохраняем сообщение
                text = msg['text']
                messages['test'].append(text)
                print(f"Сохранили: {text}")
                
                # Отправляем всем подписчикам
                for sub in subscribers['test']:
                    sub.write(json.dumps({'new_message': text}).encode())
                    await sub.drain()
                
                # Ответ отправителю
                writer.write(b'{"status": "sent"}')
                
            elif action == 'get':
                # Отдаем все сообщения
                if messages['test']:
                    response = {'messages': messages['test']}
                    writer.write(json.dumps(response).encode())
                else:
                    writer.write(b'{"messages": []}')
                    
            elif action == 'listen':
                # Добавляем в подписчики
                subscribers['test'].append(writer)
                writer.write(b'{"status": "listening"}')
                # Не закрываем соединение - ждем новые сообщения
                continue
                
            await writer.drain()
            
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        if writer in subscribers['test']:
            subscribers['test'].remove(writer)
        writer.close()
        print(f"Клиент отключен: {addr}")

async def main():
    server = await asyncio.start_server(handle_client, 'localhost', 8888)
    print("Сервер запущен! Подключение: telnet localhost 8888")
    
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
```

## Простой тестовый клиент

```python
# test_client.py
import asyncio
import json

async def test_client():
    reader, writer = await asyncio.open_connection('localhost', 8888)
    
    # Отправляем сообщение
    message = {'action': 'send', 'text': 'Тестовое сообщение'}
    writer.write(json.dumps(message).encode())
    await writer.drain()
    
    # Получаем ответ
    data = await reader.read(100)
    print(f"Ответ: {data.decode()}")
    
    # Получаем все сообщения
    message = {'action': 'get'}
    writer.write(json.dumps(message).encode())
    await writer.drain()
    
    data = await reader.read(100)
    print(f"Все сообщения: {data.decode()}")
    
    writer.close()

async def listen_messages():
    """Слушаем новые сообщения"""
    reader, writer = await asyncio.open_connection('localhost', 8888)
    
    # Подписываемся
    message = {'action': 'listen'}
    writer.write(json.dumps(message).encode())
    await writer.drain()
    
    print("Слушаем сообщения...")
    
    try:
        while True:
            data = await reader.read(100)
            if data:
                print(f"Новое сообщение: {data.decode()}")
    except:
        pass

# Запуск
async def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'listen':
        await listen_messages()
    else:
        await test_client()

asyncio.run(main())
```

## Как тестировать:

1. **Запустите сервер:**
```bash
python simplest_broker.py
```

2. **Отправьте сообщение:**
```bash
python test_client.py
```

3. **Слушайте сообщения (в отдельном окне):**
```bash
python test_client.py listen
```

4. **Или используйте telnet для ручного тестирования:**
```bash
telnet localhost 8888
```
Затем введите JSON:
```json
{"action": "send", "text": "Привет"}
{"action": "get"}
{"action": "listen"}
```

## Что делает этот упрощенный код:

1. **Сервер** хранит сообщения в памяти
2. **Три основных действия:**
   - `send` - отправить сообщение
   - `get` - получить все сообщения  
   - `listen` - подписаться на новые сообщения
3. **Автоматическая рассылка** новым подписчикам
4. **Минимальная обработка ошибок**

# Домашнее задание по созданию брокера сообщений для учебных целей

В этом руководстве мы создадим простой асинхронный брокер сообщений на Python, используя возможности asyncio и сокетов.

## Содержание
1. [Что такое брокер сообщений?](#что-такое-брокер-сообщений)
2. [Архитектура системы](#архитектура-системы)
3. [Реализация сервера-брокера](#реализация-сервера-брокера)
4. [Реализация клиента](#реализация-клиента)
5. [Протокол обмена сообщениями](#протокол-обмена-сообщениями)
6. [Пример использования](#пример-использования)
7. [Дальнейшее развитие](#дальнейшее-развитие)

## Что такое брокер сообщений?

Брокер сообщений - это промежуточное программное обеспечение, которое обеспечивает обмен сообщениями между различными компонентами системы. Он действует как "почтовое отделение" - принимает сообщения от отправителей и доставляет их получателям.

Основные концепции:
- **Producer (Продюсер)** - отправляет сообщения
- **Consumer (Консьюмер)** - получает сообщения  
- **Queue (Очередь)** - временное хранилище сообщений
- **Topic (Топик)** - категория/канал для сообщений

## Архитектура системы

```
┌─────────────┐    сообщения    ┌─────────────┐
│   Клиент A  │ ──────────────> │   Сервер-   │
│ (Producer)  │                 │   брокер    │
└─────────────┘                 └─────────────┘
                                      │
                                      │ сообщения
                                      ▼
┌─────────────┐                 ┌─────────────┐
│   Клиент B  │ <───────────────┤   Очередь   │
│ (Consumer)  │                 │  сообщений  │
└─────────────┘                 └─────────────┘
```

## Реализация сервера-брокера

```python
# server.py
import asyncio
import json
import logging
from collections import defaultdict, deque
from typing import Dict, Set, Deque

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MessageBroker")

class MessageBroker:
    def __init__(self):
        # Очереди для разных топиков
        self.queues: Dict[str, Deque[dict]] = defaultdict(deque)
        # Подписчики на топики
        self.subscribers: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        # Максимальный размер очереди
        self.max_queue_size = 1000
        
    async def publish(self, topic: str, message: dict) -> bool:
        """Публикация сообщения в топик"""
        if len(self.queues[topic]) >= self.max_queue_size:
            logger.warning(f"Queue for topic '{topic}' is full")
            return False
            
        self.queues[topic].append(message)
        logger.info(f"Published message to topic '{topic}': {message}")
        
        # Уведомляем всех подписчиков
        if self.subscribers[topic]:
            for subscriber_queue in list(self.subscribers[topic]):
                try:
                    await subscriber_queue.put(message)
                except Exception as e:
                    logger.error(f"Error notifying subscriber: {e}")
                    self.subscribers[topic].remove(subscriber_queue)
        
        return True
    
    async def subscribe(self, topic: str) -> asyncio.Queue:
        """Подписка на топик"""
        queue = asyncio.Queue()
        self.subscribers[topic].add(queue)
        logger.info(f"New subscription to topic '{topic}'")
        
        # Отправляем историю сообщений новому подписчику
        for message in list(self.queues[topic]):
            await queue.put(message)
            
        return queue
    
    def unsubscribe(self, topic: str, queue: asyncio.Queue):
        """Отписка от топика"""
        if queue in self.subscribers[topic]:
            self.subscribers[topic].remove(queue)
            logger.info(f"Unsubscribed from topic '{topic}'")
    
    async def get_message(self, topic: str) -> dict:
        """Получение сообщения из топика (если есть)"""
        if self.queues[topic]:
            return self.queues[topic].popleft()
        return None

class BrokerServer:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.broker = MessageBroker()
        self.clients = set()
        
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Обработка подключения клиента"""
        client_addr = writer.get_extra_info('peername')
        logger.info(f"New client connected: {client_addr}")
        self.clients.add(writer)
        
        try:
            while True:
                # Чтение данных от клиента
                data = await reader.read(1024)
                if not data:
                    break
                    
                # Обработка сообщения
                await self.process_message(data, writer)
                
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            self.clients.remove(writer)
            writer.close()
            await writer.wait_closed()
            logger.info(f"Client disconnected: {client_addr}")
    
    async def process_message(self, data: bytes, writer: asyncio.StreamWriter):
        """Обработка входящего сообщения"""
        try:
            message = json.loads(data.decode())
            action = message.get('action')
            
            if action == 'publish':
                # Публикация сообщения
                topic = message['topic']
                msg_data = message['message']
                success = await self.broker.publish(topic, msg_data)
                
                response = {
                    'status': 'success' if success else 'error',
                    'message': 'Published' if success else 'Queue full'
                }
                
            elif action == 'subscribe':
                # Подписка на топик
                topic = message['topic']
                queue = await self.broker.subscribe(topic)
                
                # Асинхронная отправка сообщений подписчику
                asyncio.create_task(self.push_messages_to_subscriber(queue, writer, topic))
                
                response = {'status': 'success', 'message': 'Subscribed'}
                
            elif action == 'get':
                # Получение одного сообщения
                topic = message['topic']
                msg = await self.broker.get_message(topic)
                response = {
                    'status': 'success', 
                    'message': msg if msg else 'No messages'
                }
                
            else:
                response = {'status': 'error', 'message': 'Unknown action'}
                
            # Отправка ответа клиенту
            await self.send_response(response, writer)
            
        except json.JSONDecodeError:
            error_response = {'status': 'error', 'message': 'Invalid JSON'}
            await self.send_response(error_response, writer)
        except Exception as e:
            error_response = {'status': 'error', 'message': str(e)}
            await self.send_response(error_response, writer)
    
    async def push_messages_to_subscriber(self, queue: asyncio.Queue, writer: asyncio.StreamWriter, topic: str):
        """Отправка сообщений подписчику в реальном времени"""
        try:
            while True:
                message = await queue.get()
                push_message = {
                    'type': 'push',
                    'topic': topic,
                    'message': message
                }
                await self.send_response(push_message, writer)
        except Exception as e:
            logger.error(f"Error pushing messages to subscriber: {e}")
            self.broker.unsubscribe(topic, queue)
    
    async def send_response(self, response: dict, writer: asyncio.StreamWriter):
        """Отправка ответа клиенту"""
        try:
            data = json.dumps(response).encode()
            writer.write(data + b'\n')
            await writer.drain()
        except Exception as e:
            logger.error(f"Error sending response: {e}")
    
    async def run(self):
        """Запуск сервера"""
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        
        addr = server.sockets[0].getsockname()
        logger.info(f'Message broker server running on {addr}')
        
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    broker_server = BrokerServer()
    asyncio.run(broker_server.run())
```

## Реализация клиента

```python
# client.py
import asyncio
import json
import logging
from typing import Callable, Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MessageClient")

class MessageClient:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.is_connected = False
        self.message_handlers = []
        
    async def connect(self):
        """Подключение к серверу"""
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port
            )
            self.is_connected = True
            logger.info(f"Connected to message broker at {self.host}:{self.port}")
            
            # Запуск прослушивания входящих сообщений
            asyncio.create_task(self._listen_for_messages())
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    async def disconnect(self):
        """Отключение от сервера"""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.is_connected = False
        logger.info("Disconnected from message broker")
    
    async def publish(self, topic: str, message: dict) -> dict:
        """Публикация сообщения в топик"""
        request = {
            'action': 'publish',
            'topic': topic,
            'message': message
        }
        return await self._send_request(request)
    
    async def subscribe(self, topic: str):
        """Подписка на топик"""
        request = {
            'action': 'subscribe',
            'topic': topic
        }
        return await self._send_request(request)
    
    async def get_message(self, topic: str) -> dict:
        """Получение одного сообщения из топика"""
        request = {
            'action': 'get',
            'topic': topic
        }
        return await self._send_request(request)
    
    async def _send_request(self, request: dict) -> dict:
        """Отправка запроса на сервер"""
        if not self.is_connected:
            raise ConnectionError("Not connected to server")
            
        try:
            data = json.dumps(request).encode()
            self.writer.write(data + b'\n')
            await self.writer.drain()
            
            # Ждем ответа (ответ придет через _listen_for_messages)
            response = await self._wait_for_response()
            return response
            
        except Exception as e:
            logger.error(f"Error sending request: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def _wait_for_response(self) -> dict:
        """Ожидание ответа от сервера"""
        # В реальной реализации здесь должна быть более сложная логика
        # сопоставления запросов и ответов
        await asyncio.sleep(0.1)
        return {'status': 'unknown'}
    
    async def _listen_for_messages(self):
        """Прослушивание входящих сообщений от сервера"""
        try:
            while self.is_connected:
                data = await self.reader.readuntil(b'\n')
                if not data:
                    break
                    
                message = json.loads(data.decode().strip())
                await self._handle_incoming_message(message)
                
        except asyncio.IncompleteReadError:
            # Клиент отключился
            pass
        except Exception as e:
            logger.error(f"Error listening for messages: {e}")
        finally:
            self.is_connected = False
    
    async def _handle_incoming_message(self, message: dict):
        """Обработка входящего сообщения"""
        if message.get('type') == 'push':
            # Это push-уведомление от сервера
            logger.info(f"Received push message: {message}")
            for handler in self.message_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        handler(message)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")
        else:
            # Это ответ на запрос
            logger.info(f"Received response: {message}")
    
    def add_message_handler(self, handler: Callable):
        """Добавление обработчика входящих сообщений"""
        self.message_handlers.append(handler)

# Пример использования клиента
async def example_producer():
    """Пример производителя сообщений"""
    client = MessageClient()
    await client.connect()
    
    try:
        for i in range(5):
            message = {
                'id': i,
                'text': f'Hello from producer! Message #{i}',
                'timestamp': asyncio.get_event_loop().time()
            }
            result = await client.publish('test_topic', message)
            logger.info(f"Publish result: {result}")
            await asyncio.sleep(1)
    finally:
        await client.disconnect()

async def example_consumer():
    """Пример потребителя сообщений"""
    client = MessageClient()
    await client.connect()
    
    # Обработчик входящих сообщений
    def handle_message(message):
        logger.info(f"Consumer received: {message}")
    
    client.add_message_handler(handle_message)
    
    try:
        # Подписываемся на топик
        result = await client.subscribe('test_topic')
        logger.info(f"Subscribe result: {result}")
        
        # Ждем сообщения
        logger.info("Waiting for messages...")
        await asyncio.sleep(10)
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    # Запуск примера
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'producer':
        asyncio.run(example_producer())
    else:
        asyncio.run(example_consumer())
```

## Протокол обмена сообщениями

### Формат сообщений

**Запрос от клиента:**
```json
{
  "action": "publish|subscribe|get",
  "topic": "название_топика",
  "message": { ... }  // только для action=publish
}
```

**Ответ от сервера:**
```json
{
  "status": "success|error",
  "message": "текст сообщения или данные"
}
```

**Push-уведомление:**
```json
{
  "type": "push",
  "topic": "название_топика", 
  "message": { ... }
}
```

### Примеры взаимодействия

1. **Публикация сообщения:**
```python
request = {
    "action": "publish",
    "topic": "news",
    "message": {"title": "Новость", "content": "Текст новости"}
}
```

2. **Подписка на топик:**
```python
request = {
    "action": "subscribe", 
    "topic": "news"
}
```

3. **Получение сообщения:**
```python
request = {
    "action": "get",
    "topic": "news"
}
```

## Пример использования

### Запуск системы

1. **Запуск сервера:**
```bash
python server.py
```

2. **Запуск производителя:**
```bash
python client.py producer
```

3. **Запуск потребителя:**
```bash
python client.py consumer
```

### Расширенный пример использования

```python
# advanced_example.py
import asyncio
from client import MessageClient
import random
import time

async def stock_price_producer():
    """Производитель цен на акции"""
    client = MessageClient()
    await client.connect()
    
    stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
    
    try:
        while True:
            for stock in stocks:
                price = round(random.uniform(100, 500), 2)
                change = round(random.uniform(-10, 10), 2)
                
                message = {
                    'symbol': stock,
                    'price': price,
                    'change': change,
                    'timestamp': time.time()
                }
                
                await client.publish('stock_prices', message)
                await asyncio.sleep(0.5)
                
    except KeyboardInterrupt:
        print("Producer stopped")
    finally:
        await client.disconnect()

async def stock_price_consumer():
    """Потребитель цен на акции"""
    client = MessageClient()
    await client.connect()
    
    def handle_stock_message(message):
        if message.get('type') == 'push':
            data = message['message']
            symbol = data['symbol']
            price = data['price']
            change = data['change']
            
            arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
            print(f"{symbol}: ${price} {arrow} {abs(change):.2f}")
    
    client.add_message_handler(handle_stock_message)
    
    try:
        await client.subscribe('stock_prices')
        print("Subscribed to stock prices. Press Ctrl+C to stop.")
        await asyncio.Future()  # Бесконечное ожидание
    except KeyboardInterrupt:
        print("Consumer stopped")
    finally:
        await client.disconnect()

async def chat_user(username: str):
    """Пользователь чата"""
    client = MessageClient()
    await client.connect()
    
    def handle_chat_message(message):
        if message.get('type') == 'push':
            data = message['message']
            if data['user'] != username:  # Не показываем свои сообщения
                print(f"\n[{data['user']}]: {data['text']}")
    
    client.add_message_handler(handle_chat_message)
    await client.subscribe('chat_room')
    
    try:
        print(f"Chat started as '{username}'. Type messages or 'quit' to exit.")
        
        while True:
            text = await asyncio.get_event_loop().run_in_executor(
                None, input, f"[{username}]: "
            )
            
            if text.lower() == 'quit':
                break
                
            message = {
                'user': username,
                'text': text,
                'timestamp': time.time()
            }
            
            await client.publish('chat_room', message)
            
    finally:
        await client.disconnect()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'stock_producer':
            asyncio.run(stock_price_producer())
        elif sys.argv[1] == 'stock_consumer':
            asyncio.run(stock_price_consumer())
        elif sys.argv[1] == 'chat' and len(sys.argv) > 2:
            asyncio.run(chat_user(sys.argv[2]))
        else:
            print("Usage:")
            print("  python advanced_example.py stock_producer")
            print("  python advanced_example.py stock_consumer") 
            print("  python advanced_example.py chat <username>")
    else:
        print("Please specify a mode")
```

## Дальнейшее развитие

Этот простой брокер сообщений можно улучшить следующими способами:

1. **Авторизация и аутентификация**
2. **Сохраняемость сообщений** (запись в базу данных)
3. **Кластеризация** для горизонтального масштабирования
4. **Поддержка различных паттернов** (pub/sub, point-to-point, request/reply)
5. **Поддержка качества обслуживания** (доставка "точно один раз", приоритеты)
6. **Мониторинг и метрики**
7. **Поддержка различных форматов сообщений** (Protobuf, Avro)

Это руководство демонстрирует основные принципы работы брокеров сообщений и дает хорошую основу для понимания более сложных систем обмена сообщениями.