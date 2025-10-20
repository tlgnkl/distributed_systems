import asyncio
import contextlib
import json
from typing import Callable, Awaitable, Optional, Union


class AsyncMessageClient:
    Handler = Callable[[dict], Union[Awaitable[None], None]]

    def __init__(self, host: str = 'localhost', port: int = 8888):
        self.host = host
        self.port = port
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self._response_queue: asyncio.Queue = asyncio.Queue()
        self._handlers: list[AsyncMessageClient.Handler] = []
        self._listen_task: Optional[asyncio.Task] = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        self._listen_task = asyncio.create_task(self._listen())

    async def disconnect(self):
        if self.writer and not self.writer.is_closing():
            self.writer.close()
            await self.writer.wait_closed()

        if self._listen_task:
            self._listen_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listen_task

    def add_handler(self, handler: Handler) -> None:
        self._handlers.append(handler)

    async def publish(self, topic: str, message):
        request = {
            'action': 'publish',
            'topic': topic,
            'message': message
        }
        return await self._send_request(request)

    async def subscribe(self, topic: str):
        request = {'action': 'subscribe', 'topic': topic}
        return await self._send_request(request)

    async def unsubscribe(self, topic: str):
        request = {'action': 'unsubscribe', 'topic': topic}
        return await self._send_request(request)

    async def get(self, topic: str):
        request = {'action': 'get', 'topic': topic}
        return await self._send_request(request)

    async def _send_request(self, payload: dict):
        if not self.writer:
            raise ConnectionError('Client is not connected')

        data = json.dumps(payload).encode() + b"\n"
        self.writer.write(data)
        await self.writer.drain()
        return await self._response_queue.get()

    async def _listen(self):
        try:
            while True:
                data = await self.reader.readline()
                if not data:
                    break

                message = json.loads(data.decode())
                if message.get('type') == 'message':
                    await self._dispatch_push(message)
                else:
                    await self._response_queue.put(message)
        except asyncio.CancelledError:
            raise
        finally:
            await self._response_queue.put({'status': 'disconnected'})

    async def _dispatch_push(self, message: dict):
        for handler in self._handlers:
            result = handler(message)
            if asyncio.iscoroutine(result):
                await result


async def demo_producer():
    client = AsyncMessageClient()
    await client.connect()

    try:
        for idx in range(3):
            payload = {'id': idx, 'text': f'Message #{idx}'}
            response = await client.publish('news', payload)
            print(f'Producer -> {response}')
            await asyncio.sleep(0.5)
    finally:
        await client.disconnect()


def _print_handler(message: dict):
    data = message['data']
    print(f"Consumer получил: [{message['topic']}] {data}")


async def demo_consumer():
    client = AsyncMessageClient()
    client.add_handler(_print_handler)
    await client.connect()

    try:
        response = await client.subscribe('news')
        print(f'Consumer subscribe -> {response}')
        await asyncio.sleep(5)
    finally:
        await client.disconnect()


async def demo_get():
    client = AsyncMessageClient()
    await client.connect()

    try:
        response = await client.get('news')
        print(f'Get -> {response}')
    finally:
        await client.disconnect()


async def main():
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = 'consumer'

    if mode == 'producer':
        await demo_producer()
    elif mode == 'consumer':
        await demo_consumer()
    elif mode == 'get':
        await demo_get()
    else:
        print('Использование: python async_message_client.py [producer|consumer|get]')


if __name__ == '__main__':
    asyncio.run(main())
