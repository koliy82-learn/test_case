import threading
import time
from queue import Queue, Empty
from venv import logger

from celery import Celery
from flask import Flask, request, jsonify
from redis import Redis

from message import Message

host = "host.docker.internal"
redis_url = f'redis://{host}:6379/0'
rabbit_url = f'amqp://guest:guest@{host}:5672/'
app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = redis_url
app.config['CELERY_RESULT_BACKEND'] = redis_url

redis = Redis(host=host, port=6379, db=0)
celery = Celery(
    app.import_name,
    broker=rabbit_url,
    backend="rpc://",
)

# celery.conf.update(
#     task_annotations={'*': {'rate_limit': '8/s'}}
# )


@celery.task(rate_limit='8/s')
def send_to_receiver(message_data):
    message = Message.from_json(message_data)


queue = Queue()


@app.route('/webhook', methods=['POST'])
def webhook():
    response = jsonify(success=True)
    data_json = request.get_json()

    try:
        message = Message.from_json(data_json)
    except ValueError as err:
        response.status = err
        return response, 200

    logger.debug(f"request message: {message}")

    exist = redis.exists(message.message_id)
    if not exist:
        redis.set(message.message_id, message.text, ex=300)

    queue.put(message)

    response.headers['X-Celery-ID'] = message.message_id or 'duplicate'
    return response, 200


def process_messages(rate=8):
    while True:
        try:
            message = queue.get(timeout=1)
            send_to_receiver.delay(message.to_json())
            print(f"Processed message: {message}")
            time.sleep(1 / rate)
            queue.task_done()
        except Empty:
            logger.debug("Message queue is empty")
            time.sleep(1)
            pass


messages_thread = threading.Thread(target=process_messages)
messages_thread.daemon = True
messages_thread.start()


if __name__ == '__main__':
    app.run(debug=True, threaded=True)