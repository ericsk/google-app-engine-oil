#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" The entry point. """

import os
import sys
import settings

PATHS = [settings.APP_DIR, 'lib', os.path.join('lib', 'gaeo')]

def safe_append(path):
    if path not in sys.path:
        sys.path.append(path)

def main():
    cur_path = os.path.dirname(__file__)
    safe_append(cur_path)
    
    for p in PATHS:
        path = os.path.join(cur_path, p)
        safe_append(path)
    
    from gaeo.app import GaeoApp, start_app
    application = GaeoApp()
    start_app(application)

if __name__ == '__main__':
    main()
