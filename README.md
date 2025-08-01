# KissMyICS - Industrial Control System Protocol Tools

A collection of tools for interacting with various industrial control system protocols.

## Protocols

### BACnet Client
Modern asyncio-based BACnet client with comprehensive device discovery, enumeration, and manipulation capabilities.

**📖 [Full Documentation](protocols/bacnet/bacnet.md)**

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

### Planned Protocols
Additional protocol implementations are planned for:
- Modbus
- DNP3
- EtherCAT
- And more...

## Requirements

- Python 3.7+ (for asyncio support)
- No external dependencies required
