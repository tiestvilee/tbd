#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Gitless - a version control system built on top of Git
# Licensed under MIT

# This file is for PyInstaller

import sys

from tbd.cli import tbd


if __name__ == '__main__':
  sys.exit(tbd.main())
