import threading
import time

# Цвета ANSI
COLORS = ["\033[91m", "\033[92m", "\033[93m", "\033[94m"]
RESET_COLOR = "\033[0m"

START_NUMBER = 5
LETTERS = "EDCBA"


def print_numbers(color: str, thread_id: int, start_number: int) -> None:
    for value in range(start_number, 0, -1):
        print(f"{color}Поток-{thread_id}: число {value}{RESET_COLOR}")
        time.sleep(1)
    print(f"{color}Поток-{thread_id} завершен!{RESET_COLOR}")


def print_letters(color: str, thread_id: int, letters: str) -> None:
    for letter in letters:
        print(f"{color}Поток-{thread_id}: буква {letter}{RESET_COLOR}")
        time.sleep(1)
    print(f"{color}Поток-{thread_id} завершен!{RESET_COLOR}")


def main() -> None:
    threads: list[threading.Thread] = []

    # Два потока работают с числами, два с буквами
    workers = [
        (print_numbers, START_NUMBER),
        (print_letters, LETTERS),
        (print_numbers, START_NUMBER),
        (print_letters, LETTERS),
    ]

    for idx, (worker, payload) in enumerate(workers):
        color = COLORS[idx % len(COLORS)]
        thread_id = idx + 1
        if worker is print_numbers:
            args = (color, thread_id, payload)
        else:
            args = (color, thread_id, payload)
        thread = threading.Thread(target=worker, args=args)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
