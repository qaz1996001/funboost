from funboost.utils.notify_util import Notifier

from dotenv import load_dotenv
import os
load_dotenv('/my_dotenv.env')

notifier = Notifier(
    wechat_webhook=os.getenv('QYWEIXIN_WEBHOOK')
)

# 2. Send message (using default config, automatically adds caller info)
# notifier.send_dingtalk("DingTalk message test")
notifier.send_wechat("WeChat Work message test")