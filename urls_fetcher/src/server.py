from fastapi import FastAPI, WebSocket
from producer import publish
from consumer import consume
from worker import worker
from uuid import uuid4
from aiokafka.admin import AIOKafkaAdminClient
from kafka.admin import NewTopic
import asyncio
import config

app = FastAPI()
admin = None

topics = set()

@app.on_event("startup")
async def startup_event():
    print('starting admin!')
    global admin


    print('starting workers!')
    asyncio.create_task(worker(0))
    asyncio.create_task(worker(1))


async def create_results_topic(request_id: str):
    topic = f'results-{request_id}'
    if topic not in topics:
        print(f'creating topic {topic=}!')

        for _ in range(30):
            admin = AIOKafkaAdminClient(bootstrap_servers=config.KAFKA_SERVER)
            await admin.start()

            res = await admin.create_topics(new_topics=[NewTopic(topic, 1, 1)])

            if res.topic_errors[0][1] == 0:
                topics.add(topic)
                return


        print('oh no! failed creating topic')



@app.post("/urls")
async def post_urls():
    request_id = str(uuid4())

    await create_results_topic(request_id)

    urls = [
        'hey',
        'ho',
        'lets',
        'go',
    ]

    await publish(request_id, urls)

    return {
        "status": "accepted",
        "ws": f"/results/{request_id}",
    }


@app.websocket("/results/{request_id}")
async def websocket_endpoint(websocket: WebSocket, request_id: str):
    await websocket.accept()
    await consume(websocket.send_text, request_id)
