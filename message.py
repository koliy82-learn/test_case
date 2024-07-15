import pika


class Message:
    def __init__(self, message_id, text, from_id):
        self.message_id = message_id
        self.text = text
        self.from_id = from_id

    @classmethod
    def from_json(cls, json_data):
        if 'message_id' not in json_data:
            raise ValueError("Incorrect model (field message_id must be set)")
        if 'text' not in json_data:
            raise ValueError("Incorrect model (field text must be set)")
        return Message(
            from_id=json_data.get('from_id'),
            message_id=json_data.get('message_id'),
            text=json_data.get('text')
        )

    def __str__(self):
        return f"№{self.message_id} text: {self.text} by user_id: {self.from_id}"

    def to_json(self):
        return {
            'message_id': self.message_id,
            'text': self.text
        }