from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from datetime import datetime
import motor.motor_asyncio
import asyncio
from pymongo.errors import DuplicateKeyError
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "webhook_service"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
collection = db["transactions"]

app = FastAPI()


class WebhookRequest(BaseModel):
    transaction_id: str
    source_account: str
    destination_account: str
    amount: float
    currency: str


@app.on_event("startup")
async def startup():
    # Unique index for idempotency
    await collection.create_index("transaction_id", unique=True)


@app.get("/")
async def health():
    return {
        "status": "HEALTHY",
        "current_time": datetime.utcnow().isoformat() + "Z"
    }


async def process_transaction(transaction_id: str):

    await asyncio.sleep(30)

    await collection.update_one(
        {"transaction_id": transaction_id, "status": "PROCESSING"},
        {
            "$set": {
                "status": "PROCESSED",
                "processed_at": datetime.utcnow()
            }
        }
    )


@app.post("/v1/webhooks/transactions", status_code=202)
async def receive_webhook(data: WebhookRequest, background_tasks: BackgroundTasks):

    doc = {
        "transaction_id": data.transaction_id,
        "source_account": data.source_account,
        "destination_account": data.destination_account,
        "amount": data.amount,
        "currency": data.currency,
        "status": "PROCESSING",
        "created_at": datetime.utcnow(),
        "processed_at": None
    }

    try:
        await collection.insert_one(doc)
    except DuplicateKeyError:
        # Duplicate webhook -> ignore safely
        pass

    background_tasks.add_task(process_transaction, data.transaction_id)

    return {"message": "accepted"}


@app.get("/v1/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):

    tx = await collection.find_one({"transaction_id": transaction_id})

    if not tx:
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "transaction_id": tx["transaction_id"],
        "source_account": tx["source_account"],
        "destination_account": tx["destination_account"],
        "amount": tx["amount"],
        "currency": tx["currency"],
        "status": tx["status"],
        "created_at": tx["created_at"].isoformat() + "Z",
        "processed_at": tx["processed_at"].isoformat() + "Z" if tx["processed_at"] else None
    }
