from fastapi import APIRouter
from fastapi import HTTPException

from .schemas.requests import CalculateSchedule
from .schemas.responces import ScheduleResponce
from utils.utils import calculate_schedule
from utils.exceptions import InvalidScheduleParameter


scheduler = APIRouter(prefix="/scheduler", tags=["schedule", ])
_API_VERS: str = "1.0"


@scheduler.post(f"/{_API_VERS}/schedule.json")
async def get_schedule(
        s_request: CalculateSchedule,
        ) -> ScheduleResponce:
    """calculate schedule by request.
    If invalid parameters detected, raised InvalidScheduleParameter.
    Return list of schedules."""
    try:
        schedules = await calculate_schedule(s_request)
        return ScheduleResponce(workers=schedules)
    except (InvalidScheduleParameter, Exception) as exp:
        msg = f"ERROR: {exp}"
        raise HTTPException(status_code=422, detail=msg)
