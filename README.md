# *Unofficial* Sumitomo (SHI) Cryogenics F-70 Helium Compressor Python Driver

Unofficial python driver for monitoring and controlling Sumitomo Cryogenics F-70 Helium Compressors through their serial (RS232) port. 

**NOTE:** this requires firmware version 1.6 or higher.

## Example Usage

```python
from sumitomo_f70 import SumitomoF70

with SumitomoF70(com_port='<your com port>') as f70:
    # Insert commands here (full list in docs)
    # For example:
    t1, t2, t3, t4 = f70.read_all_temperatures()
```

Complete documentation can be found [here](https://xkstein.github.io/Sumitomo-F70-Python/)

## Installation

This package can be installed using [pip](https://pypi.org/project/sumitomo-f70/)

```
pip install sumitomo-f70
```
