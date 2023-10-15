import uvicorn
from fastapi import FastAPI

from api.api import scheduler
from settings import AppSettings


app = FastAPI(
        title="BIA Technologies test task.",
        version="0.1.0",
        )
app.include_router(scheduler)
app_set = AppSettings()


if __name__ == "__main__":
    uvicorn.run(app_set.app_run_path, reload=app_set.reload)
