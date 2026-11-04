# -*- coding: utf-8 -*-
"""Check if Ollama service is running. Called by the start bat.

Exit code: 0 = running, 1 = not running.
ASCII only - must work under any console code page.
"""
import sys
import urllib.request

try:
    urllib.request.urlopen("http://127.0.0.1:11434/api/version", timeout=2)
    sys.exit(0)
except Exception:
    sys.exit(1)
