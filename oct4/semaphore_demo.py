import random
import threading
import time

# --- Конфигурация синхронизации и общие структуры ---------------------------------

# Создание семафора с начальным значением 3
semaphore = threading.Semaphore(3)

# Текущие активные работники, защищенные мьютексом
active_workers = []
active_lock = threading.Lock()


def timestamp() -> str:
    """Возвращает человекочитаемое время для логов."""
    return time.strftime("%H:%M:%S")


def snapshot_active():
    """Создает снимок текущего списка активных потоков."""
    with active_lock:
        return sorted(active_workers)


def worker(worker_id):
    """Функция рабочего потока"""
    # Фиксируем начало ожидания, чтобы вычислить длительность блокировки.
    request_start = time.perf_counter()
    print(f"[{timestamp()}] Работник {worker_id}: просит доступ (активные: {snapshot_active()})")

    # Пытаемся получить семафор мгновенно, чтобы логировать попадание в очередь.
    acquired_immediately = semaphore.acquire(blocking=False)
    if not acquired_immediately:
        print(f"[{timestamp()}] Работник {worker_id}: в очереди (активные: {snapshot_active()})")
        semaphore.acquire()

    # Сколько времени поток провел, ожидая разрешения от семафора.
    wait_time = time.perf_counter() - request_start

    # Регистрируем поток в списке активных, чтобы выводить текущую картину.
    with active_lock:
        active_workers.append(worker_id)
        current_active = sorted(active_workers)

    print(
        f"[{timestamp()}] Работник {worker_id}: получил доступ "
        f"(ждал {wait_time:.2f} с). Активные: {current_active}"
    )

    # Имитируем произвольную нагрузку в критической секции.
    work_time = random.uniform(1, 3)
    time.sleep(work_time)
    print(
        f"[{timestamp()}] Работник {worker_id}: завершил работу "
        f"(работал {work_time:.2f} с)"
    )

    # Удаляем поток из активного списка и освобождаем слот в семафоре.
    with active_lock:
        active_workers.remove(worker_id)
        remaining = sorted(active_workers)

    semaphore.release()
    print(
        f"[{timestamp()}] Работник {worker_id}: освободил доступ "
        f"(остались: {remaining})"
    )


def launch_workers(total: int, delay: float = 0.0):
    """Создает и запускает `total` потоков с опциональной задержкой между стартами."""
    threads = []
    for worker_id in range(total):
        thread = threading.Thread(target=worker, args=(worker_id,))
        threads.append(thread)
        thread.start()
        if delay:
            time.sleep(delay)
    return threads


if __name__ == "__main__":
    capacity = 3
    total_workers = 10
    # Заголовок запуска, фиксируем время и глобальные параметры.
    start_time = timestamp()
    print(
        f"[{start_time}] 🚀 Запускаем {total_workers} работников с лимитом {capacity} "
        "одновременных доступов\n"
    )

    # Стартуем потоков с небольшим смещением по времени, чтобы лог выглядел плавнее.
    threads = launch_workers(total_workers, delay=0.1)

    # Ждем завершения всех потоков перед финальным сообщением.
    for thread in threads:
        thread.join()

    print(f"[{timestamp()}] 🎉 Все работы завершены!")
