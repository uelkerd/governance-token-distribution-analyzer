#!/usr/bin/env python3
"""Test script to verify all dependencies are working."""

import sys
import os

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Virtual environment: {os.environ.get('VIRTUAL_ENV', 'Not activated')}")
print(f"Python path: {sys.path[:3]}...")

try:
    import numpy
    print(f"✓ numpy {numpy.__version__}")
except ImportError as e:
    print(f"✗ numpy: {e}")

try:
    import pandas
    print(f"✓ pandas {pandas.__version__}")
except ImportError as e:
    print(f"✗ pandas: {e}")

try:
    import requests
    print(f"✓ requests {requests.__version__}")
except ImportError as e:
    print(f"✗ requests: {e}")

try:
    import web3
    print(f"✓ web3 {web3.__version__}")
except ImportError as e:
    print(f"✗ web3: {e}")

try:
    import eth_account
    print(f"✓ eth_account {eth_account.__version__}")
except ImportError as e:
    print(f"✗ eth_account: {e}")

print("Test completed!") 