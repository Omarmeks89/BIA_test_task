from fastapi import APIRouter


scheduler = APIRouter(prefix="/scheduler")


@scheduler.get()
async def get_schedule() -> None:
    ...
