# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/1/13 0013 9:15
print('Test that before importing the framework, print should be white, and in the console it is unclear which file/line the print comes from')

# Once the framework is imported anywhere, print in any module of the project automatically changes. All subsequent prints will have color & clickable links. Print color change and log color change are independent and can be selected as needed.
from funboost import LogManager

print('After importing utils_ydf, a monkey patch is automatically applied to print. This line color should have changed, and it is clickable/jumpable in PyCharm')

logger = LogManager('lalala').get_logger_and_add_handlers()

for i in range(3):
    logger.debug(f'Testing debug color with monokai theme in console {i}')
    logger.info(f'Testing info color with monokai theme in console {i}')
    logger.warning(f'Testing warning color with monokai theme in console {i}')
    logger.error(f'Testing error color with monokai theme in console {i}')
    logger.critical(f'Testing critical error color with monokai theme in console {i}')
    print(f'Direct print will also have color and auto-jump because of the monkey patch {i}')



# print('''File "D:/coding2/distributed_framework/test_frame/other_tests/test_color.py", line ''')
#
# print('''"D:/coding2/distributed_framework/test_frame/other_tests/test_color.py"''')
#
# raise Exception('aaaaaaaa')
