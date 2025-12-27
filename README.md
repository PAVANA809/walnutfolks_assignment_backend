# Webhook Processing Service

This is a simple backend service designed to handle transaction webhooks. It receives transaction data, saves it to a database, and processes it in the background so the sender gets a quick response.

**Live Deployment:** [https://walnutfolks-assignment-backend.onrender.com/](https://walnutfolks-assignment-backend.onrender.com/)

> **Note:** Since this is hosted on a Render free instance, the service may spin down when inactive. Please expect a delay of up to 50 seconds for the first request while the service restarts.

## System Behavior
*   **Fast Response:** The API acknowledges webhooks immediately (within 500ms) with a `202 Accepted` status.
*   **Background Processing:** Actual processing happens in the background with a simulated **30-second delay**.
*   **Idempotency:** Duplicate webhooks for the same `transaction_id` are safely ignored.

## How to Test

### 1. Send a Webhook
**Endpoint:** `POST /v1/webhooks/transactions`
**Body:**
```json
{
  "transaction_id": "txn_test_123",
  "source_account": "acc_source",
  "destination_account": "acc_dest",
  "amount": 100.0,
  "currency": "USD"
}
```

### 2. Check Status
**Endpoint:** `GET /v1/transactions/txn_test_123`

*   **Before 30s:** Returns `{"status": "PROCESSING", ...}`
*   **After 30s:** Returns `{"status": "PROCESSED", ...}`

## Setup and Running

1.  **Environment Setup**
    Create a virtual environment to keep dependencies isolated:
    ```
    python -m venv .venv
    ```

    Activate the environment:
    - Windows: `.venv\Scripts\activate`
    - Mac/Linux: `source .venv/bin/activate`

2.  **Install Dependencies**
    ```
    pip install -r requirements.txt
    ```

3.  **Configuration**
    Create a `.env` file in this folder if you haven't already. It needs your database connection string:
    ```
    MONGO_URI=mongodb://localhost:27017/wfa_db
    ```

4.  **Run the Server**
    Start the application using uvicorn:
    ```
    uvicorn app.main:app --reload
    ```
    
    The API will be available at `http://127.0.0.1:8000`.
    You can see the interactive docs at `http://127.0.0.1:8000/docs`.

## Why we chose this stack

We made a few specific technology choices for this project to ensure it's fast and easy to maintain:

*   **FastAPI**: We picked this because it's modern, very fast, and supports asynchronous code out of the box. Since we are handling webhooks, we need to be able to handle many requests concurrently without blocking. The automatic validation and documentation are a nice bonus.

*   **MongoDB**: Webhook data is naturally JSON, so a document store like MongoDB fits perfectly. It lets us store the data exactly as it comes in without fighting with rigid table schemas.

*   **Motor**: This is the asynchronous driver for MongoDB. It's crucial because a standard database driver would pause the entire application while waiting for a database query to finish. Motor lets the app handle other requests while the database is working.

*   **Pydantic**: We use this to define what a valid transaction looks like. It automatically checks types (like making sure the amount is a number) so we don't have to write a bunch of manual validation code.

*   **Background Tasks**: To keep the webhook response time low, we don't process the transaction immediately. We save it, return a "202 Accepted" response, and then let FastAPI's background task handler do the processing (simulated with a delay) afterwards.
