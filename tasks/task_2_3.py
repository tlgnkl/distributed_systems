import threading
import time
from queue import PriorityQueue
from typing import Dict, List, Tuple

product_types = ["еда", "одежда", "электроника"]

producers_config = [
    {"name": "Фабрика-А", "type": "еда", "count": 3},
    {"name": "Фабрика-Б", "type": "одежда", "count": 4},
    {"name": "Фабрика-В", "type": "электроника", "count": 2},
]

priority_map = {"еда": 1, "электроника": 2, "одежда": 3}

TERMINATION_SENTINEL = (999, None)


def producer(queue: PriorityQueue, name: str, product_type: str, count: int) -> None:
    for index in range(count):
        item = f"{product_type} от {name}-{index}"
        priority = priority_map[product_type]
        queue.put((priority, item))
        print(f"🛠️  {name} произвел: {item} (приоритет {priority})")
        time.sleep(0.2)


def consumer(
    queue: PriorityQueue,
    name: str,
    accepted_types: List[str],
    process_all: bool = False,
) -> None:
    while True:
        priority, item = queue.get()

        if (priority, item) == TERMINATION_SENTINEL:
            queue.task_done()
            break

        product_type = item.split()[0]
        if process_all or product_type in accepted_types:
            print(f"🛒 {name} приобрел: {item} (приоритет {priority})")
            time.sleep(0.4)
        else:
            print(f"⚠️  {name} пропустил: {item} (тип {product_type})")
            # Возвращаем продукт в очередь, чтобы его обработали другие потребители
            queue.put((priority, item))
            time.sleep(0.1)

        queue.task_done()


def main() -> None:
    queue: PriorityQueue[Tuple[int, str]] = PriorityQueue()

    producers: List[threading.Thread] = [
        threading.Thread(
            target=producer,
            args=(queue, cfg["name"], cfg["type"], cfg["count"]),
            name=f"Producer-{cfg['name']}",
        )
        for cfg in producers_config
    ]

    consumers: List[threading.Thread] = [
        threading.Thread(
            target=consumer,
            args=(queue, "Магазин всеядный", product_types),
            kwargs={"process_all": True},
            name="Consumer-Universal",
        ),
        threading.Thread(
            target=consumer,
            args=(queue, "Бутик одежды", ["одежда"]),
            name="Consumer-Clothes",
        ),
    ]

    for thread in producers + consumers:
        thread.start()

    for thread in producers:
        thread.join()

    # Добавляем сигналы завершения для каждого потребителя
    for _ in consumers:
        queue.put(TERMINATION_SENTINEL)

    queue.join()

    for thread in consumers:
        thread.join()

    print("🎉 Производство и продажи завершены")


if __name__ == "__main__":
    main()
