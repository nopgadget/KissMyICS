# BACnet Client

## Modern Asyncio Implementation

The BACnet client has been updated to use **asyncio** instead of the deprecated **asyncore**-based `bacpypes` library. This ensures compatibility with Python 3.12+ and provides better performance.

## Key Changes

- ✅ **Removed dependency on `bacpypes`** (which uses deprecated asyncore)
- ✅ **Uses Python standard library only** (asyncio, socket, struct)
- ✅ **Modern async/await patterns** for better performance
- ✅ **Future-proof** - compatible with Python 3.12+ and beyond
- ✅ **No external dependencies** required

## Usage

```bash
# Basic device discovery
python protocols/bacnet/bacnet_client.py

# Enumerate devices with detailed information
python protocols/bacnet/bacnet_client.py --enumerate

# Custom device ID and timeout
python protocols/bacnet/bacnet_client.py --device-id 1000 --timeout 15

# Target specific device
python protocols/bacnet/bacnet_client.py --target 192.168.1.100 --enumerate

# Command execution examples
python protocols/bacnet/bacnet_client.py --target 192.168.1.100 --command set_value --value 75.5
python protocols/bacnet/bacnet_client.py --target 192.168.1.100 --command enable --target analogOutput,1
python protocols/bacnet/bacnet_client.py --target 192.168.1.100 --command disable --target analogInput,1
python protocols/bacnet/bacnet_client.py --target 192.168.1.100 --command reset --target device,1

# Device manipulation
python protocols/bacnet/bacnet_client.py --target 192.168.1.100 --operation reinitialize
python protocols/bacnet/bacnet_client.py --target 192.168.1.100 --operation backup
python protocols/bacnet/bacnet_client.py --target 192.168.1.100 --operation set_time

# Object management
python protocols/bacnet/bacnet_client.py --target 192.168.1.100 --create-object analogValue,5
python protocols/bacnet/bacnet_client.py --target 192.168.1.100 --delete-object analogValue,5

# Subscribe to changes
python protocols/bacnet/bacnet_client.py --target 192.168.1.100 --subscribe analogInput,1,presentValue

# Test connection to specific device
python protocols/bacnet/bacnet_client.py --target 172.17.0.2 --test-connection
```

## Features

- **Device Discovery**: Automatically find BACnet devices on the network
- **Property Reading**: Read object properties (presentValue, objectName, etc.)
- **Property Writing**: Write to writable properties (with safety checks)
- **Device Enumeration**: Detailed enumeration of device objects and capabilities
- **Permission Checking**: Test read/write permissions for properties
- **Command Execution**: Execute commands on objects (set_value, enable, disable, reset, acknowledge)
- **Device Manipulation**: Reinitialize, backup, restore, update firmware, set time
- **Object Management**: Create and delete BACnet objects
- **Change Subscription**: Subscribe to property changes (COV - Change of Value)
- **Priority Control**: Write values with priority levels (1-16)
- **Alarm Management**: Acknowledge alarms and manage alarm states

## Architecture

The new implementation uses:

- **`asyncio.DatagramProtocol`** for UDP communication
- **Custom BACnet APDU handling** for protocol messages
- **Type-safe enums** for object types and properties
- **Async/await patterns** throughout the codebase

## Why This Change Was Needed

1. **asyncore Deprecation**: asyncore is deprecated in Python 3.12+ and will be removed in Python 3.14
2. **Performance**: asyncio provides better performance than asyncore
3. **Maintainability**: Modern async patterns are easier to understand and maintain
4. **Future-proofing**: Ensures the code will work with future Python versions

## Migration Notes

The API remains largely the same, but all methods are now `async`:

```python
# Old (sync)
client = BACnetClient()
client.start()
devices = client.discover_devices()

# New (async)
client = BACnetClient()
await client.start()
devices = await client.discover_devices()
```

## Docker Integration

The client works seamlessly with Docker containers:

```bash
# Test connection to Docker BACnet server
python protocols/bacnet/bacnet_client.py --target 172.17.0.2 --test-connection

# Enumerate Docker BACnet server
python protocols/bacnet/bacnet_client.py --target 172.17.0.2 --enumerate
```

## Port Handling

The client automatically handles port conflicts:

- **Auto-assigns ports** when 47808 is in use
- **Works with Docker containers** that use standard BACnet port
- **Custom port specification** via `--port` argument
- **Graceful fallbacks** for port conflicts

## Command Reference

### Basic Commands
- `--enumerate`: Detailed device enumeration
- `--test-connection`: Test direct connection to target
- `--target <ip>`: Specify target device IP
- `--timeout <seconds>`: Discovery timeout
- `--device-id <id>`: Local device ID
- `--port <port>`: Local port (auto-assign if not specified)

### Object Commands
- `--command set_value --value <value>`: Set present value
- `--command enable --target <object>`: Enable object
- `--command disable --target <object>`: Disable object
- `--command reset --target <object>`: Reset object
- `--command acknowledge --target <object>`: Acknowledge alarm

### Device Operations
- `--operation reinitialize`: Reinitialize device
- `--operation backup`: Backup device configuration
- `--operation restore`: Restore device configuration
- `--operation update_firmware`: Update device firmware
- `--operation set_time`: Set device time

### Object Management
- `--create-object <type,instance>`: Create new object
- `--delete-object <type,instance>`: Delete object
- `--subscribe <object,property>`: Subscribe to changes

## Requirements

- Python 3.7+ (for asyncio support)
- No external dependencies required for BACnet client

## Example Scripts

See `example_commands.py` for comprehensive usage examples demonstrating all capabilities.