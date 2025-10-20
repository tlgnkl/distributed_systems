import asyncio
import json


class SimpleBroker:
    def __init__(self):
        self.queues = {}
        self.subscribers = {}

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"Новый клиент: {addr}")

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                message = json.loads(data.decode())
                await self.process_message(message, writer)

        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            for topic, writers in self.subscribers.items():
                if writer in writers:
                    writers.remove(writer)
            writer.close()
            await writer.wait_closed()

    async def process_message(self, message, writer):
        action = message.get('action')
        topic = message.get('topic')

        if action == 'publish':
            if topic not in self.queues:
                self.queues[topic] = []
            self.queues[topic].append(message['message'])

            if topic in self.subscribers:
                for sub_writer in self.subscribers[topic]:
                    try:
                        response = {'type': 'message', 'data': message['message']}
                        sub_writer.write(json.dumps(response).encode() + b"\n")
                        await sub_writer.drain()
                    except Exception:
                        pass

            response = {'status': 'ok'}

        elif action == 'subscribe':
            if topic not in self.subscribers:
                self.subscribers[topic] = []
            self.subscribers[topic].append(writer)

            if topic in self.queues:
                for msg in self.queues[topic]:
                    response = {'type': 'message', 'data': msg}
                    writer.write(json.dumps(response).encode() + b"\n")
                    await writer.drain()

            response = {'status': 'subscribed'}

        elif action == 'get':
            if topic in self.queues and self.queues[topic]:
                msg = self.queues[topic].pop(0)
                response = {'status': 'ok', 'data': msg}
            else:
                response = {'status': 'no_messages'}

        else:
            response = {'status': 'error', 'message': 'Unknown action'}

        writer.write(json.dumps(response).encode() + b"\n")
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
