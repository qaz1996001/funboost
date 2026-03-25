import time

from funboost import boost, BoostersManager, BoosterParams, ConcurrentModeEnum, BrokerEnum


def gen_queue_name_by_ip(queue_namex, ip):
    return queue_namex + '-' + ip.replace(".", "_")


def get_current_ip(ip=None):
    return ip  # In practice, this would automatically get the current machine's IP without parameters; in the author's example, two scripts run on one machine simulating two machines, so a parameter is needed.


ip_101 = '192.168.1.101b'
ip_102 = '192.168.1.102b'
ip_list = [ip_101, ip_102]


class GlobalVars:
    i = -1


@boost(BoosterParams(queue_name='queue1', concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD, broker_kind=BrokerEnum.REDIS))
def distribute_msg(x):
    """Distribute messages to each machine in turn, blocking until function completes before distributing the next task to the next machine"""
    GlobalVars.i += 1
    ip = ip_list[GlobalVars.i % len(ip_list)]  # Round-robin push messages to each machine's queue
    booster = build_booster_really_execute_msg_on_host_by_ip(ip)
    async_result = booster.push(x)
    # async_result.set_timeout(10)
    """
    Using async_result.get() RPC mode to block until the really_execute_msg_on_host function finishes
    processing the message. Combined with distribute_msg's single-thread mode, this guarantees that
    only one machine at a time uses really_execute_msg_on_host to process messages from queue1.
    """
    print(async_result.get()) # This line blocks until the message finishes running in really_execute_msg_on_host.


def really_execute_msg_on_host(x):
    """Actually execute messages; this function runs on each machine in turn."""
    time.sleep(5)
    print(x)
    return f'{x} finish from ip_xx '


def build_booster_really_execute_msg_on_host_by_ip(ip):
    return BoostersManager.build_booster(BoosterParams(queue_name=gen_queue_name_by_ip('queue2', ip),
                                                       concurrent_mode=ConcurrentModeEnum.SINGLE_THREAD,
                                                       is_using_rpc_mode=True,
                                                       broker_kind=BrokerEnum.REDIS,
                                                       consuming_function=really_execute_msg_on_host,
                                                       ))


if __name__ == '__main__':
    distribute_msg.clear()
    for i in range(10):
        distribute_msg.push(i)
    distribute_msg.consume()
    """
    This message dispatcher is deployed on one machine.
    """