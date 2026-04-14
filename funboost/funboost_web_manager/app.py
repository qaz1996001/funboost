"""
The main purpose of this file is to maintain backward compatibility for the old import style:
from funboost.funboost_web_manager import xx
"""

from funboost.funweb.app import *



if __name__ == "__main__":
    start_funboost_web_manager(debug=False)