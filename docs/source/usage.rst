Usage
=====

Installation
------------

To install, just install it from pip:

.. code-block:: console

   (.venv) $ pip install sumitomo-f70

Example Usage
-------------

.. code-block:: python
    
   from sumitomo_f70 import SumitomoF70

   with SumitomoF70(com_port='<your com port>') as f70:
       # Insert code here
       # Example:
       status = f70.read_status_bits()
