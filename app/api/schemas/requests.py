from typing import Iterable

from pydantic import BaseModel


class _Preset(BaseModel):
    """Some preset for several days at week."""
    days_of_week: Iterable[str]


class Increace(_Preset):
    inc_workers_on: int


class Decreace(_Preset):
    dec_workers_on: int


class CalculateSchedule(BaseModel):
    """Request DTO."""
    time_slots: Iterable[str]
    workers: Iterable[str]
    working_hrs_month_max: int
    working_hours: int
    increase_load_at: Increace
    decrease_load_at: Decreace
    days_in_month: int
    start_schedule_from_day: str
