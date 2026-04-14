from test_frame.test_distributed_turn_run.run_distribute_msg import build_booster_really_execute_msg_on_host_by_ip, ip_102,get_current_ip

"""
Currently simulating on a single machine the requirement: "two machines alternately run messages, with only one
machine executing messages at a time, and only one message executed at a time -- concurrent execution of messages
is not allowed". In practice, the current machine's IP is dynamically obtained automatically, so the two
duplicate files run_execute_msg_on_host101.py and run_execute_msg_on_host102.py are not needed.
"""

booster_execute_msg_on_host = build_booster_really_execute_msg_on_host_by_ip(get_current_ip(ip_102))

if __name__ == '__main__':
    booster_execute_msg_on_host.fabric_deploy(0,0,0,0)

    """
    This is the real message executor, deployed on each machine.
    """
