import requests
from celery import Celery
from flask import Flask, request, jsonify
from redis import Redis

from message import Message

redis_url = 'redis://redis:6379'
app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = redis_url
app.config['CELERY_RESULT_BACKEND'] = redis_url

celery_app = Celery(app.name)
celery_app.conf.update(
    broker_url=redis_url,
    result_backend=redis_url,
)

redis = Redis(host='redis', port=6379, db=0)

# limiter = Limiter(
#     get_remote_address,
#     app=app,
#     default_limits=["500/second"],
#     storage_uri="redis://localhost:6379",
#     storage_options={"socket_connect_timeout": 30},
# )


@celery_app.task(rate_limit='8/s', bind=True)
def send_to_receiver(self, data):
    headers = {'X-Celery-ID': self.request.id}
    response = requests.post('https://chatbot.com/webhook', json=data, headers=headers)
    return response.status_code


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

    print("request message: ", message)

    if not redis.exists(message.message_id):
        redis.set(message.message_id, message.text, ex=300)
        task = send_to_receiver.delay(data_json)
        task_id = task.id

    response.headers['X-Celery-ID'] = task_id or 'duplicate'
    return response, 200


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
