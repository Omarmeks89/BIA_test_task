from typing import Iterable

from pydantic import BaseModel


class WorkerSchedule(BaseModel):
    """Base impl of worker`s schedule."""
    wname: str
    worked: int
    remaining_hrs: int
    frames: dict[str, Iterable[int]]


class ScheduleResponce(BaseModel):
    """Base responce with calculated schedule."""
    workers: Iterable[WorkerSchedule]
