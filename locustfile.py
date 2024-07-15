import random
import uuid

from locust import HttpUser, TaskSet, task, between, constant_pacing


class UserBehavior(TaskSet):

    @task(1)
    def post_message(self):
        headers = {'Content-Type': 'application/json'}
        data = {
            "from_id": 12345,
            "message_id": "random.randint(1, 1000)",
            "text": "str(uuid.uuid4())"
        }
        self.client.post("/webhook", json=data, headers=headers)


class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = constant_pacing(1)
