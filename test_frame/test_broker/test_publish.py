import time

from test_frame.test_broker.test_consume import f, f2

# f.clear()
# f2.clear()
for i in range(200):

    if i == 0:
        print(time.strftime("%H:%M:%S"), 'Publishing first message')
    if i %100 ==  0:
        print(time.strftime("%H:%M:%S"), f'Publishing message {i}')
    f2.push(i, i * 2)
    # f2.push(i, 1 * 2)
    # time.sleep(1)

if __name__ == '__main__':
    pass
    # f.multi_process_pub_params_list([{'a':i,'b':2*i} for i in range(100000)],process_num=5)
