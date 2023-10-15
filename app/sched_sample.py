import asyncio

from api.schemas.requests import CalculateSchedule, Increace, Decreace
from utils.utils import calculate_schedule


fst_sched = CalculateSchedule(
        time_slots=["08:00-20:00", "10:00-22:00"],
        workers=["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"],
        working_hrs_month_max=144,
        working_hours=12,
        increase_load_at=Increace(
            days_of_week=["Mon", "Tue", "Wed"],
            inc_workers_on=1,
            ),
        decrease_load_at=Decreace(
            days_of_week=["Sun", ],
            dec_workers_on=1,
            ),
        days_in_month=31,
        start_schedule_from_day="Mon",
        )


sec_sched = CalculateSchedule(
        time_slots=["08:00-20:00", "10:00-22:00"],
        workers=["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"],
        working_hrs_month_max=144,
        working_hours=12,
        increase_load_at=Increace(
            days_of_week=["Mon", ],
            inc_workers_on=1,
            ),
        decrease_load_at=Decreace(
            days_of_week=["Sun", ],
            dec_workers_on=1,
            ),
        days_in_month=28,
        start_schedule_from_day="Sun",
        )


third_sched = CalculateSchedule(
        time_slots=["09:00-19:00", "10:00-20:00", "11:00-21:00"],
        workers=["a", "b", "c", "d", "e", "f"],
        working_hrs_month_max=189,
        working_hours=9,
        increase_load_at=Increace(
            days_of_week=["Sun"],
            inc_workers_on=1,
            ),
        decrease_load_at=Decreace(
            days_of_week=[],
            dec_workers_on=0,
            ),
        days_in_month=30,
        start_schedule_from_day="Sun",
        )


async def main() -> None:
    """test of samples."""
    for s in (fst_sched, sec_sched, third_sched):
        workers = await calculate_schedule(s)
        for w in workers:
            for t_frame, schedule in w.frames.items():
                print(f"{w.wname:>4} | {t_frame:<16} | {list(schedule)}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
