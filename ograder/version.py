__version__ = '0.0.1'

import sys

from textwrap import dedent

LOGO_WITH_VERSION = fr"""
  _________       ______ 
 /  _____  \     /   __ \ 
|  /     \  |   / /    \_|
| |       | |  | |        
| |       | |  | |   ___  
| |       | |  |  \  \  \ 
|  \_____/  |   \  \__\  |
 \_________/     \_______|
                           v{__version__}
"""[1:]                

def print_version_info(logo=False):
    """
    Prints the ograder logo and version information to stdout
    Args:
        logo (``bool``, optional): whether to print the logo
    """
    if logo:
        print(LOGO_WITH_VERSION)
    print(dedent(f"""\
        Python version: {".".join(str(v) for v in sys.version_info[:3])}
        ograder version: {__version__}"""))