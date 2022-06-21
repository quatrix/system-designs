import aiokafka
import asyncio
import config
import json

async def worker(worker_id):
    consumer = aiokafka.AIOKafkaConsumer(
        config.TOPIC,
        bootstrap_servers=config.KAFKA_SERVER,
        group_id='worker',
        enable_auto_commit=True,
    )

    producer = aiokafka.AIOKafkaProducer(bootstrap_servers=config.KAFKA_SERVER)


    await producer.start()
    await consumer.start()

    print(f'[{worker_id=}] started worker!')

    try:
        async for msg in consumer:
            partition = msg.partition
            msg = json.loads(msg.value.decode('utf-8'))
            request_id = msg['request_id']
            topic = f'results-{request_id}'

            print(f'[{worker_id=} ({partition=})] got msg! {msg=}')

            if msg['action'] == 'FETCH':
                url = msg['url']

                print(f'[{worker_id=}] fetching url {url=}')
                await asyncio.sleep(0.5)

                response = {
                    'action': 'RESULT',
                    'url': url,
                }

                response = json.dumps(response).encode('utf-8')
                print(f'[{worker_id=}] sending repsonse {response=}')
                await producer.send_and_wait(topic, response)
            elif msg['action'] == 'FIN':
                response = {
                    'action': 'FIN',
                    'partition': partition,
                }
                response = json.dumps(response).encode('utf-8')
                print(f'[{worker_id=}] sending repsonse {response=}')
                await producer.send_and_wait(topic, response)
    finally:
        print(f'[{worker_id=}] bye!')
        await consumer.stop()
        await producer.stop()

