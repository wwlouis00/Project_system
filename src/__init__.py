"""
__init__ will automatically create directory: para & result
"""

import os

if not os.path.isdir('./para'):
    print("Directory 'para' does not exist.")
    os.mkdir('./para')
    print("Directory 'para' is established.")
if not os.path.isdir('./result'):
    print("Directory 'result' does not exist.")
    os.mkdir('./result')
    print("Directory 'result' is established.")
