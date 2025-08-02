#!/usr/bin/env python3
"""
Modern Modbus Client Script using pymodbus
A Python script to interact with Modbus servers using pymodbus library
Supports both TCP and RTU modes
"""

import asyncio
import argparse
import sys
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

# Import pymodbus components
try:
    from pymodbus.client import ModbusTcpClient, ModbusSerialClient
    from pymodbus.exceptions import ModbusException, ConnectionException
    from pymodbus.pdu import ExceptionResponse
    PYMODBUS_AVAILABLE = True
except ImportError as e:
    print(f"Error: pymodbus not installed or import failed: {e}")
    print("Please install with: pip install pymodbus[serial]")
    sys.exit(1)

# Optional imports for additional features
try:
    from pymodbus.repl import ModbusRplClient
    from pymodbus.simulator import ModbusSimulator
    REPL_AVAILABLE = True
except ImportError:
    REPL_AVAILABLE = False

class ModbusFunctionCode(Enum):
    """Modbus function codes"""
    READ_COILS = 0x01
    READ_DISCRETE_INPUTS = 0x02
    READ_HOLDING_REGISTERS = 0x03
    READ_INPUT_REGISTERS = 0x04
    WRITE_SINGLE_COIL = 0x05
    WRITE_SINGLE_REGISTER = 0x06
    WRITE_MULTIPLE_COILS = 0x0F
    WRITE_MULTIPLE_REGISTERS = 0x10
    READ_WRITE_MULTIPLE_REGISTERS = 0x17
    DIAGNOSTIC = 0x08
    GET_COM_EVENT_COUNTER = 0x0B
    GET_COM_EVENT_LOG = 0x0C
    REPORT_SLAVE_ID = 0x11
    READ_FILE_RECORD = 0x14
    WRITE_FILE_RECORD = 0x15
    MASK_WRITE_REGISTER = 0x16
    READ_FIFO_QUEUE = 0x18
    ENCAPSULATED_INTERFACE_TRANSPORT = 0x2B

class ModbusExceptionCode(Enum):
    """Modbus exception codes"""
    ILLEGAL_FUNCTION = 0x01
    ILLEGAL_DATA_ADDRESS = 0x02
    ILLEGAL_DATA_VALUE = 0x03
    SLAVE_DEVICE_FAILURE = 0x04
    ACKNOWLEDGE = 0x05
    SLAVE_DEVICE_BUSY = 0x06
    MEMORY_PARITY_ERROR = 0x08
    GATEWAY_PATH_UNAVAILABLE = 0x0A
    GATEWAY_TARGET_DEVICE_FAILED_TO_RESPOND = 0x0B

@dataclass
class ModbusDevice:
    """Represents a Modbus device"""
    unit_id: int
    address: str
    port: int = 502
    device_type: str = "TCP"
    baud_rate: int = 9600
    data_bits: int = 8
    stop_bits: int = 1
    parity: str = "N"

class ModbusClient:
    """Modern Modbus client using pymodbus library"""
    
    def __init__(self, device_type: str = "TCP", 
                 local_address: str = '0.0.0.0', local_port: int = None,
                 serial_port: str = None, baud_rate: int = 9600,
                 data_bits: int = 8, stop_bits: int = 1, parity: str = "N"):
        self.device_type = device_type.upper()
        self.local_address = local_address
        self.local_port = local_port
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.data_bits = data_bits
        self.stop_bits = stop_bits
        self.parity = parity
        
        # pymodbus client objects
        self.tcp_client = None
        self.serial_client = None
        self.client = None
        
    async def start(self) -> bool:
        """Start the Modbus client"""
        try:
            if self.device_type == "TCP":
                # TCP client will be created when target is set
                print(f"Modbus TCP client configured")
            else:
                # Create RTU client
                self.serial_client = ModbusSerialClient(
                    method='rtu',
                    port=self.serial_port,
                    baudrate=self.baud_rate,
                    bytesize=self.data_bits,
                    stopbits=self.stop_bits,
                    parity=self.parity
                )
                self.client = self.serial_client
                print(f"Modbus RTU client configured for {self.serial_port}")
                print(f"  Baud rate: {self.baud_rate}")
                print(f"  Data bits: {self.data_bits}")
                print(f"  Stop bits: {self.stop_bits}")
                print(f"  Parity: {self.parity}")
            
            return True
        except Exception as e:
            print(f"Failed to start Modbus client: {e}")
            return False
    
    def set_target_address(self, address: str, port: int = 502) -> None:
        """Set target device address"""
        self.target_address = address
        self.target_port = port
        
        # Create TCP client with target address and port
        if self.device_type == "TCP":
            self.tcp_client = ModbusTcpClient(host=address, port=port)
            self.client = self.tcp_client
            print(f"Target set to {address}:{port}")
    
    async def connect(self) -> bool:
        """Connect to the Modbus device"""
        try:
            if self.client:
                return self.client.connect()
            return False
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from the Modbus device"""
        if self.client:
            self.client.close()
    
    async def discover_devices(self, start_unit_id: int = 1, end_unit_id: int = 247,
                             timeout: int = 5) -> List[ModbusDevice]:
        """Discover Modbus devices on the network"""
        devices = []
        
        if not await self.connect():
            print("Failed to connect for device discovery")
            return devices
        
        try:
            print(f"Scanning for Modbus devices...")
            
            for unit_id in range(start_unit_id, end_unit_id + 1):
                try:
                    # Try to read device ID or a single register
                    result = self._call_modbus_method('read_holding_registers', 0, count=1, unit_id=unit_id)
                    
                    if result and not result.isError():
                        device = ModbusDevice(
                            unit_id=unit_id,
                            address=self.target_address if hasattr(self, 'target_address') else self.serial_port,
                            port=self.target_port if hasattr(self, 'target_port') else None,
                            device_type=self.device_type,
                            baud_rate=self.baud_rate,
                            data_bits=self.data_bits,
                            stop_bits=self.stop_bits,
                            parity=self.parity
                        )
                        devices.append(device)
                        print(f"  Found device with unit ID: {unit_id}")
                        
                except Exception:
                    # Device not responding or doesn't exist
                    pass
                    
        finally:
            await self.disconnect()
        
        return devices
    
    async def read_coils(self, target_address: str, unit_id: int, 
                        start_address: int, count: int, timeout: int = 10) -> Optional[List[bool]]:
        """Read coils (0x01)"""
        try:
            if not await self.connect():
                return None
            
            result = self._call_modbus_method('read_coils', start_address, count=count, unit_id=unit_id)
            if result and not result.isError():
                return result.bits[:count]
            return None
        except Exception as e:
            print(f"Error reading coils: {e}")
            return None
        finally:
            await self.disconnect()
    
    async def read_discrete_inputs(self, target_address: str, unit_id: int,
                                 start_address: int, count: int, timeout: int = 10) -> Optional[List[bool]]:
        """Read discrete inputs (0x02)"""
        try:
            if not await self.connect():
                return None
            
            result = self._call_modbus_method('read_discrete_inputs', start_address, count=count, unit_id=unit_id)
            if result and not result.isError():
                return result.bits[:count]
            return None
        except Exception as e:
            print(f"Error reading discrete inputs: {e}")
            return None
        finally:
            await self.disconnect()
    
    async def read_holding_registers(self, target_address: str, unit_id: int,
                                   start_address: int, count: int, timeout: int = 10) -> Optional[List[int]]:
        """Read holding registers (0x03)"""
        try:
            if not await self.connect():
                return None
            
            result = self._call_modbus_method('read_holding_registers', start_address, count=count, unit_id=unit_id)
            if result and not result.isError():
                return result.registers
            return None
        except Exception as e:
            print(f"Error reading holding registers: {e}")
            return None
        finally:
            await self.disconnect()
    
    async def read_input_registers(self, target_address: str, unit_id: int,
                                 start_address: int, count: int, timeout: int = 10) -> Optional[List[int]]:
        """Read input registers (0x04)"""
        try:
            if not await self.connect():
                return None
            
            result = self._call_modbus_method('read_input_registers', start_address, count=count, unit_id=unit_id)
            if result and not result.isError():
                return result.registers
            return None
        except Exception as e:
            print(f"Error reading input registers: {e}")
            return None
        finally:
            await self.disconnect()
    
    async def write_single_coil(self, target_address: str, unit_id: int,
                              address: int, value: bool, timeout: int = 10) -> bool:
        """Write single coil (0x05)"""
        try:
            if not await self.connect():
                return False
            
            result = self._call_modbus_method('write_coil', address, value, unit_id=unit_id)
            return result and not result.isError()
        except Exception as e:
            print(f"Error writing single coil: {e}")
            return False
        finally:
            await self.disconnect()
    
    async def write_single_register(self, target_address: str, unit_id: int,
                                  address: int, value: int, timeout: int = 10) -> bool:
        """Write single register (0x06)"""
        try:
            if not await self.connect():
                return False
            
            result = self._call_modbus_method('write_register', address, value, unit_id=unit_id)
            return result and not result.isError()
        except Exception as e:
            print(f"Error writing single register: {e}")
            return False
        finally:
            await self.disconnect()
    
    async def write_multiple_coils(self, target_address: str, unit_id: int,
                                 start_address: int, values: List[bool], timeout: int = 10) -> bool:
        """Write multiple coils (0x0F)"""
        try:
            if not await self.connect():
                return False
            
            result = self._call_modbus_method('write_coils', start_address, values, unit_id=unit_id)
            return result and not result.isError()
        except Exception as e:
            print(f"Error writing multiple coils: {e}")
            return False
        finally:
            await self.disconnect()
    
    async def write_multiple_registers(self, target_address: str, unit_id: int,
                                     start_address: int, values: List[int], timeout: int = 10) -> bool:
        """Write multiple registers (0x10)"""
        try:
            if not await self.connect():
                return False
            
            result = self._call_modbus_method('write_registers', start_address, values, unit_id=unit_id)
            return result and not result.isError()
        except Exception as e:
            print(f"Error writing multiple registers: {e}")
            return False
        finally:
            await self.disconnect()
    
    async def read_device_info(self, target_address: str, unit_id: int, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """Read device information using diagnostic functions"""
        try:
            if not await self.connect():
                return None
            
            # Try to read device ID using Report Slave ID function
            result = self._call_modbus_method('read_holding_registers', 0, count=1, unit_id=unit_id)
            if result and not result.isError():
                return {
                    'unit_id': unit_id,
                    'status': 'online',
                    'registers_accessible': True
                }
            return None
        except Exception as e:
            print(f"Error reading device info: {e}")
            return None
        finally:
            await self.disconnect()
    
    async def test_connection(self, target_address: str, unit_id: int = 1, timeout: int = 5) -> bool:
        """Test connection to a Modbus device"""
        try:
            if not await self.connect():
                return False
            
            # Try to read a single register
            result = self._call_modbus_method('read_holding_registers', 0, count=1, unit_id=unit_id)
            return result and not result.isError()
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
        finally:
            await self.disconnect()
    
    async def stop(self) -> None:
        """Stop the Modbus client"""
        await self.disconnect()
        print("Modbus client stopped")

    def _call_modbus_method(self, method_name: str, *args, unit_id: int = 1, **kwargs):
        """Call pymodbus method with version-compatible parameters"""
        try:
            # Try with unit_id parameter (newer versions)
            if method_name == 'read_coils':
                return self.client.read_coils(*args, unit_id=unit_id, **kwargs)
            elif method_name == 'read_discrete_inputs':
                return self.client.read_discrete_inputs(*args, unit_id=unit_id, **kwargs)
            elif method_name == 'read_holding_registers':
                return self.client.read_holding_registers(*args, unit_id=unit_id, **kwargs)
            elif method_name == 'read_input_registers':
                return self.client.read_input_registers(*args, unit_id=unit_id, **kwargs)
            elif method_name == 'write_coil':
                return self.client.write_coil(*args, unit_id=unit_id, **kwargs)
            elif method_name == 'write_register':
                return self.client.write_register(*args, unit_id=unit_id, **kwargs)
            elif method_name == 'write_coils':
                return self.client.write_coils(*args, unit_id=unit_id, **kwargs)
            elif method_name == 'write_registers':
                return self.client.write_registers(*args, unit_id=unit_id, **kwargs)
        except TypeError:
            # Try with slave parameter (older versions)
            try:
                if method_name == 'read_coils':
                    return self.client.read_coils(*args, slave=unit_id, **kwargs)
                elif method_name == 'read_discrete_inputs':
                    return self.client.read_discrete_inputs(*args, slave=unit_id, **kwargs)
                elif method_name == 'read_holding_registers':
                    return self.client.read_holding_registers(*args, slave=unit_id, **kwargs)
                elif method_name == 'read_input_registers':
                    return self.client.read_input_registers(*args, slave=unit_id, **kwargs)
                elif method_name == 'write_coil':
                    return self.client.write_coil(*args, slave=unit_id, **kwargs)
                elif method_name == 'write_register':
                    return self.client.write_register(*args, slave=unit_id, **kwargs)
                elif method_name == 'write_coils':
                    return self.client.write_coils(*args, slave=unit_id, **kwargs)
                elif method_name == 'write_registers':
                    return self.client.write_registers(*args, slave=unit_id, **kwargs)
            except TypeError:
                # Try without any unit_id/slave parameter (some versions)
                if method_name == 'read_coils':
                    return self.client.read_coils(*args, **kwargs)
                elif method_name == 'read_discrete_inputs':
                    return self.client.read_discrete_inputs(*args, **kwargs)
                elif method_name == 'read_holding_registers':
                    return self.client.read_holding_registers(*args, **kwargs)
                elif method_name == 'read_input_registers':
                    return self.client.read_input_registers(*args, **kwargs)
                elif method_name == 'write_coil':
                    return self.client.write_coil(*args, **kwargs)
                elif method_name == 'write_register':
                    return self.client.write_register(*args, **kwargs)
                elif method_name == 'write_coils':
                    return self.client.write_coils(*args, **kwargs)
                elif method_name == 'write_registers':
                    return self.client.write_registers(*args, **kwargs)
        return None

async def main():
    """Main async function demonstrating Modbus client usage"""
    parser = argparse.ArgumentParser(description='Modern Modbus Client Demo using pymodbus')
    parser.add_argument('--mode', choices=['TCP', 'RTU'], default='TCP',
                       help='Modbus mode (default: TCP)')
    parser.add_argument('--address', default='0.0.0.0',
                       help='Local IP address for TCP mode (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=None,
                       help='Local port for TCP mode (default: auto-assign)')
    parser.add_argument('--serial-port', 
                       help='Serial port for RTU mode')
    parser.add_argument('--baud-rate', type=int, default=9600,
                       help='Baud rate for RTU mode (default: 9600)')
    parser.add_argument('--data-bits', type=int, default=8,
                       help='Data bits for RTU mode (default: 8)')
    parser.add_argument('--stop-bits', type=int, default=1,
                       help='Stop bits for RTU mode (default: 1)')
    parser.add_argument('--parity', choices=['N', 'E', 'O'], default='N',
                       help='Parity for RTU mode (default: N)')
    parser.add_argument('--target', required=True,
                       help='Target device IP address (TCP) or serial port (RTU)')
    parser.add_argument('--target-port', type=int, default=502,
                       help='Target port for TCP mode (default: 502)')
    parser.add_argument('--unit-id', type=int, default=1,
                       help='Modbus unit ID (default: 1)')
    parser.add_argument('--timeout', type=int, default=10,
                       help='Request timeout in seconds (default: 10)')
    
    # Operation arguments
    parser.add_argument('--discover', action='store_true',
                       help='Discover devices on the network')
    parser.add_argument('--test-connection', action='store_true',
                       help='Test connection to target device')
    parser.add_argument('--read-coils', 
                       help='Read coils (format: start_address,count)')
    parser.add_argument('--read-discrete-inputs',
                       help='Read discrete inputs (format: start_address,count)')
    parser.add_argument('--read-holding-registers',
                       help='Read holding registers (format: start_address,count)')
    parser.add_argument('--read-input-registers',
                       help='Read input registers (format: start_address,count)')
    parser.add_argument('--write-coil',
                       help='Write single coil (format: address,value)')
    parser.add_argument('--write-register',
                       help='Write single register (format: address,value)')
    parser.add_argument('--write-multiple-coils',
                       help='Write multiple coils (format: start_address,values)')
    parser.add_argument('--write-multiple-registers',
                       help='Write multiple registers (format: start_address,values)')
    parser.add_argument('--read-device-info', action='store_true',
                       help='Read device information')
    
    args = parser.parse_args()
    
    print("Modern Modbus Client Demo using pymodbus")
    print("=" * 50)
    print(f"Mode: {args.mode}")
    print(f"Target: {args.target}")
    print(f"Unit ID: {args.unit_id}")
    print(f"Timeout: {args.timeout}s")
    
    # Create client
    if args.mode == "TCP":
        client = ModbusClient(device_type="TCP", local_address=args.address, local_port=args.port)
        client.set_target_address(args.target, args.target_port)
    else:
        client = ModbusClient(device_type="RTU", serial_port=args.serial_port or args.target,
                            baud_rate=args.baud_rate, data_bits=args.data_bits,
                            stop_bits=args.stop_bits, parity=args.parity)
    
    # Start the client
    if not await client.start():
        print("Failed to start Modbus client")
        return
    
    try:
        # Discover devices
        if args.discover:
            print(f"\nDiscovering Modbus devices...")
            devices = await client.discover_devices(timeout=args.timeout)
            if devices:
                print(f"Found {len(devices)} device(s):")
                for device in devices:
                    print(f"  Unit ID: {device.unit_id}, Address: {device.address}")
            else:
                print("No devices found")
        
        # Test connection
        elif args.test_connection:
            print(f"\nTesting connection to {args.target}...")
            success = await client.test_connection(args.target, args.unit_id, args.timeout)
            print(f"Connection test {'successful' if success else 'failed'}")
        
        # Read coils
        elif args.read_coils:
            try:
                start_addr, count = map(int, args.read_coils.split(','))
                print(f"\nReading {count} coils starting at address {start_addr}...")
                result = await client.read_coils(args.target, args.unit_id, start_addr, count, args.timeout)
                if result:
                    print(f"Coils: {result}")
                else:
                    print("Failed to read coils")
            except ValueError:
                print("Invalid format. Use: start_address,count")
        
        # Read discrete inputs
        elif args.read_discrete_inputs:
            try:
                start_addr, count = map(int, args.read_discrete_inputs.split(','))
                print(f"\nReading {count} discrete inputs starting at address {start_addr}...")
                result = await client.read_discrete_inputs(args.target, args.unit_id, start_addr, count, args.timeout)
                if result:
                    print(f"Discrete inputs: {result}")
                else:
                    print("Failed to read discrete inputs")
            except ValueError:
                print("Invalid format. Use: start_address,count")
        
        # Read holding registers
        elif args.read_holding_registers:
            try:
                start_addr, count = map(int, args.read_holding_registers.split(','))
                print(f"\nReading {count} holding registers starting at address {start_addr}...")
                result = await client.read_holding_registers(args.target, args.unit_id, start_addr, count, args.timeout)
                if result:
                    print(f"Holding registers: {result}")
                else:
                    print("Failed to read holding registers")
            except ValueError:
                print("Invalid format. Use: start_address,count")
        
        # Read input registers
        elif args.read_input_registers:
            try:
                start_addr, count = map(int, args.read_input_registers.split(','))
                print(f"\nReading {count} input registers starting at address {start_addr}...")
                result = await client.read_input_registers(args.target, args.unit_id, start_addr, count, args.timeout)
                if result:
                    print(f"Input registers: {result}")
                else:
                    print("Failed to read input registers")
            except ValueError:
                print("Invalid format. Use: start_address,count")
        
        # Write single coil
        elif args.write_coil:
            try:
                address, value = args.write_coil.split(',')
                address = int(address)
                value = value.lower() in ['true', '1', 'on']
                print(f"\nWriting coil at address {address} to {value}...")
                success = await client.write_single_coil(args.target, args.unit_id, address, value, args.timeout)
                print(f"Write coil {'successful' if success else 'failed'}")
            except ValueError:
                print("Invalid format. Use: address,value (value: true/false, 1/0, on/off)")
        
        # Write single register
        elif args.write_register:
            try:
                address, value = map(int, args.write_register.split(','))
                print(f"\nWriting register at address {address} to {value}...")
                success = await client.write_single_register(args.target, args.unit_id, address, value, args.timeout)
                print(f"Write register {'successful' if success else 'failed'}")
            except ValueError:
                print("Invalid format. Use: address,value")
        
        # Write multiple coils
        elif args.write_multiple_coils:
            try:
                parts = args.write_multiple_coils.split(',')
                start_addr = int(parts[0])
                values = [v.lower() in ['true', '1', 'on'] for v in parts[1:]]
                print(f"\nWriting {len(values)} coils starting at address {start_addr}...")
                success = await client.write_multiple_coils(args.target, args.unit_id, start_addr, values, args.timeout)
                print(f"Write multiple coils {'successful' if success else 'failed'}")
            except (ValueError, IndexError):
                print("Invalid format. Use: start_address,value1,value2,...")
        
        # Write multiple registers
        elif args.write_multiple_registers:
            try:
                parts = args.write_multiple_registers.split(',')
                start_addr = int(parts[0])
                values = [int(v) for v in parts[1:]]
                print(f"\nWriting {len(values)} registers starting at address {start_addr}...")
                success = await client.write_multiple_registers(args.target, args.unit_id, start_addr, values, args.timeout)
                print(f"Write multiple registers {'successful' if success else 'failed'}")
            except (ValueError, IndexError):
                print("Invalid format. Use: start_address,value1,value2,...")
        
        # Read device info
        elif args.read_device_info:
            print(f"\nReading device information...")
            info = await client.read_device_info(args.target, args.unit_id, args.timeout)
            if info:
                print(f"Device info: {info}")
            else:
                print("Failed to read device information")
        
        else:
            print("\nNo operation specified. Use --help to see available options.")
            print("\nExample usage:")
            print("  python modbus_client.py --target 192.168.1.100 --read-holding-registers 0,10")
            print("  python modbus_client.py --target 192.168.1.100 --write-register 0,123")
            print("  python modbus_client.py --target 192.168.1.100 --discover")
        
        print("\nDemo completed!")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        await client.stop()

if __name__ == "__main__":
    asyncio.run(main()) 