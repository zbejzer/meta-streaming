#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, ".")

try:
    from metastreaming import main

    main()
except SystemExit:
    raise  # Normal application exit
except:
    raise
