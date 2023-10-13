from pydantic import BaseModel


_dto = {
    "time_slots": ["8:00-20:00", "10:00-22:00"],
    "workers": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"],
    "working_hrs_month_max": 144,
    "working_hours": 12,
    "increase_load_at": {
        "days_of_week": ["Mon", ],
        "inc_workers_on": 1,
    },
    "decrease_load_at": {
        "days_of_week": ["Sun", ],
        "dec_workers_on": 1,
    },
    "days_in_month": 31,
    "start_schedule_from_day": "Mon",
}


class _Preset(BaseModel):
    """Some preset for several days at week."""
    days_of_week: list[str, ...]


class Increace(_Preset):
    inc_workers_on: int


class Decreace(_Preset):
    dec_workers_on: int


class CalculateSchedule(BaseModel):
    """Request DTO."""
    time_slots: list[str, ...]
    workers: list[str, ...]
    working_hrs_month_max: int
    working_hours: int
    increase_load_at: Increace
    decrease_load_at: Decreace
    days_in_month: int
    start_schedule_from_day: str
