import threading
import time
from queue import Queue, Empty
from typing import Tuple
from venv import logger

from celery import Celery
from flask import Flask, request, jsonify
from redis import Redis

from message import Message

redis_url = 'redis://localhost:6379/0'
rabbit_url = 'amqp://guest:guest@localhost:5672/'
app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = redis_url
app.config['CELERY_RESULT_BACKEND'] = redis_url

redis = Redis(host='localhost', port=6379, db=0)
celery = Celery(
    app.import_name,
    broker=rabbit_url,
    backend="rpc://",
)

celery.conf.update(
    task_annotations={'*': {'rate_limit': '8/s'}}
)


# limiter = Limiter(
#     get_remote_address,
#     app=celery,
#     default_limits=["500/second"],
#     storage_uri="redis://localhost:6379",
#     storage_options={"socket_connect_timeout": 30},
# )


@celery.task(rate_limit='8/s')
def send_to_receiver(message_data):
    message = Message.from_json(message_data)


def parse_rate(rate: str) -> Tuple[int, int]:
    num, period = rate.split("/")
    num_requests = int(num)
    if len(period) > 1:
        duration_multiplier = int(period[:-1])
        duration_unit = period[-1]
    else:
        duration_multiplier = 1
        duration_unit = period[-1]
    duration_base = {"s": 1, "m": 60, "h": 3600, "d": 86400}[duration_unit]
    duration = duration_base * duration_multiplier
    return num_requests, duration


queue = Queue()


@app.route('/webhook', methods=['POST'])
def webhook():
    response = jsonify(success=True)
    data_json = request.get_json()
    task_id = None

    try:
        message = Message.from_json(data_json)
    except ValueError as err:
        response.status = err
        return response, 200

    logger.info(f"request message: {message}")

    exist = redis.exists(message.message_id)
    if not exist:
        redis.set(message.message_id, message.text, ex=300)

    # task = send_to_receiver.delay(message.to_json())
    # logger.info(f"task: {task}")
    queue.put(message)

    response.headers['X-Celery-ID'] = message.message_id or 'duplicate'
    return response, 200


def process_messages(rate=8):
    while True:
        try:
            message = queue.get(timeout=1)
            send_to_receiver.delay(message.to_json())
            print(f"Processed: {message}")
            time.sleep(1 / rate)
            queue.task_done()
        except Empty:
            print(f"Queue is empty")
            time.sleep(1)
            pass


messages_thread = threading.Thread(target=process_messages)
messages_thread.daemon = True
messages_thread.start()


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
