from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple


class Airport:
    """Класс, представляющий аэропорт."""
    def __init__(self, code: str, name: str, city: str):
        self.code: str = code.upper()  # Идентификатор (например, SVO, DXB)
        self.name: str = name
        self.city: str = city

    def __repr__(self):
        return f"{self.city} ({self.code})"


class FlightConfiguration:
    """Класс конфигурации мест по классам обслуживания."""
    def __init__(self, config_data: Dict[str, Tuple[int, int]]):
        """
        config_data принимает словарь вида:
        {'Бизнес': (rows, cols), 'Эконом': (rows, cols)}
        Пример: {'Бизнес': (2, 4)} означает 2 ряда по 4 места (всего 8 мест).
        """
        self.layout: Dict[str, List[List[str]]] = {}
        
        for service_class, (rows, cols) in config_data.items():
            # 'O' означает свободное место
            self.layout[service_class] = [['O' for _ in range(cols)] for _ in range(rows)]

    def get_total_free_seats(self, service_class: str) -> int:
        """Возвращает общее количество свободных мест в классе."""
        if service_class not in self.layout:
            return 0
        return sum(row.count('O') for row in self.layout[service_class])

    def book_seat(self, service_class: str, row: int, col: int) -> bool:
        """Бронирует конкретное место (индексы с 0)."""
        if service_class not in self.layout:
            return False
        
        try:
            if self.layout[service_class][row][col] == 'O':
                self.layout[service_class][row][col] = 'X'  # 'X' - занято
                return True
        except IndexError:
            return False
        return False

    def find_adjacent_seats(self, service_class: str, count: int) -> List[Tuple[int, int]]:
        """Ищет несколько свободных мест подряд в одном ряду."""
        if service_class not in self.layout or count <= 0:
            return []

        for row_idx, row in enumerate(self.layout[service_class]):
            current_streak = []
            for col_idx, seat in enumerate(row):
                if seat == 'O':
                    current_streak.append((row_idx, col_idx))
                    if len(current_streak) == count:
                        return current_streak
                else:
                    current_streak = []
        return []

    def print_layout(self):
        """Выводит визуальный план салона."""
        for service_class, rows in self.layout.items():
            print(f"\n--- Класс: {service_class} ---")
            for i, row in enumerate(rows):
                row_str = " ".join(row)
                print(f"Ряд {i+1:02d}: [ {row_str} ]")


class Flight:
    """Класс, описывающий конкретный рейс."""
    def __init__(self, flight_number: str, origin: Airport, destination: Airport, 
                 departure_time: datetime, duration_minutes: int, 
                 config: FlightConfiguration, has_meal: bool = True, extra_baggage: bool = False):
        self.flight_number: str = flight_number
        self.origin: Airport = origin
        self.destination: Airport = destination
        self.departure_time: datetime = departure_time
        self.duration: timedelta = timedelta(minutes=duration_minutes)
        self.config: FlightConfiguration = config
        
        # Специальные условия
        self.special_conditions: Dict[str, bool] = {
            "Питание": has_meal,
            "Доп. багаж": extra_baggage
        }

    @property
    def arrival_time(self) -> datetime:
        return self.departure_time + self.duration

    def __repr__(self):
        return f"Рейс {self.flight_number} | {self.origin} -> {self.destination} | Вылет: {self.departure_time.strftime('%Y-%m-%d %H:%M')}"


class AirlineSystem:
    """Основная управляющая система авиакомпании."""
    def __init__(self):
        self.airports: Dict[str, Airport] = {}
        self.flights: List[Flight] = []

    def add_airport(self, code: str, name: str, city: str) -> Airport:
        """Добавляет аэропорт в систему."""
        airport = Airport(code, name, city)
        self.airports[airport.code] = airport
        return airport

    def add_flight(self, flight_number: str, origin_code: str, destination_code: str, 
                   departure_time: datetime, duration_minutes: int, 
                   config: FlightConfiguration, has_meal: bool = True, extra_baggage: bool = False) -> Optional[Flight]:
        """Добавляет рейс между аэропортами."""
        origin = self.airports.get(origin_code.upper())
        destination = self.airports.get(destination_code.upper())

        if not origin or not destination:
            print(f"Ошибка создания рейса {flight_number}: Аэропорт не найден.")
            return None

        flight = Flight(flight_number, origin, destination, departure_time, duration_minutes, config, has_meal, extra_baggage)
        self.flights.append(flight)
        return flight

    def get_flights_between(self, origin_code: str, destination_code: str, 
                             start_from: datetime) -> List[Flight]:
        """Фильтрует рейсы по направлению и времени (только будущие от start_from)."""
        return [
            f for f in self.flights
            if f.origin.code == origin_code.upper() 
            and f.destination.code == destination_code.upper() 
            and f.departure_time >= start_from
        ]

    def find_nearest_flight(self, origin_code: str, destination_code: str, 
                             start_from: datetime, service_class: str, 
                             time_preference: Optional[str] = None) -> Optional[Flight]:
        """
        Поиск ближайшего рейса по направлению с доступными местами.
        time_preference может быть: 'morning' (06:00-12:00), 'afternoon' (12:00-18:00), 'evening' (18:00-00:00), 'night' (00:00-06:00)
        """
        candidate_flights = self.get_flights_between(origin_code, destination_code, start_from)
        
        # Сортируем по времени вылета (сначала самые близкие)
        candidate_flights.sort(key=lambda x: x.departure_time)

        for flight in candidate_flights:
            # Проверяем наличие мест в нужном классе
            if flight.config.get_total_free_seats(service_class) > 0:
                
                # Проверяем временные предпочтения, если они заданы
                if time_preference:
                    hour = flight.departure_time.hour
                    if time_preference == 'morning' and not (6 <= hour < 12): continue
                    if time_preference == 'afternoon' and not (12 <= hour < 18): continue
                    if time_preference == 'evening' and not (18 <= hour < 24): continue
                    if time_preference == 'night' and not (0 <= hour < 6): continue

                return flight
        return None

    def find_nearest_flight_with_adjacent_seats(self, origin_code: str, destination_code: str, 
                                                start_from: datetime, service_class: str, 
                                                seat_count: int) -> Optional[Tuple[Flight, List[Tuple[int, int]]]]:
        """Поиск ближайшего рейса, где есть несколько свободных мест РЯДОМ."""
        candidate_flights = self.get_flights_between(origin_code, destination_code, start_from)
        candidate_flights.sort(key=lambda x: x.departure_time)

        for flight in candidate_flights:
            adjacent_seats = flight.config.find_adjacent_seats(service_class, seat_count)
            if adjacent_seats:
                return flight, adjacent_seats
        return None


# ==========================================
# ДЕМОНСТРАЦИЯ РАБОТЫ ПРОГРАММЫ
# ==========================================
if __name__ == "__main__":
    system = AirlineSystem()

    # 1. Добавляем аэропорты
    system.add_airport("SVO", "Шереметьево", "Москва")
    system.add_airport("DXB", "Дубай Интернешнл", "Дубай")
    system.add_airport("JFK", "Дж. Кеннеди", "Нью-Йорк")

    # 2. Создаем конфигурации мест для самолетов
    # Схема: 2 ряда по 2 места в Бизнесе, 3 ряда по 4 места в Экономе
    plane_config_1 = FlightConfiguration({"Бизнес": (2, 2), "Эконом": (3, 4)})
    plane_config_2 = FlightConfiguration({"Бизнес": (1, 2), "Эконом": (5, 4)})

    # 3. Добавляем рейсы
    now = datetime.now()
    
    # Утренний рейс в Дубай (9:30)
    flight1 = system.add_flight(
        flight_number="SU-520", origin_code="SVO", destination_code="DXB",
        departure_time=now + timedelta(days=1, hours=1), duration_minutes=330, 
        config=plane_config_1, has_meal=True, extra_baggage=True
    )
    
    # Вечерний рейс в Дубай (21:00)
    flight2 = system.add_flight(
        flight_number="SU-522", origin_code="SVO", destination_code="DXB",
        departure_time=now + timedelta(days=1, hours=12), duration_minutes=330, 
        config=plane_config_2, has_meal=True, extra_baggage=False
    )

    print("--- Проверка специальных условий для рейса SU-520 ---")
    print(f"Питание включено: {flight1.special_conditions['Питание']}")
    print(f"Возможен доп. багаж: {flight1.special_conditions['Доп. багаж']}\n")

    # 4. Бронирование мест
    print("--- Бронирование мест на рейс SU-520 ---")
    # Успешное бронирование конкретного места в бизнесе (Ряд 1, Место 1)
    success = flight1.config.book_seat("Бизнес", row=0, col=0)
    print(f"Бронирование Бизнес (0,0): {'Успешно' if success else 'Место занято/Ошибка'}")
    
    # Повторное бронирование того же места
    success = flight1.config.book_seat("Бизнес", row=0, col=0)
    print(f"Повторное бронирование Бизнес (0,0): {'Успешно' if success else 'Место занято/Ошибка'}")

    # 5. Печать плана салона после бронирования
    print("\n--- Текущий план салона SU-520 ('O' - свободно, 'X' - занято) ---")
    flight1.config.print_layout()