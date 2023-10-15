import copy
import asyncio
import heapq
from typing import Iterable
from typing import TypeVar
from typing import Final
from abc import abstractmethod
from collections import deque

from api.schemas.requests import (
        CalculateSchedule,
        Increace,
        Decreace,
        )
from api.schemas.responces import (
        WorkerSchedule,
        )
from .exceptions import InvalidScheduleParameter


WorkerT = TypeVar("WorkerT", bound="BaseWorker", contravariant=True)

_MIN_DAYS_MNTH: Final[int] = 28
_MAX_DAYS_MNTH: Final[int] = 31
_MAX_HRS_DAY: Final[int] = 24


__all__ = (
        "WorkerT",
        "calculate_schedule",
        )


class RingBuffer:

    _def_payload_days = {
        "Mon": 0,
        "Tue": 0,
        "Wed": 0,
        "Thu": 0,
        "Fri": 0,
        "Sat": 0,
        "Sun": 0,
    }

    def __init__(self, st_day: str, days_cnt: int) -> None:
        self._frames = type(self)._def_payload_days
        self._days_cnt = days_cnt
        self._days = list(self._frames.keys())
        self._curr_day_no = 0
        if self._validate_start_day(st_day):
            self._start_day = st_day
        self._pos = self._set_st_pos(self._start_day)

    @property
    def day_no(self) -> int:
        return self._curr_day_no

    def __repr__(self) -> str:
        return f"{type(self).__name__}(day={self._days[self._pos]})"

    def _set_st_pos(self, day: str) -> int:
        return self._days.index(day)

    def next(self) -> bool:
        """return true if curr pos isn`t a last day in month."""
        return self._curr_day_no < self._days_cnt

    def _validate_start_day(self, day: str) -> bool:
        if day not in self._days:
            msg = f"Invalid day-name: {day}."
            raise InvalidScheduleParameter(msg)
        return True

    def frame(self) -> int:
        """return frame by day-name."""
        frame = self._frames[self._days[self._pos]]
        self._pos += 1
        if self._pos > len(self._days) - 1:
            self._pos = 0
        self._curr_day_no += 1
        return frame

    def set_frames(
            self,
            dframe_s: int,
            inc: Increace,
            dec: Decreace,
            ) -> None:
        """set frame size = workers count per current day.
        If we have increase or decreace count, we apply it here."""
        inc_days = list(inc.days_of_week)
        dec_days = list(dec.days_of_week)
        for day in self._days:
            self._frames[day] = dframe_s
            if inc_days and day in inc_days:
                self._frames[day] += inc.inc_workers_on
            if dec_days and day in dec_days:
                if (self._frames[day] - dec.dec_workers_on) >= 2:
                    self._frames[day] -= dec.dec_workers_on


class BaseWorker:
    """base for workers impl."""

    def __init__(
            self,
            name: str,
            hpm: int,
            ) -> None:
        self._name = name
        self._wh_per_month = hpm  # work hours per month
        self._w_hours = 0  # used for minheap

    @property
    def hours_worked(self) -> int:
        return self._w_hours

    @property
    def remaining_hrs(self) -> int:
        return self._wh_per_month

    @property
    def name(self) -> str:
        return self._name

    @property
    @abstractmethod
    def frames(self) -> dict[str, Iterable[int]]: pass

    @property
    @abstractmethod
    def can_work(self) -> bool: pass

    def __eq__(self, other: WorkerT) -> bool:
        self._w_hours == other.hours_worked

    def __lt__(self, other: WorkerT) -> bool:
        self._w_hours < other.hours_worked

    def __gt__(self, other: WorkerT) -> bool:
        self._w_hours > other.hours_worked

    def __le__(self, other: WorkerT) -> bool:
        self._w_hours <= other.hours_worked

    def __ge__(self, other: WorkerT) -> bool:
        self._w_hours >= other.hours_worked

    @abstractmethod
    def work_in_frame(self, frame: str, day_by_ord: int) -> None: pass


class Worker(BaseWorker):

    def __init__(
            self,
            name: str,
            hpm: int,
            days_in_month: int,
            mtime: int,
            ) -> None:
        super().__init__(name, hpm)
        self._days = days_in_month
        # control list for exclude duplicates
        self._w_ctrl = [0] * self._days
        self._mtime = mtime
        self._frames = {}

    @property
    def can_work(self) -> bool:
        return self._wh_per_month >= self._mtime

    @property
    def frames(self) -> dict[str, Iterable[int]]:
        return copy.copy(self._frames)

    def __repr__(self) -> str:
        return f"{self._name}[{self._wh_per_month}][{self._w_hours}]()"

    def work_in_frame(self, frame: str, day_by_ord: int) -> None:
        if frame not in self._frames:
            self._frames[frame] = [0] * self._days
        if self._w_ctrl[day_by_ord - 1]:
            return None
        self._w_ctrl[day_by_ord - 1] = True
        self._frames[frame][day_by_ord - 1] = 1
        self._wh_per_month -= self._mtime
        self._w_hours += self._mtime


async def _check_enough_workers(wcnt: int, frames: int) -> None:
    """compare workers count with frames count.
    If workers < (f * 2 - 1), raised InvalidScheduleParameter()."""
    if wcnt < (frames * 2 - 1):
        msg = (
                f"Not enough workers ({wcnt}) for "
                f"frames ({frames}). Need min {frames * 2 - 1} workers."
                )
        raise InvalidScheduleParameter(msg)
    return


async def _calculate_whours_per_day(
        max_hrs_month: int,
        workers_cnt: int,
        days_in_month: int,
        ) -> int:
    """calculate total work hours by
    all of workers per day."""
    if days_in_month < _MIN_DAYS_MNTH or days_in_month > _MAX_DAYS_MNTH:
        msg = f"Invalid days count = {days_in_month}"
        raise InvalidScheduleParameter(msg)
    return (max_hrs_month * workers_cnt) // days_in_month


def _fill_payload(
        hrs_day: int,
        payload: RingBuffer,
        source: CalculateSchedule
        ) -> None:
    """Fill current frame-sizes into ring buffer."""
    if (
            source.working_hours <= 0 or
            source.working_hours > _MAX_HRS_DAY
            ):
        msg = "Working hours have to be in between of 1 and 24"
        raise InvalidScheduleParameter(msg)
    w_count_day = hrs_day // source.working_hours
    payload.set_frames(
            w_count_day,
            source.increase_load_at,
            source.decrease_load_at,
            )


async def _fill_heap(
        heap: list,
        workers: Iterable[str],
        wh_per_month: int,
        days_in_month: int,
        max_time_per_day: int,
        ) -> None:
    """fill minheap by created workers."""
    if not workers:
        msg = "No workers to calculate schedule."
        raise InvalidScheduleParameter(msg)
    for w in workers:
        heap.append(
                Worker(w, wh_per_month, days_in_month, max_time_per_day),
                )
    heapq.heapify(heap)
    return


def calc_schedule(
        buff: RingBuffer,
        workers: list[Worker],
        frames: Iterable[str],
        ) -> None:
    """create schedule from fetched params."""
    _frames, _dump_heap = deque(frames), []
    while buff.next():
        frame_size, day_no = buff.frame(), buff.day_no
        for i in range(frame_size):
            frame = _frames.popleft()
            if not workers:
                for _ in range(len(_dump_heap)):
                    heapq.heappush(workers, heapq.heappop(_dump_heap))
            worker = heapq.heappop(workers)
            if worker.can_work:
                worker.work_in_frame(frame, day_no)
            heapq.heappush(_dump_heap, worker)
            _frames.append(frame)
    if _dump_heap:
        for _ in range(len(_dump_heap)):
            heapq.heappush(workers, heapq.heappop(_dump_heap))


async def calculate_schedule(
        request: CalculateSchedule,
        ) -> Iterable[WorkerSchedule]:
    _heap, schedules = [], []
    workers = list(request.workers)
    slots = list(request.time_slots)
    len_w, len_s = len(workers), len(slots)
    enough_wrk = asyncio.create_task(
            _check_enough_workers(
                len_w,
                len_s,
                ),
            )
    whours_p_day = asyncio.create_task(
            _calculate_whours_per_day(
                request.working_hrs_month_max,
                len_w,
                request.days_in_month,
                ),
            )
    fill_heap = asyncio.create_task(
            _fill_heap(
                _heap,
                workers,
                request.working_hrs_month_max,
                request.days_in_month,
                request.working_hours,
                ),
            )
    await asyncio.gather(whours_p_day, fill_heap, enough_wrk)
    if whours_p_day.done():
        buffer = RingBuffer(
                request.start_schedule_from_day,
                request.days_in_month,
                )
        _fill_payload(whours_p_day.result(), buffer, request)
        calc_schedule(buffer, _heap, slots)
        for w in _heap:
            schedules.append(
                    WorkerSchedule(
                        wname=w.name,
                        worked=w.hours_worked,
                        remaining_hrs=w.remaining_hrs,
                        frames=w.frames,
                        )
                    )
        return schedules
    raise Exception("Unexpected error.")
