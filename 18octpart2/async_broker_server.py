import asyncio
import json
from collections import defaultdict, deque


class AsyncMessageBroker:
    def __init__(self):
        self.queues = defaultdict(deque)
        self.subscribers = defaultdict(set)
        self.writer_topics = defaultdict(set)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        print(f"Клиент подключен: {addr}")

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                try:
                    message = json.loads(data.decode())
                except json.JSONDecodeError as exc:
                    await self._send(writer, {
                        'status': 'error',
                        'message': f"Invalid JSON: {exc.msg}"
                    })
                    continue

                await self.process_message(message, writer)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"Ошибка обработки клиента {addr}: {exc}")
        finally:
            await self._cleanup_writer(writer)
            print(f"Клиент отключен: {addr}")

    async def process_message(self, message: dict, writer: asyncio.StreamWriter):
        action = message.get('action')
        topic = message.get('topic')

        if action == 'publish':
            await self._handle_publish(topic, message.get('message'), writer)
        elif action == 'subscribe':
            await self._handle_subscribe(topic, writer)
        elif action == 'unsubscribe':
            await self._handle_unsubscribe(topic, writer)
        elif action == 'get':
            await self._handle_get(topic, writer)
        else:
            await self._send(writer, {
                'status': 'error',
                'message': f"Unknown action: {action}"
            })

    async def _handle_publish(self, topic: str, payload, writer: asyncio.StreamWriter):
        if topic is None:
            await self._send(writer, {'status': 'error', 'message': 'Topic is required'})
            return

        self.queues[topic].append(payload)

        await self._send(writer, {'status': 'published', 'topic': topic})
        await self._push_to_subscribers(topic, payload)

    async def _handle_subscribe(self, topic: str, writer: asyncio.StreamWriter):
        if topic is None:
            await self._send(writer, {'status': 'error', 'message': 'Topic is required'})
            return

        self.subscribers[topic].add(writer)
        self.writer_topics[writer].add(topic)

        await self._send(writer, {'status': 'subscribed', 'topic': topic})

        if self.queues[topic]:
            for message in list(self.queues[topic]):
                await self._send(writer, {
                    'type': 'message',
                    'topic': topic,
                    'data': message
                })

    async def _handle_unsubscribe(self, topic: str, writer: asyncio.StreamWriter):
        if topic is None:
            await self._send(writer, {'status': 'error', 'message': 'Topic is required'})
            return

        self.subscribers[topic].discard(writer)
        if writer in self.writer_topics:
            self.writer_topics[writer].discard(topic)

        await self._send(writer, {'status': 'unsubscribed', 'topic': topic})

    async def _handle_get(self, topic: str, writer: asyncio.StreamWriter):
        if topic is None:
            await self._send(writer, {'status': 'error', 'message': 'Topic is required'})
            return

        message = self.queues[topic].popleft() if self.queues[topic] else None
        await self._send(writer, {
            'status': 'ok',
            'topic': topic,
            'data': message
        })

    async def _push_to_subscribers(self, topic: str, payload):
        if topic not in self.subscribers:
            return

        dead_writers = []
        for sub_writer in list(self.subscribers[topic]):
            try:
                await self._send(sub_writer, {
                    'type': 'message',
                    'topic': topic,
                    'data': payload
                })
            except Exception:
                dead_writers.append(sub_writer)

        for writer in dead_writers:
            await self._cleanup_writer(writer)

    async def _send(self, writer: asyncio.StreamWriter, payload: dict):
        data = json.dumps(payload).encode() + b"\n"
        writer.write(data)
        await writer.drain()

    async def _cleanup_writer(self, writer: asyncio.StreamWriter):
        topics = self.writer_topics.pop(writer, set())
        for topic in topics:
            self.subscribers[topic].discard(writer)

        if not writer.is_closing():
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass


async def main(host: str = 'localhost', port: int = 8888):
    broker = AsyncMessageBroker()
    server = await asyncio.start_server(broker.handle_client, host, port)

    addr = server.sockets[0].getsockname()
    print(f"Async broker запущен на {addr}")

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nОстановка брокера")
