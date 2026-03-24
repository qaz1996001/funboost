import urllib3
import json
import nb_log
import decorator_libs

# https://www.cnblogs.com/YrRoom/p/14054282.html

"""
-p 18083 服务器启动端口
-p 1882 TCP端口
-p 8083 WS端口
-p 8084 WSS端口
-p 8883 SSL端口
"""

"""
Ideal for: Frontend subscribes to a unique UUID topic -> form includes this topic name when requesting Python API ->
API publishes tasks to RabbitMQ or Redis message queue -> backend consumer processes execute tasks and publish results
to that unique UUID MQTT topic -> MQTT pushes results to the frontend.

Using AJAX polling or importing WebSocket packages for long-running task interaction with the frontend is suboptimal compared to MQTT.
"""


class MqttHttpHelper(nb_log.LoggerMixin, nb_log.LoggerLevelSetterMixin):

    def __init__(self, mqtt_publish_url='http://127.0.0.1:18083/api/v2/mqtt/publish', user='admin', passwd='public', display_full_msg=False):
        """
        :param mqtt_publish_url: MQTT's HTTP API, built into the MQTT middleware, not a custom implementation. No need to import paho.mqtt.client, just requests/urllib3.
        :param display_full_msg: Whether to print the full published message.
        """
        self._mqtt_publish_url = mqtt_publish_url
        self.http = urllib3.PoolManager()
        self._headers = urllib3.util.make_headers(basic_auth=f'{user}:{passwd}')
        self._headers['Content-Type'] = 'application/json'
        self._display_full_msg = display_full_msg

    # @decorator_libs.tomorrow_threads(10)
    def pub_message(self, topic, msg):
        msg = json.dumps(msg) if isinstance(msg, (dict, list)) else msg
        if not isinstance(msg, str):
            raise Exception('The published message is not a string')
        post_data = {"qos": 1, "retain": False, "topic": topic, "payload": msg}
        try:  # UnicodeEncodeError: 'latin-1' codec can't encode character '\u6211' in position 145: Body ('我') is not valid Latin-1. Use body.encode('utf-8') if you want to send it encoded in UTF-8.
            resp_dict = json.loads(self.http.request('post', self._mqtt_publish_url, body=json.dumps(post_data),
                                                     headers=self._headers).data)
        except UnicodeEncodeError as e:
            self.logger.warning(e)
            post_data['payload'] = post_data['payload'].encode().decode('latin-1')
            resp_dict = json.loads(self.http.request('post', self._mqtt_publish_url, body=json.dumps(post_data),
                                                     headers=self._headers).data)
        if resp_dict['code'] == 0:
            self.logger.debug(f' MQTT publish succeeded, topic: {topic}, length: {len(msg)}, message: {msg if self._display_full_msg else msg[:200]} ')
        else:
            self.logger.debug(f' MQTT publish failed, topic: {topic}, MQTT response: {json.dumps(resp_dict)}, message: {msg if self._display_full_msg else msg[:200]}')


if __name__ == '__main__':
    with decorator_libs.TimerContextManager():
        mp = MqttHttpHelper('http://192.168.6.130:18083/api/v2/mqtt/publish')
        for i in range(2000):
            mp.pub_message('/topic_test_uuid123456', 'msg_test3')
