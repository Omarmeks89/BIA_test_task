import json
import heapq
from abc import abstractmethod
from collections import deque

from .schemas.requests import (
        CalculateSchedule,
        Increace,
        Decreace,
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
        self._start_day = st_day
        self._days_cnt = days_cnt
        self._days = list(self._frames.keys())
        self._pos = self._set_st_pos(self._start_day)
        self._curr_day_no = 0

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
        for day in self._days:
            self._frames[day] = dframe_s
            if inc and day in inc.days_of_week:
                self._frames[day] += inc.inc_workers_on
            if dec and day in dec.days_of_week:
                if (self._frames[day] - dec.dec_workers_on) >= 2:
                    self._frames[day] -= dec.dec_workers_on


_WORKERS = []


class BaseWorker:

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

    def __eq__(self, other: "BaseWorker") -> bool:
        self._w_hours == other.hours_worked

    def __lt__(self, other: "BaseWorker") -> bool:
        self._w_hours < other.hours_worked

    def __gt__(self, other: "BaseWorker") -> bool:
        self._w_hours > other.hours_worked

    def __le__(self, other: "BaseWorker") -> bool:
        self._w_hours <= other.hours_worked

    def __ge__(self, other: "BaseWorker") -> bool:
        self._w_hours >= other.hours_worked

    @abstractmethod
    def work_in_frame(self, frame: str, day_by_ord: int) -> None: pass

    @abstractmethod
    def as_json(self) -> str: pass


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
        self._mtime = mtime
        self._frames = {}

    @property
    def can_work(self) -> bool:
        return self._wh_per_month >= self._mtime

    def __repr__(self) -> str:
        return f"{self._name}[{self._wh_per_month}][{self._w_hours}]()"

    def work_in_frame(self, frame: str, day_by_ord: int) -> None:
        if frame not in self._frames:
            self._frames[frame] = [0] * self._days
        self._frames[frame][day_by_ord - 1] = 1
        self._wh_per_month -= self._mtime
        self._w_hours += self._mtime

    def as_json(self) -> str:
        return json.dumps(self.__dict__, indent=4)


def _calculate_whours_per_day(
        max_hrs_month: int,
        workers_cnt: int,
        days: int,
        ) -> int:
    """calculate total work hours by
    all of worker per day."""
    return (max_hrs_month * workers_cnt) // days


def _fill_payload(
        hrs_day: int,
        payload: RingBuffer,
        source: CalculateSchedule
        ) -> None:
    """Fill current frame-sizes into ring buffer."""
    w_count_day = hrs_day // source.working_hours
    payload.set_frames(
            w_count_day,
            source.increase_load_at,
            source.decrease_load_at,
            )


def _fill_heap(
        workers: list[str],
        wh_per_month: int,
        days_in_month: int,
        max_time_per_day: int,
        ) -> None:
    """fill mimheap by created workers."""
    for w in workers:
        _WORKERS.append(
                Worker(w, wh_per_month, days_in_month, max_time_per_day),
                )
    heapq.heapify(_WORKERS)


def calc_schedule(
        buff: RingBuffer,
        workers: list[Worker, ...],
        frames: list[str, ...],
        ) -> None:
    _frames, _dump_heap = deque(frames), []
    while buff.next():
        frame_size, day_no = buff.frame(), buff.day_no
        for i in range(frame_size):
            frame = _frames.popleft()
            if not _WORKERS:
                for _ in range(len(_dump_heap)):
                    heapq.heappush(_WORKERS, heapq.heappop(_dump_heap))
            worker = heapq.heappop(_WORKERS)
            if worker.can_work:
                worker.work_in_frame(frame, day_no)
            heapq.heappush(_dump_heap, worker)
            _frames.append(frame)
    if _dump_heap:
        for _ in range(len(_dump_heap)):
            heapq.heappush(_WORKERS, heapq.heappop(_dump_heap))
