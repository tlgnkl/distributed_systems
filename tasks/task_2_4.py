import random
import threading
import time
from typing import List, Tuple

FILES: List[Tuple[str, float]] = [
    ("document.pdf", 2.5),
    ("image.jpg", 1.8),
    ("video.mp4", 3.0),
    ("music.mp3", 2.2),
    ("archive.zip", 2.7),
    ("presentation.pptx", 2.4),
]

BAR_WIDTH = 20
UPDATE_INTERVAL = 0.2
MAX_SIMULTANEOUS_DOWNLOADS = 3

download_semaphore = threading.Semaphore(MAX_SIMULTANEOUS_DOWNLOADS)
active_downloads = 0
active_lock = threading.Lock()

def format_progress(percent: float) -> str:
    filled = int(percent / 100 * BAR_WIDTH)
    empty = BAR_WIDTH - filled
    bar = "[" + "#" * filled + "_" * empty + "]"
    return f"{bar} {percent:5.1f}%"

def download_file(filename: str, size: float) -> None:
    total_time = random.uniform(1.5, 3.5) * (size / 2.5)
    start_time = time.time()

    download_semaphore.acquire()
    try:
        global active_downloads
        with active_lock:
            active_downloads += 1
            current = active_downloads
        print(
            f"📥 Начата загрузка {filename}. Скачивается {current} из {MAX_SIMULTANEOUS_DOWNLOADS} допустимых."
        )

        while True:
            elapsed = time.time() - start_time
            if elapsed >= total_time:
                break
            percent = min(100.0, (elapsed / total_time) * 100)
            progress = format_progress(percent)
            print(f"{filename}: {progress} ({elapsed:4.1f}/{total_time:4.1f} c)")
            time.sleep(UPDATE_INTERVAL)

        # Финальное обновление
        percent = 100.0
        progress = format_progress(percent)
        print(f"✅ Завершена загрузка {filename}: {progress} за {total_time:4.1f} c")
    finally:
        with active_lock:
            active_downloads -= 1
            current = active_downloads
        print(
            f"📤 Завершена обработка {filename}. Активных загрузок: {current}."
        )
        download_semaphore.release()

def main() -> None:
    print("🚀 Запуск менеджера загрузок")
    threads: List[threading.Thread] = []

    for filename, size in FILES:
        thread = threading.Thread(target=download_file, args=(filename, size), name=f"Downloader-{filename}")
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print("🏁 Все загрузки завершены")

if __name__ == "__main__":
    main()
