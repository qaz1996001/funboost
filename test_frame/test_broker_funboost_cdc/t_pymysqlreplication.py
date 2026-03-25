import time

from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import (
    DeleteRowsEvent,
    UpdateRowsEvent,
    WriteRowsEvent,

)

MYSQL_SETTINGS = {"host": "127.0.0.1", "port": 3306, "user": "root", "passwd": "123456"}

stream = BinLogStreamReader(
        connection_settings=MYSQL_SETTINGS,
        server_id=103,
        only_events=[DeleteRowsEvent, UpdateRowsEvent, WriteRowsEvent,],

        # Add these two key parameters
        blocking=True,      # 1. Set to blocking mode to keep waiting for new events
        resume_stream=True, # 2. (Recommended) Allow automatic resumption from last position after disconnection
    )

for binlogevent in stream:
    for row in binlogevent.rows:
        print(row)


