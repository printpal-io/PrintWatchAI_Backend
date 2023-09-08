#!/usr/bin/env python3
import subprocess
import os
import sys
'''
try:
    import fastapi
    import pydantic
    import PIL.Image as Image
    import uvicorn
    import requests
    import typing
    import aiohttp
except:
    os.system("python3 -m pip install --upgrade pip")

    libraries = [
        'fastapi',
        'aiohttp[speedsups]',
        'typing',
        'pydantic',
        'uvicorn',
        'Pillow',
        'requests'
    ]

    for library in libraries:
        subprocess.check_call([sys.executable, "-m", "pip3", "install", library])
'''



from printwatch.core import *

if __name__ == '__main__':
    pfp = PrintFarmPro()
