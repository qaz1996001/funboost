import dataset
from typing import Dict

class MySql2Mysql:
    """
    Uses dataset to save MySQL binlog message data to a target database.
    With this contrib class, users only need one line of code to implement mysql2mysql via CDC,
    making it very convenient to automatically sync source table A from database instance 1
    to target table A in database instance 2 in real time.

    This is just a contrib class. Users can insert into tables or clean data however they want.
    This example shows how dataset conveniently saves a dictionary as a row in MySQL.
    Users can also customize bulk inserts into target tables. This class is not required; it serves as a demonstration.
    """
    def __init__(self, primary_key: str,
                 target_table_name: str,
                 target_sink_db: dataset.Database, ):
        self.primary_key = primary_key
        self.target_table_name = target_table_name
        self.target_sink_db = target_sink_db

    def sync_data(self, event_type: str,
                  schema: str,
                  table: str,
                  timestamp: int,
                  row_data: Dict, ):
        # For example, insert the data from this table as-is into testdb7.users
        target_table: dataset.Table = self.target_sink_db[self.target_table_name]  # dataset automatically gets or creates the table by name
        print(f"Received event: {event_type} on schema: {schema},  table: {table}, timestamp: {timestamp}")

        if event_type == 'INSERT':
            # `row_data` contains the 'values' dictionary
            data_to_insert = row_data['values']
            target_table.upsert(data_to_insert, [self.primary_key])
            print(f"  [INSERT] Successfully synced data: {data_to_insert}")

        elif event_type == 'UPDATE':
            # `row_data` contains 'before_values' and 'after_values'
            data_to_update = row_data['after_values']
            target_table.upsert(data_to_update, [self.primary_key])
            print(f"  [UPDATE] Successfully synced data: {data_to_update}")

        elif event_type == 'DELETE':
            # `row_data` contains the 'values' dictionary, i.e. the data of the deleted row
            data_to_delete = row_data['values']
            target_table.delete(**{self.primary_key: data_to_delete[self.primary_key]})
            print(f"  [DELETE] Successfully synced data: {data_to_delete}")