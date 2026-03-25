"""
This code demonstrates funboost's powerful message format compatibility: it can consume any
non-standard messages already in a queue (even if the format is not JSON).
Regardless of whether you use funboost to publish messages, and regardless of whether
your messages are in JSON format, funboost can still consume them.
By user-defining _user_convert_msg_before_run to clean and convert messages to a dict or
JSON string, funboost can consume any message.
This is a niche requirement, but funboost easily surpasses celery in terms of simplicity
when it comes to consuming arbitrary messages.
"""

import typing
import redis
from funboost import BrokerEnum, BoosterParams, AbstractConsumer


class MyAnyMsgConvetConsumer(AbstractConsumer):
    def _user_convert_msg_before_run(self, msg) -> typing.Union[dict,str]:
        # 'a=1,b=2' e.g. extract key-value pairs from this string and return a dict to fit funboost consumption
        new_msg_dict = {}
        msg_split_list = msg.split(',')
        for item in msg_split_list:
            key, value = item.split('=')
            new_msg_dict[key] = int(value)
        self.logger.debug(f'Original message: {msg}, converted new message: {new_msg_dict}')  # e.g. actually prints: Original message: a=3,b=4, converted new message: {'a': 3, 'b': 4}
        return new_msg_dict


@BoosterParams(queue_name="task_queue_consume_any_msg", broker_kind=BrokerEnum.REDIS,
               consumer_override_cls=MyAnyMsgConvetConsumer  # This line is key; MyAnyMsgConvetConsumer defines _user_convert_msg_before_run where users can freely clean and convert messages
               )
def task_fun(a: int, b: int):
    print(f'a:{a},b:{b}')
    return a + b


if __name__ == "__main__":
    redis_conn = redis.Redis(db=7)  # Use native redis to publish messages; funboost can still consume them.

    redis_conn.lpush('task_queue_consume_any_msg', 'a=1,b=2')  # Simulate another team member manually sending a message format that funboost cannot recognize; funboost normally needs JSON, but the other team sent a raw string to the queue.
    task_fun.publisher.send_msg('a=3,b=4')  # Using send_msg instead of push/publish to intentionally send a non-standard message; this sends the raw message to the queue without funboost adding any auxiliary fields like task_id or publish time.

    task_fun.consume()  # funboost can now consume non-standard messages in the queue because the user cleaned them in _user_convert_msg_before_run
