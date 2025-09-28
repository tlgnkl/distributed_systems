import threading
import time
from typing import Callable, List

MAX_BALANCE = 500
COMMISSION = 1


class BankAccount:
    def __init__(self, initial_balance: int = 100):
        self.balance = initial_balance
        self.max_balance = MAX_BALANCE
        self.lock = threading.Lock()
        self.history: List[str] = []
        self.history_lock = threading.Lock()

    def _log(self, message: str) -> None:
        with self.history_lock:
            self.history.append(message)

    def withdraw(self, amount: int) -> None:
        total = amount + COMMISSION
        with self.lock:
            if self.balance >= total:
                time.sleep(0.1)
                self.balance -= total
                self._log(f"Снятие {amount} + комиссия {COMMISSION}")
                print(
                    f"Снятие {amount} + комиссия {COMMISSION}. Остаток: {self.balance}"
                )
            else:
                self._log(
                    f"Отказ в снятии {amount} (комиссия {COMMISSION}) — недостаточно средств"
                )
                print(
                    f"Недостаточно средств для снятия {amount} с комиссией {COMMISSION}."
                )

    def deposit(self, amount: int) -> None:
        with self.lock:
            if self.balance + amount > self.max_balance:
                allowed = self.max_balance - self.balance
                self._log(
                    f"Отказ в пополнении {amount}: превышение лимита (доступно {allowed})"
                )
                print(
                    f"Пополнение {amount} отклонено: превышение лимита. Доступно {allowed}."
                )
                return

            time.sleep(0.1)
            self.balance += amount
            self._log(f"Пополнение {amount}")
            print(f"Пополнение {amount}. Текущий баланс: {self.balance}")



def withdraw_worker(account: BankAccount, amount: int, repeat: int) -> None:
    for _ in range(repeat):
        account.withdraw(amount)


def deposit_worker(account: BankAccount, amount: int, repeat: int) -> None:
    for _ in range(repeat):
        account.deposit(amount)


def run_scenario() -> BankAccount:
    account = BankAccount()

    threads: List[threading.Thread] = [
        threading.Thread(target=withdraw_worker, args=(account, 30, 3), name="Withdraw-1"),
        threading.Thread(target=withdraw_worker, args=(account, 25, 3), name="Withdraw-2"),
        threading.Thread(target=deposit_worker, args=(account, 40, 4), name="Deposit-1"),
        threading.Thread(target=deposit_worker, args=(account, 50, 4), name="Deposit-2"),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    return account


def main() -> None:
    account = run_scenario()

    print("\nИстория операций:")
    for entry in account.history:
        print(f"- {entry}")

    print(f"\nИтоговый баланс: {account.balance}")


if __name__ == "__main__":
    main()
