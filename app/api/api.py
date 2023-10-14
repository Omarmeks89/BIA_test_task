from fastapi import APIRouter
from fastapi import Depends, HTTPException

from .schemas.requests import CalculateSchedule
from .schemas.responces import ScheduleResponce
from utils.utils import calculate_schedule
from utils.exceptions import InvalidScheduleParameter


scheduler = APIRouter(prefix="/scheduler")


@scheduler.post("/schedule.json")
async def get_schedule(
        s_request: CalculateSchedule = Depends(),
        ) -> ScheduleResponce:
    try:
        schedules = await calculate_schedule(s_request)
        return ScheduleResponce(workers=schedules)
    except (InvalidScheduleParameter, Exception) as exp:
        msg = f"ERROR: {exp}"
        raise HTTPException(
                status_code=409,
                detail=msg,
                )
