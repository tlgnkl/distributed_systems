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

        self.writer.write(json.dumps(data).encode() + b"\n")
        await self.writer.drain()

        response_data = await self.reader.readline()
        if not response_data:
            raise ConnectionError("Нет ответа от сервера")
        return json.loads(response_data.decode())

    async def listen_messages(self):
        try:
            while True:
                data = await self.reader.readline()
                if data:
                    message = json.loads(data.decode())
                    if message.get('type') == 'message':
                        print(f"Получено сообщение: {message['data']}")
        except Exception:
            pass


async def example_producer():
    client = SimpleClient()
    await client.connect()

    for i in range(3):
        message = f"Привет мир #{i}"
        result = await client.send_message('publish', 'test', message)
        print(f"Отправили: {message} -> {result}")
        await asyncio.sleep(1)

    client.writer.close()
    await client.writer.wait_closed()


async def example_consumer():
    client = SimpleClient()
    await client.connect()

    await client.send_message('subscribe', 'test')
    print("Подписались на топик 'test'")

    await client.listen_messages()


async def example_get():
    client = SimpleClient()
    await client.connect()

    result = await client.send_message('get', 'test')
    print(f"Получили сообщение: {result}")

    client.writer.close()
    await client.writer.wait_closed()


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
