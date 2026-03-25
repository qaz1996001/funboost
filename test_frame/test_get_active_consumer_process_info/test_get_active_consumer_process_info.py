from funboost import ActiveCousumerProcessInfoGetter

'''
Get consumer process info in a distributed environment.
The 4 methods here require the corresponding function's @boost decorator to set is_send_consumer_heartbeat_to_redis=True,
so that it automatically sends active heartbeats to Redis. Otherwise, consumer process info for that function cannot be queried.
To use the consumer process info statistics feature, users must install Redis regardless of which message queue middleware type they use,
and configure the Redis connection info in funboost_config.py.
'''

# Get all consumer info for the test_queue queue in a distributed environment
print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_queue_name('test_queue'))

# Get all consumer info for the current machine in a distributed environment
print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_ip())

# Get all consumer info for the specified IP in a distributed environment
print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_by_ip('10.0.195.220'))

# Get all consumer info for all queues in a distributed environment, partitioned by queue name
print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_queue_name())

# Get all consumer info for all machines in a distributed environment, partitioned by IP
print(ActiveCousumerProcessInfoGetter().get_all_hearbeat_info_partition_by_ip())