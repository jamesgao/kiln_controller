Firmware
========

The kiln controller circuit communicates with the raspberry pi using an I2C bus. This allows multiple connectors to be stacked to enable more controllers and feedback circuits.

Communication protocol
----------------------

| Register   | Input      | Meaning           |
|------------|------------|-------------------|
| `ord('I')` | True/False | Toggle ignition   |
| `ord('M')` | Integer    | Move motor        |
| `ord('F')` | None       | Show flame status |
