import aiokafka
import config
import json


async def consume(send, request_id):
    topic = f'results-{request_id}'

    consumer = aiokafka.AIOKafkaConsumer(
        topic,
        bootstrap_servers=config.KAFKA_SERVER,
        auto_offset_reset="earliest"
    )

    await consumer.start()

    waiting = set(range(100))

    print(f'[CONSUMER] starting consumer {topic=}')

    try:
        async for msg in consumer:
            msg = json.loads(msg.value.decode('utf-8'))
            print(f'[CONSUMER] got msg {msg=}')

            if msg['action'] == 'RESULT':
                await send(msg['url'])
            elif msg['action'] == 'FIN':
                partition = msg['partition']
                waiting.remove(partition)

                if not waiting:
                    await send('done!')
                    break
    finally:
        print('bye')
        await consumer.stop()
