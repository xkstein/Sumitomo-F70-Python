# *Unofficial* Sumitomo (SHI) Cryogenics F-70 Helium Compressor Python Driver

Unofficial python driver for monitoring and controlling Sumitomo Cryogenics F-70 Helium Compressors through their serial (RS232) port. Note that this requires firmware version 1.6 or higher.

## Recommended Usage
```python
from shif70 import SHICryoF70

with SHICryoF70(com_port='<your com port>') as f70:
    # Insert code here
    # Example:
    status = f70.read_status_bits()
```
