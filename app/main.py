import logging
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from app.rules import calculate_risk, make_decision
from app.db import save_event, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

class LoginEvent(BaseModel):
    user_id: str
    ip: str
    country: str
    device: str
    hour: int
    failed_attempts: int

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/login")
def login(event: LoginEvent):
    data = event.model_dump()
    score, reasons = calculate_risk(data)
    decision = make_decision(score)
    save_event(data, score, decision)
    logger.info(json.dumps({
        "event_type": "login_risk_evaluated",
        "user_id": data["user_id"],
        "ip": data["ip"],
        "country": data["country"],
        "decision": decision,
        "risk_score": score,
        "reasons": reasons
    }))
    return {
        "risk_score": score,
        "decision": decision,
        "reasons": reasons
    }
