# Modbus Client

A modern, configurable Modbus client written in Python using the [pymodbus](https://github.com/pymodbus-dev/pymodbus) library. This client can communicate with Modbus devices using both TCP and RTU protocols.

## Features

- **Dual Protocol Support**: TCP and RTU modes using pymodbus
- **Async/Await**: Built with asyncio for non-blocking operations
- **Comprehensive Function Support**: All standard Modbus function codes via pymodbus
- **Device Discovery**: Automatic device scanning and discovery
- **Command Line Interface**: Easy-to-use CLI with extensive options
- **Error Handling**: Robust error handling and timeout management
- **Type Safety**: Full type hints for better development experience
- **Production Ready**: Based on mature pymodbus library (2.5k+ stars)

## Supported Modbus Functions

### Read Operations
- **Read Coils (0x01)**: Read multiple coils (boolean values)
- **Read Discrete Inputs (0x02)**: Read multiple discrete inputs
- **Read Holding Registers (0x03)**: Read multiple holding registers
- **Read Input Registers (0x04)**: Read multiple input registers

### Write Operations
- **Write Single Coil (0x05)**: Write a single coil
- **Write Single Register (0x06)**: Write a single register
- **Write Multiple Coils (0x0F)**: Write multiple coils
- **Write Multiple Registers (0x10)**: Write multiple registers

### Diagnostic Operations
- **Report Slave ID (0x11)**: Get device information
- **Diagnostic Functions (0x08)**: Various diagnostic operations

## Installation

### Prerequisites
- Python 3.7+
- pymodbus with serial support

### Install Dependencies
```bash
# Install pymodbus with serial support
pip install pymodbus[serial]

# Or install from requirements.txt
pip install -r requirements.txt
```

## Usage

### Command Line Interface

The Modbus client provides a comprehensive command-line interface with the following options:

#### Basic Configuration
```bash
# TCP Mode (default)
python modbus_client.py --target 192.168.1.100 --read-holding-registers 0,10

# RTU Mode
python modbus_client.py --mode RTU --target COM3 --read-holding-registers 0,10
```

#### Connection Options
- `--mode`: Modbus mode (TCP or RTU, default: TCP)
- `--target`: Target device IP address (TCP) or serial port (RTU)
- `--target-port`: Target port for TCP mode (default: 502)
- `--unit-id`: Modbus unit ID (default: 1)
- `--timeout`: Request timeout in seconds (default: 10)

#### TCP Mode Options
- `--address`: Local IP address (default: 0.0.0.0)
- `--port`: Local port (default: auto-assign)

#### RTU Mode Options
- `--serial-port`: Serial port for RTU mode
- `--baud-rate`: Baud rate (default: 9600)
- `--data-bits`: Data bits (default: 8)
- `--stop-bits`: Stop bits (default: 1)
- `--parity`: Parity (N, E, O, default: N)

### Operation Examples

#### Device Discovery
```bash
# Discover devices on TCP network
python modbus_client.py --target 192.168.1.100 --discover

# Discover devices on RTU network
python modbus_client.py --mode RTU --target COM3 --discover
```

#### Connection Testing
```bash
# Test TCP connection
python modbus_client.py --target 192.168.1.100 --test-connection

# Test RTU connection
python modbus_client.py --mode RTU --target COM3 --test-connection
```

#### Read Operations
```bash
# Read 10 holding registers starting at address 0
python modbus_client.py --target 192.168.1.100 --read-holding-registers 0,10

# Read 5 coils starting at address 0
python modbus_client.py --target 192.168.1.100 --read-coils 0,5

# Read 8 discrete inputs starting at address 0
python modbus_client.py --target 192.168.1.100 --read-discrete-inputs 0,8

# Read 4 input registers starting at address 0
python modbus_client.py --target 192.168.1.100 --read-input-registers 0,4
```

#### Write Operations
```bash
# Write single register
python modbus_client.py --target 192.168.1.100 --write-register 0,123

# Write single coil (true/false, 1/0, on/off)
python modbus_client.py --target 192.168.1.100 --write-coil 0,true

# Write multiple registers
python modbus_client.py --target 192.168.1.100 --write-multiple-registers 0,100,200,300

# Write multiple coils
python modbus_client.py --target 192.168.1.100 --write-multiple-coils 0,true,false,true,false
```

#### Device Information
```bash
# Read device information
python modbus_client.py --target 192.168.1.100 --read-device-info
```

### Advanced Usage

#### Custom Unit ID
```bash
# Communicate with device at unit ID 5
python modbus_client.py --target 192.168.1.100 --unit-id 5 --read-holding-registers 0,10
```

#### Custom Timeout
```bash
# Set 30-second timeout
python modbus_client.py --target 192.168.1.100 --timeout 30 --read-holding-registers 0,10
```

#### RTU with Custom Serial Settings
```bash
# Use custom baud rate and parity
python modbus_client.py --mode RTU --target COM3 --baud-rate 19200 --parity E --read-holding-registers 0,10
```

## Programmatic Usage

You can also use the Modbus client programmatically:

```python
import asyncio
from modbus_client import ModbusClient

async def main():
    # Create TCP client
    client = ModbusClient(device_type="TCP")
    client.set_target_address("192.168.1.100", 502)
    
    # Start client
    await client.start()
    
    try:
        # Read holding registers
        registers = await client.read_holding_registers("192.168.1.100", 1, 0, 10)
        print(f"Holding registers: {registers}")
        
        # Write single register
        success = await client.write_single_register("192.168.1.100", 1, 0, 123)
        print(f"Write successful: {success}")
        
    finally:
        await client.stop()

# Run the example
asyncio.run(main())
```

## Benefits of Using pymodbus

This client leverages the [pymodbus library](https://github.com/pymodbus-dev/pymodbus) which provides:

- **Mature & Stable**: 2.5k+ stars, active development
- **Comprehensive Support**: Both TCP and RTU modes
- **Multiple Client Types**: Sync, async, and REPL clients
- **Server & Simulator**: Can also create Modbus servers for testing
- **Well Documented**: Extensive documentation and examples
- **Production Ready**: Used in projects like Home Assistant
- **Error Handling**: Comprehensive exception handling
- **Performance**: Optimized for production use

## Error Handling

The client includes comprehensive error handling for common Modbus exceptions:

- **Illegal Function**: Function code not supported by device
- **Illegal Data Address**: Address not accessible
- **Illegal Data Value**: Invalid data value
- **Slave Device Failure**: Device internal error
- **Acknowledge**: Device busy, retry later
- **Slave Device Busy**: Device busy, retry later
- **Memory Parity Error**: Memory error
- **Gateway Path Unavailable**: Gateway error
- **Gateway Target Device Failed to Respond**: Gateway timeout

## Protocol Details

### TCP Mode
- Uses Modbus TCP protocol over Ethernet via pymodbus
- Standard port 502
- Includes transaction ID tracking
- Supports multiple concurrent requests

### RTU Mode
- Uses Modbus RTU protocol over serial via pymodbus
- Configurable serial parameters
- CRC error checking
- Point-to-point communication

## Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Check network connectivity
   - Verify target IP address and port
   - Ensure firewall allows Modbus traffic

2. **No Response from Device**
   - Verify unit ID is correct
   - Check device is powered and connected
   - Try different timeout values

3. **Serial Communication Issues (RTU)**
   - Verify serial port exists
   - Check baud rate matches device
   - Ensure correct parity and stop bits

4. **Invalid Data**
   - Check register addresses are valid
   - Verify data types match expectations
   - Ensure values are within valid ranges

### Debug Mode

For debugging, you can add verbose output by modifying the client code or using Python's logging module.

## Additional pymodbus Features

Since this client uses pymodbus, you can also leverage additional features:

### REPL Client
```bash
# Interactive REPL client
python -m pymodbus.repl --comm tcp --host 192.168.1.100 --port 502
```

### Simulator
```bash
# Start Modbus simulator
python -m pymodbus.simulator
```

### Server
```python
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext

# Create a simple server
store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, [0]*100),
    co=ModbusSequentialDataBlock(0, [0]*100),
    hr=ModbusSequentialDataBlock(0, [0]*100),
    ir=ModbusSequentialDataBlock(0, [0]*100)
)
context = ModbusServerContext(slaves=store, single=True)
StartTcpServer(context, address=("localhost", 502))
```

## Contributing

This Modbus client is part of the KissMyICS project. Contributions are welcome! Please ensure:

- Code follows PEP 8 style guidelines
- All functions have proper type hints
- Error handling is comprehensive
- Tests are included for new features

## License

This project is licensed under the MIT License - see the main project LICENSE file for details. 