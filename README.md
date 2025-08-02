# KissMyICS - Industrial Control System Protocol Tools

A collection of tools for interacting with various industrial control system protocols.

## Protocols

### BACnet Client
Modern asyncio-based BACnet client with comprehensive device discovery, enumeration, and manipulation capabilities.

**📖 [Full Documentation](protocols/bacnet/BACNET.md)**

**Quick Start:**
```bash
# Test connection to BACnet device
python protocols/bacnet/bacnet_client.py --target 192.168.1.100 --test-connection

# Enumerate device capabilities
python protocols/bacnet/bacnet_client.py --target 192.168.1.100 --enumerate

# Execute commands
python protocols/bacnet/bacnet_client.py --target 192.168.1.100 --command set_value --value 75.5
```

**Key Features:**
- ✅ Modern asyncio implementation (no deprecated asyncore)
- ✅ Docker container support
- ✅ Auto-port assignment for port conflicts
- ✅ Comprehensive command and manipulation capabilities
- ✅ No external dependencies

### Modbus Client
Modern Modbus client using pymodbus library with support for both TCP and RTU modes.

**📖 [Full Documentation](protocols/modbus/README.md)**

**Quick Start:**
```bash
# Test connection to Modbus device
python protocols/modbus/modbus_client.py --target 192.168.1.100 --test-connection

# Read holding registers
python protocols/modbus/modbus_client.py --target 192.168.1.100 --read-holding-registers 0,10

# Write single register
python protocols/modbus/modbus_client.py --target 192.168.1.100 --write-register 0,123

# Discover devices
python protocols/modbus/modbus_client.py --target 192.168.1.100 --discover
```

**Key Features:**
- ✅ TCP and RTU mode support
- ✅ Comprehensive Modbus function support
- ✅ Device discovery capabilities
- ✅ Version-compatible pymodbus integration
- ✅ Async/await support

### Planned Protocols
Additional protocol implementations are planned for:
- DNP3
- EtherCAT
- S7comm
- And more...

## Requirements

- Python 3.7+ (for asyncio support)
- `pymodbus[serial]>=3.5.0` (for Modbus client)
- No other external dependencies required
