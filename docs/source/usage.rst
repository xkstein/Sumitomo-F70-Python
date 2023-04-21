Usage
=====

Installation
------------

To install, just install it from pip:

.. code-block:: console

   (.venv) $ pip install sumitomo-f70

Example Usage
-------------

After finding the com port which the helium compressor is attached to, you can access information or send commands like this:

.. code-block:: python
    
   from sumitomo_f70 import SumitomoF70

   with SumitomoF70(com_port='<your com port>') as f70:
       # Insert commands here (full list in docs)
       # For example:
       t1, t2, t3, t4 = f70.read_all_temperatures()
