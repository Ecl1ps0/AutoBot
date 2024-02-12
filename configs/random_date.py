import random
import datetime

from datetime import datetime


def get_random_date(start_date: datetime = datetime(1990, 1, 1),
                    end_date: datetime = datetime(2004, 12, 31),
                    time_format: str = "%d.%m.%Y") -> str:
    start_time = datetime.strptime(start_date.strftime(time_format), time_format)
    end_time = datetime.strptime(end_date.strftime(time_format), time_format)

    prop = random.random()
    delta = end_time - start_time

    random_date = start_time + prop * delta
    return random_date.strftime(time_format)
