# CALAHAN

Calahan is a Python library to allow connections to financial APIs.

## Logging

Calahan uses Python's standard logging module. To see debug information:

```python
import logging

# Enable Calahan debug logs
logging.basicConfig(level=logging.DEBUG)
# Or just for Calahan:
logging.getLogger('calahan').setLevel(logging.DEBUG)
```
