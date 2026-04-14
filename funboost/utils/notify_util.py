import requests
import json
import inspect

from typing import Optional
from funboost.core.loggers import logger_notify

logger = logger_notify

class Notifier:
    """
    Enterprise message push utility, supports DingTalk, WeCom (WeChat Work), and Feishu (Lark) bots.
    """

    def __init__(self,
                 dingtalk_webhook: Optional[str] = None,
                 wechat_webhook: Optional[str] = None,
                 feishu_webhook: Optional[str] = None):
        """
        Initialize the notifier with optional default Webhooks for each platform.

        :param dingtalk_webhook: DingTalk bot Webhook URL
        :param wechat_webhook:  WeCom bot Webhook URL
        :param feishu_webhook:  Feishu (Lark) bot Webhook URL
        """
        self.dingtalk_webhook = dingtalk_webhook
        self.wechat_webhook = wechat_webhook
        self.feishu_webhook = feishu_webhook

    def _get_caller_info(self) -> str:
        """Get the caller's file path and line number"""
        try:
            # Get the call stack, skip the current method and the send method
            frame = inspect.currentframe()
            caller_frame = frame.f_back.f_back

            # Get file path and line number
            filename = caller_frame.f_code.co_filename
            lineno = caller_frame.f_lineno

            # Simplify file path, show only the last two directory levels
            parts = filename.split('/')
            if len(parts) >= 2:
                short_path = '/'.join(parts[-2:])
            else:
                short_path = filename
            
            return f"{short_path}:{lineno}"
        except Exception:
            return "unknown:0"

    def send_dingtalk(self, message: str, webhook: Optional[str] = None, add_caller_info: bool = True) -> bool:
        """
        Send a DingTalk text message.

        :param message: Message content
        :param webhook: Optional, overrides the default Webhook set during initialization
        :param add_caller_info: Whether to automatically add caller info (file path and line number), default True
        :return: Whether the send was successful
        """
        url = webhook or self.dingtalk_webhook
        if not url:
            raise ValueError("DingTalk Webhook not configured")

        if add_caller_info:
            caller_info = self._get_caller_info()
            message = f"{message}\n\n📍Sent from: {caller_info}"

        logger.warning(f"Sending DingTalk message: {message} ")

        payload = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        return self._post(url, payload)

    def send_wechat(self, message: str, webhook: Optional[str] = None, add_caller_info: bool = True) -> bool:
        """
        Send a WeCom (WeChat Work) text message.

        :param message: Message content
        :param webhook: Optional, overrides the default Webhook set during initialization
        :param add_caller_info: Whether to automatically add caller info (file path and line number), default True
        :return: Whether the send was successful
        """
        url = webhook or self.wechat_webhook
        if not url:
            raise ValueError("WeCom Webhook not configured")

        if add_caller_info:
            caller_info = self._get_caller_info()
            message = f"{message}\n\n📍Sent from: {caller_info}"

        logger.warning(f"Sending WeCom message: {message}")

        payload = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        return self._post(url, payload)

    def send_feishu(self, message: str, webhook: Optional[str] = None, add_caller_info: bool = True) -> bool:
        """
        Send a Feishu (Lark) text message.

        :param message: Message content
        :param webhook: Optional, overrides the default Webhook set during initialization
        :param add_caller_info: Whether to automatically add caller info (file path and line number), default True
        :return: Whether the send was successful
        """
        url = webhook or self.feishu_webhook
        if not url:
            raise ValueError("Feishu Webhook not configured")

        if add_caller_info:
            caller_info = self._get_caller_info()
            message = f"{message}\n\n📍Sent from: {caller_info}"

        logger.warning(f"Sending Feishu message: {message} ")

        payload = {
            "msg_type": "text",
            "content": {
                "text": message
            }
        }
        return self._post(url, payload)

    def _post(self, url: str, payload: dict) -> bool:
        """Internal method: send POST request and check response"""
        try:
            headers = {'Content-Type': 'application/json'}
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
            resp.raise_for_status()
            result = resp.json()
            # Different platforms have slightly different response formats; usually errcode/code == 0 means success
            if result.get('errcode') == 0 or result.get('code') == 0:
                return True
            # Feishu returns StatusCode 0 on success instead of errcode
            if result.get('StatusCode') == 0:
                return True
            # Print error message for debugging
            print(f"Send failed: {result}")
            return False
        except Exception as e:
            print(f"Request exception: {e}")
            return False


# ========== Usage Example ==========
if __name__ == '__main__':
    # 1. Configure default Webhooks during initialization
    notifier = Notifier(
        dingtalk_webhook='https://oapi.dingtalk.com/robot/send?access_token=your_token',
        wechat_webhook='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your_key',
        feishu_webhook='https://open.feishu.cn/open-apis/bot/v2/hook/your_webhook'
    )

    # 2. Send messages (using default config, automatically adds caller info)
    # notifier.send_dingtalk("DingTalk message test")
    notifier.send_wechat("WeCom message test")
    # notifier.send_feishu("Feishu message test")

    # 3. You can also temporarily specify a different Webhook to override the default
    # notifier.send_dingtalk("Temporary message", webhook="https://another-dingtalk-bot")

    # 4. You can disable automatic caller info
    # notifier.send_wechat("Message without location", add_caller_info=False)
