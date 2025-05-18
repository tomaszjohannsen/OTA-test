import sys
import os

__version__ = '1.0.1'

print(f'version: {__version__}')

if __version__ != '0.0.0':
    print('should have checked __main__')
