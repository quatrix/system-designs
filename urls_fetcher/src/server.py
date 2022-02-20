from fastapi import FastAPI, WebSocket
from producer import publish
from consumer import consume
from worker import worker
from uuid import uuid4
import asyncio

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print('starting workers!')
    asyncio.create_task(worker(0))
    asyncio.create_task(worker(1))

@app.post("/urls")
async def post_urls():
    request_id = str(uuid4())

    urls = [
        'hey',
        'ho',
        'lets',
        'go',
    ]

    await publish(request_id, urls)

    return {
        "status": "accepted",
        "results-ws": f"/results/{request_id}",
    }


@app.websocket("/results/{request_id}")
async def websocket_endpoint(websocket: WebSocket, request_id: str):
    await websocket.accept()
    await consume(websocket.send_text, request_id)
