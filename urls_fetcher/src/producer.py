import aiokafka
import config
import json
import asyncio


async def publish(request_id, urls):
    producer = aiokafka.AIOKafkaProducer(bootstrap_servers=config.KAFKA_SERVER)

    await producer.start()

    try:
        for url in urls:
            msg = {
                'action': 'FETCH',
                'request_id': request_id,
                'url': url,

            }

            msg = json.dumps(msg).encode('utf-8')
            print(f'publishing {config.TOPIC=} {msg=}')
            await producer.send_and_wait(config.TOPIC, msg)

        for partition in range(100):
            msg = {
                'action': 'FIN',
                'request_id': request_id,
            }

            msg = json.dumps(msg).encode('utf-8')
            await producer.send_and_wait(config.TOPIC, msg, partition=partition)
    finally:
        await producer.stop()
