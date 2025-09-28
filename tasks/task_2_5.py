import random
import threading
import time
from collections import defaultdict
from typing import Dict, List

obstacle_positions = [30, 60, 80]
boost_positions = [20, 50, 70]
boost_duration = 2.0

team_assignments: Dict[str, List[str]] = {
    "красные": ["🚗 Красная-1", "🚗 Красная-2"],
    "синие": ["🚙 Синяя-1", "🚙 Синяя-2"],
}
points_system = [10, 8, 6, 4, 2]

finish_line = 100
print_lock = threading.Lock()


class RacingCar:
    def __init__(self, name: str, speed: float) -> None:
        self.name = name
        self.base_speed = speed
        self.speed = speed
        self.position = 0.0
        self.boost_active_until = 0.0

    def _check_obstacles(self) -> None:
        for obstacle in obstacle_positions:
            if self.position < obstacle <= self.position + self.speed:
                with print_lock:
                    print(f"⛔ {self.name}遇阻 на отметке {obstacle}м. Остановка на 0.5с")
                time.sleep(0.5)

    def _check_boosts(self) -> None:
        current_time = time.time()
        for boost in boost_positions:
            if self.position < boost <= self.position + self.speed:
                with print_lock:
                    print(f"⚡ {self.name} взяла ускорение на отметке {boost}м")
                self.boost_active_until = current_time + boost_duration
                self.speed = self.base_speed * 2

        if current_time > self.boost_active_until:
            self.speed = self.base_speed

    def race(self, results: List[str]) -> None:
        while self.position < finish_line:
            self._check_boosts()
            self._check_obstacles()

            move = self.speed * random.uniform(0.8, 1.2)
            self.position += move

            with print_lock:
                progress_bar = "█" * int(self.position // 5)
                print(f"{self.name}: {progress_bar:<20} {self.position:5.1f}м")

            time.sleep(0.2)

        with print_lock:
            print(f"🏁 {self.name} финишировала!")
        results.append(self.name)


def assign_points(results: List[str]) -> Dict[str, int]:
    team_scores: Dict[str, int] = defaultdict(int)
    for index, car_name in enumerate(results):
        points = points_system[index] if index < len(points_system) else 0
        for team, members in team_assignments.items():
            if car_name in members:
                team_scores[team] += points
    return team_scores


def main() -> None:
    cars = [
        RacingCar("🚗 Красная-1", 15),
        RacingCar("🚗 Красная-2", 14),
        RacingCar("🚙 Синяя-1", 15.5),
        RacingCar("🚙 Синяя-2", 13.5),
    ]

    results: List[str] = []
    threads: List[threading.Thread] = []

    print("🏎️ Стартуем командную гонку!")

    for car in cars:
        thread = threading.Thread(target=car.race, args=(results,), name=f"Racer-{car.name}")
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    with print_lock:
        print("=" * 50)
        print("🏆 Итоговый порядок финиша:")
        for place, car_name in enumerate(results, 1):
            print(f"{place}. {car_name}")

        team_scores = assign_points(results)
        print("\n📊 Командный зачёт:")
        for team, score in team_scores.items():
            print(f"Команда {team}: {score} очков")

        if team_scores:
            winner = max(team_scores, key=team_scores.get)
            print(f"\n🎖️ Победила команда {winner}!")


if __name__ == "__main__":
    main()
