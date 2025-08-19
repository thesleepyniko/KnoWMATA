import asyncio
import csv
import io
import json
import zipfile
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from config import settings
from db import SessionLocal, create_tables
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from haversine import Unit, haversine
from models import station_info
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.applications import Starlette

DATA_DIR = Path("data")
WMATA_DIR = DATA_DIR / "wmata"
origins = [
    "https://thisiscid.github.io",               # your user site
    "https://thisiscid.github.io/KnoWMATA",   # repo site
    "https://thisiscid.github.io/KnowMATA/game.html"
    "http://localhost:8000"                       # dev testing
]


async def load_gtfs() -> tuple[str, datetime]:
    async with httpx.AsyncClient() as client:
        try:
            with open(WMATA_DIR / "metadata.json", "r", encoding="utf-8") as f:
                metadata=json.load(f)
                now = datetime.now(timezone.utc)
                next_update = datetime.fromisoformat(metadata["next_update"])
                if now < next_update:
                    # print(f"GTFS still valid until {next_update}, skipping update")
                    return ("not_needed", next_update)
        except Exception as e:
            print(f"Exception: {e}")
        resp = await client.get(
            "https://api.wmata.com/gtfs/rail-bus-gtfs-static.zip",
            headers={
                "api_key": settings.WMATA_API_KEY,
                "Cache-Control": "no-cache"
            }
        )
        resp.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            print(zf.namelist())
            zf.extractall(WMATA_DIR)
        now = datetime.now(timezone.utc)
        metadata = {
            "time": now.isoformat(),
            "next_update": (now + timedelta(days=1)).isoformat()
        }
        with open(WMATA_DIR / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        create_tables()
        with open(WMATA_DIR / "stops.txt", newline="", encoding="utf-8") as f:
            reader=csv.DictReader(f)
            db: Session = SessionLocal()
            for row in reader:
                station = station_info(
                    id=row["stop_id"],
                    name=row["stop_name"],
                    stop_lat=float(row["stop_lat"]),
                    stop_long=float(row["stop_lon"]),
                    stop_lat_raw=row["stop_lat"],
                    stop_long_raw=row["stop_lon"],
                )
                db.merge(station)
            db.commit()
            db.close()
        return ("updated", now + timedelta(days=1))

async def updater_task():
    while True:
        gtfs_status=await load_gtfs()
        now = datetime.now(timezone.utc)
        if gtfs_status[0] == "not_needed":
            print(f"GTFS still valid until {gtfs_status[1]}, skipping update")
            await asyncio.sleep((gtfs_status[1] - now).total_seconds())
        elif gtfs_status[0] == "updated":
            next_update = now + timedelta(days=1)
            print(f"Updated at {now.isoformat()}, next at {next_update.isoformat()}")
            await asyncio.sleep(24 * 60 * 60)

    

@asynccontextmanager
async def lifespan(app: FastAPI):
    # asyncio.create_task(load_gtfs())
    task=asyncio.create_task(updater_task())

    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Updater task shut down cleanly")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/random_stop")
@limiter.limit("15/minute")
def get_random_stop(request: Request, user_lat: float, user_long: float, min_range: float=0.5, max_range: float=2):
    user_location = (user_lat, user_long)
    has_found_valid_loc = False
    attempts=0
    with SessionLocal() as db:
        while not has_found_valid_loc:
            result = db.query(station_info).order_by(func.random()).first()
            miles=haversine(user_location, (result.stop_lat, result.stop_long), unit=Unit.MILES) # type: ignore
            if min_range<=miles<=max_range:
                has_found_valid_loc=True
            if attempts>=1000:
                return {}
            attempts+=1
    return result #type: ignore