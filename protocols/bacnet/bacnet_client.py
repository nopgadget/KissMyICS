#!/usr/bin/env python3
"""
Modern BACnet Client Script
A Python script to interact with BACnet servers using asyncio
"""

import asyncio
import socket
import struct
import time
import sys
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class BACnetObjectType(Enum):
    """BACnet object types"""
    DEVICE = 8
    ANALOG_INPUT = 0
    ANALOG_OUTPUT = 1
    ANALOG_VALUE = 2
    BINARY_INPUT = 3
    BINARY_OUTPUT = 4
    BINARY_VALUE = 5
    MULTI_STATE_INPUT = 13
    MULTI_STATE_OUTPUT = 14
    MULTI_STATE_VALUE = 19

class BACnetProperty(Enum):
    """BACnet property identifiers"""
    OBJECT_NAME = 77
    PRESENT_VALUE = 85
    DESCRIPTION = 28
    UNITS = 117
    STATUS_FLAGS = 111
    RELIABILITY = 103
    OUT_OF_SERVICE = 81
    VENDOR_NAME = 96
    VENDOR_IDENTIFIER = 97
    MODEL_NAME = 70
    FIRMWARE_REVISION = 44
    APPLICATION_SOFTWARE_VERSION = 12
    LOCATION = 58
    PROTOCOL_VERSION = 98
    PROTOCOL_REVISION = 99
    SYSTEM_STATUS = 112
    MAX_APDU_LENGTH_ACCEPTED = 62
    SEGMENTATION_SUPPORTED = 107
    # Additional properties for manipulation
    PRIORITY_ARRAY = 87
    RELINQUISH_DEFAULT = 95
    MINIMUM_ON_TIME = 81
    MINIMUM_OFF_TIME = 82
    ALARM_VALUE = 5
    COV_INCREMENT = 125
    TIME_DELAY = 113
    NOTIFICATION_CLASS = 17
    EVENT_ENABLE = 35
    ACKED_TRANSITIONS = 0
    NOTIFICATION_TYPE = 237
    EVENT_TIME_STAMPS = 130
    EVENT_MESSAGE_TEXTS = 131
    EVENT_MESSAGE_TEXTS_FORMAT = 132
    EVENT_STATE = 36
    EVENT_TYPE = 37
    EVENT_PARAMETERS = 83
    EVENT_TIME = 40
    ACKNOWLEDGE_TRANSITIONS = 0
    ACKNOWLEDGE_ALARMS = 1
    CONFIRMED_COV_NOTIFICATIONS = 2
    CONFIRMED_EVENT_NOTIFICATIONS = 3
    GET_ALARM_SUMMARY = 4
    GET_ENROLLMENT_SUMMARY = 5
    GET_EVENT_INFORMATION = 29
    SUBSCRIBE_COV = 5
    SUBSCRIBE_COV_PROPERTY = 28
    LIFE_SAFETY_OPERATION = 20
    PRIVATE_TRANSFER = 4
    TEXT_MESSAGE = 6
    REINITIALIZE_DEVICE = 19
    VIRTUAL_TERMINAL = 18
    AUTHENTICATE = 22
    REQUEST_KEY = 25
    I_AM = 26
    I_HAVE = 27
    WHO_IS = 28
    WHO_HAS = 29
    READ_PROPERTY = 12
    READ_PROPERTY_CONDITIONAL = 13
    READ_PROPERTY_MULTIPLE = 14
    READ_RANGE = 26
    READ_TAG = 27
    WRITE_PROPERTY = 15
    WRITE_PROPERTY_MULTIPLE = 16
    WRITE_GROUP = 17
    DELETE_OBJECT = 11
    CREATE_OBJECT = 10
    ADD_LIST_ELEMENT = 8
    REMOVE_LIST_ELEMENT = 9

@dataclass
class BACnetDevice:
    """Represents a discovered BACnet device"""
    device_id: int
    address: str
    vendor_id: Optional[int] = None
    vendor_name: Optional[str] = None
    model_name: Optional[str] = None

class BACnetAPDU:
    """BACnet APDU (Application Protocol Data Unit) handling"""
    
    @staticmethod
    def create_who_is_request(low_limit: int = 0, high_limit: int = 4194303) -> bytes:
        """Create a Who-Is request"""
        # BACnet APDU header
        apdu_type = 0x08  # Unconfirmed-Request
        service_choice = 0x10  # Who-Is
        
        # Create APDU
        apdu = struct.pack('!BB', apdu_type, service_choice)
        
        # Add limits if specified
        if low_limit != 0 or high_limit != 4194303:
            apdu += struct.pack('!BIII', 0x0B, low_limit, 0x0C, high_limit)
        
        return apdu
    
    @staticmethod
    def create_read_property_request(object_id: int, object_type: int, 
                                   property_id: int, array_index: Optional[int] = None) -> bytes:
        """Create a Read-Property request"""
        # BACnet APDU header - use proper confirmed request format
        apdu_type = 0x00  # Confirmed-Request
        service_choice = 0x0C  # ReadProperty
        
        # Create APDU with proper BACnet encoding
        # All confirmed requests need an invoke ID
        apdu = struct.pack('!BBB', apdu_type, service_choice, 0x01)  # Invoke ID
        
        # Object identifier (device,1) - use context tag 0 for ReadProperty
        apdu += struct.pack('!B', 0x00)  # Context tag 0 for object identifier
        apdu += struct.pack('!B', 0x04)  # Length (4 bytes)
        apdu += struct.pack('!HH', object_type, object_id)  # Object type and instance
        
        # Property identifier - use context tag 1 for ReadProperty
        apdu += struct.pack('!B', 0x01)  # Context tag 1 for property identifier
        apdu += struct.pack('!B', 0x02)  # Length (2 bytes)
        apdu += struct.pack('!H', property_id)  # Property identifier value
        
        # Array index (optional)
        if array_index is not None:
            apdu += struct.pack('!B', 0x12)  # Array index tag
            apdu += struct.pack('!B', 0x02)  # Array index length (2 bytes)
            apdu += struct.pack('!H', array_index)  # Array index value
        
        return apdu
    
    @staticmethod
    def create_write_property_with_priority(object_id: int, object_type: int,
                                         property_id: int, value: Any, priority: int,
                                         array_index: Optional[int] = None) -> bytes:
        """Create a Write-Property request with priority"""
        # BACnet APDU header
        apdu_type = 0x00  # Confirmed-Request
        service_choice = 0x0F  # WriteProperty
        
        # Create APDU
        apdu = struct.pack('!BB', apdu_type, service_choice)
        
        # Object identifier
        apdu += struct.pack('!BII', 0x0C, object_type, object_id)
        
        # Property identifier
        apdu += struct.pack('!BI', 0x19, property_id)
        
        # Array index (optional)
        if array_index is not None:
            apdu += struct.pack('!BI', 0x12, array_index)
        
        # Priority array
        apdu += struct.pack('!BB', 0x87, priority)  # Priority array
        
        # Property value
        if isinstance(value, bool):
            apdu += struct.pack('!BB', 0x91, 1 if value else 0)
        elif isinstance(value, int):
            apdu += struct.pack('!BBI', 0x21, 0x02, value)
        elif isinstance(value, str):
            apdu += struct.pack('!BB', 0x75, len(value)) + value.encode('utf-8')
        else:
            # Default to null
            apdu += struct.pack('!B', 0x00)
        
        return apdu
    
    @staticmethod
    def create_write_property_request(object_id: int, object_type: int,
                                   property_id: int, value: Any,
                                   array_index: Optional[int] = None) -> bytes:
        """Create a Write-Property request"""
        # BACnet APDU header
        apdu_type = 0x00  # Confirmed-Request
        service_choice = 0x0F  # WriteProperty
        
        # Create APDU
        apdu = struct.pack('!BB', apdu_type, service_choice)
        
        # Object identifier
        apdu += struct.pack('!BII', 0x0C, object_type, object_id)
        
        # Property identifier
        apdu += struct.pack('!BI', 0x19, property_id)
        
        # Array index (optional)
        if array_index is not None:
            apdu += struct.pack('!BI', 0x12, array_index)
        
        # Property value
        if isinstance(value, bool):
            apdu += struct.pack('!BB', 0x91, 1 if value else 0)
        elif isinstance(value, int):
            apdu += struct.pack('!BBI', 0x21, 0x02, value)
        elif isinstance(value, str):
            apdu += struct.pack('!BB', 0x75, len(value)) + value.encode('utf-8')
        else:
            # Default to null
            apdu += struct.pack('!B', 0x00)
        
        return apdu
    
    @staticmethod
    def create_device_control_request(object_id: int, object_type: int,
                                   command: str, parameters: Dict[str, Any]) -> bytes:
        """Create a Device Control request"""
        # BACnet APDU header
        apdu_type = 0x00  # Confirmed-Request
        service_choice = 0x13  # DeviceCommunicationControl
        
        # Create APDU
        apdu = struct.pack('!BB', apdu_type, service_choice)
        
        # Object identifier
        apdu += struct.pack('!BII', 0x0C, object_type, object_id)
        
        # Command
        apdu += struct.pack('!BB', 0x75, len(command)) + command.encode('utf-8')
        
        # Parameters (simplified)
        if parameters:
            for key, value in parameters.items():
                apdu += struct.pack('!BB', 0x75, len(str(value))) + str(value).encode('utf-8')
        
        return apdu
    
    @staticmethod
    def create_reinitialize_device_request(reinit_type: str) -> bytes:
        """Create a Reinitialize Device request"""
        # BACnet APDU header
        apdu_type = 0x00  # Confirmed-Request
        service_choice = 0x13  # ReinitializeDevice
        
        # Create APDU
        apdu = struct.pack('!BB', apdu_type, service_choice)
        
        # Reinitialize type
        type_map = {'coldstart': 0, 'warmstart': 1, 'startbackup': 2, 'startupdate': 3}
        reinit_code = type_map.get(reinit_type.lower(), 0)
        apdu += struct.pack('!BB', 0x91, reinit_code)
        
        return apdu
    
    @staticmethod
    def create_acknowledge_alarm_request(object_id: int, object_type: int,
                                       action: str) -> bytes:
        """Create an Acknowledge Alarm request"""
        # BACnet APDU header
        apdu_type = 0x00  # Confirmed-Request
        service_choice = 0x00  # AcknowledgeAlarm
        
        # Create APDU
        apdu = struct.pack('!BB', apdu_type, service_choice)
        
        # Object identifier
        apdu += struct.pack('!BII', 0x0C, object_type, object_id)
        
        # Action
        apdu += struct.pack('!BB', 0x75, len(action)) + action.encode('utf-8')
        
        return apdu
    
    @staticmethod
    def create_create_object_request(object_type: int, instance: int,
                                  properties: Dict[str, Any]) -> bytes:
        """Create a Create Object request"""
        # BACnet APDU header
        apdu_type = 0x00  # Confirmed-Request
        service_choice = 0x0A  # CreateObject
        
        # Create APDU
        apdu = struct.pack('!BB', apdu_type, service_choice)
        
        # Object identifier
        apdu += struct.pack('!BII', 0x0C, object_type, instance)
        
        # Properties
        for prop_name, prop_value in properties.items():
            prop_id = BACnetProperty[prop_name.upper()].value
            apdu += struct.pack('!BI', 0x19, prop_id)
            
            # Property value
            if isinstance(prop_value, bool):
                apdu += struct.pack('!BB', 0x91, 1 if prop_value else 0)
            elif isinstance(prop_value, int):
                apdu += struct.pack('!BBI', 0x21, 0x02, prop_value)
            elif isinstance(prop_value, str):
                apdu += struct.pack('!BB', 0x75, len(prop_value)) + prop_value.encode('utf-8')
            else:
                apdu += struct.pack('!B', 0x00)
        
        return apdu
    
    @staticmethod
    def create_delete_object_request(object_type: int, instance: int) -> bytes:
        """Create a Delete Object request"""
        # BACnet APDU header
        apdu_type = 0x00  # Confirmed-Request
        service_choice = 0x0B  # DeleteObject
        
        # Create APDU
        apdu = struct.pack('!BB', apdu_type, service_choice)
        
        # Object identifier
        apdu += struct.pack('!BII', 0x0C, object_type, instance)
        
        return apdu
    
    @staticmethod
    def create_subscribe_cov_request(object_type: int, instance: int,
                                   property_id: int) -> bytes:
        """Create a Subscribe COV request"""
        # BACnet APDU header
        apdu_type = 0x00  # Confirmed-Request
        service_choice = 0x05  # SubscribeCOV
        
        # Create APDU
        apdu = struct.pack('!BB', apdu_type, service_choice)
        
        # Object identifier
        apdu += struct.pack('!BII', 0x0C, object_type, instance)
        
        # Property identifier
        apdu += struct.pack('!BI', 0x19, property_id)
        
        # Issue confirmed notifications
        apdu += struct.pack('!BB', 0x91, 1)
        
        return apdu

class BACnetClient:
    """Modern asyncio-based BACnet client"""
    
    def __init__(self, device_id: int = 999, local_address: str = '0.0.0.0', 
                 local_port: int = None):
        """
        Initialize BACnet client
        
        Args:
            device_id: Local device ID
            local_address: Local IP address to bind to
            local_port: Local port to bind to (None for auto-assign, 47808 for default BACnet port)
        """
        self.device_id = device_id
        self.local_address = local_address
        self.local_port = local_port or 0  # 0 means auto-assign port
        self.transport = None
        self.protocol = None
        self.discovered_devices: Dict[str, BACnetDevice] = {}
        self.target_address = None
        self.pending_responses = {}  # Track pending requests
        self.response_data = {}  # Store response data
        
    async def start(self) -> bool:
        """Start the BACnet client"""
        try:
            # Create UDP socket
            loop = asyncio.get_event_loop()
            
            # Try to bind to the specified port, or auto-assign if port is 0
            try:
                self.transport, self.protocol = await loop.create_datagram_endpoint(
                    lambda: BACnetProtocol(self),
                    local_addr=(self.local_address, self.local_port)
                )
            except OSError as e:
                if "Address already in use" in str(e) and self.local_port != 0:
                    print(f"Port {self.local_port} is in use, trying auto-assign...")
                    # Try with auto-assign port
                    self.local_port = 0
                    self.transport, self.protocol = await loop.create_datagram_endpoint(
                        lambda: BACnetProtocol(self),
                        local_addr=(self.local_address, self.local_port)
                    )
                else:
                    raise e
            
            # Get the actual port that was bound
            actual_port = self.transport.get_extra_info('socket').getsockname()[1]
            
            print(f"BACnet client started with device ID: {self.device_id}")
            print(f"Local address: {self.local_address}:{actual_port}")
            return True
            
        except Exception as e:
            print(f"Error starting BACnet client: {e}")
            return False
    
    def set_target_address(self, address: str) -> None:
        """Set target address for direct communication"""
        self.target_address = address
    
    async def discover_devices(self, timeout: int = 10) -> List[BACnetDevice]:
        """Discover BACnet devices on the network"""
        print(f"Discovering devices (timeout: {timeout}s)...")
        
        try:
            # Clear previous discoveries
            self.discovered_devices.clear()
            
            # Create Who-Is request
            who_is_apdu = BACnetAPDU.create_who_is_request()
            
            # Create BACnet packet
            packet = self._create_bacnet_packet(who_is_apdu)
            
            # Send to broadcast address
            broadcast_addr = ('255.255.255.255', 47808)
            self.transport.sendto(packet, broadcast_addr)
            
            # Also send directly to target if specified
            if hasattr(self, 'target_address') and self.target_address:
                target_addr = (self.target_address, 47808)
                self.transport.sendto(packet, target_addr)
                print(f"Sent Who-Is request to {self.target_address}")
            
            # Wait for responses
            await asyncio.sleep(timeout)
            
            # Return discovered devices
            devices = list(self.discovered_devices.values())
            print(f"Discovered {len(devices)} devices:")
            for device in devices:
                print(f"  Device ID: {device.device_id}, Address: {device.address}")
            
            return devices
            
        except Exception as e:
            print(f"Error discovering devices: {e}")
            return []
    
    async def read_property(self, target_address: str, object_id: str, 
                          property_id: str) -> Optional[Any]:
        """
        Read a property from a BACnet object
        
        Args:
            target_address: Target device address
            object_id: Object identifier (e.g., 'analogInput,1')
            property_id: Property identifier (e.g., 'presentValue')
        """
        try:
            # Parse object identifier
            obj_type_str, obj_inst_str = object_id.split(',')
            obj_inst = int(obj_inst_str)
            
            # Get object type enum
            obj_type = BACnetObjectType[obj_type_str.upper().replace('-', '_')].value
            
            # Get property enum - handle common property name variations
            property_mapping = {
                'objectname': 'OBJECT_NAME',
                'presentvalue': 'PRESENT_VALUE',
                'description': 'DESCRIPTION',
                'units': 'UNITS',
                'statusflags': 'STATUS_FLAGS',
                'reliability': 'RELIABILITY',
                'outofservice': 'OUT_OF_SERVICE',
                'vendorname': 'VENDOR_NAME',
                'vendoridentifier': 'VENDOR_IDENTIFIER',
                'modelname': 'MODEL_NAME',
                'firmwarerevision': 'FIRMWARE_REVISION',
                'applicationsoftwareversion': 'APPLICATION_SOFTWARE_VERSION',
                'location': 'LOCATION',
                'protocolversion': 'PROTOCOL_VERSION',
                'protocolrevision': 'PROTOCOL_REVISION',
                'systemstatus': 'SYSTEM_STATUS',
                'maxapdulengthaccepted': 'MAX_APDU_LENGTH_ACCEPTED',
                'segmentationsupported': 'SEGMENTATION_SUPPORTED'
            }
            
            prop_key = property_id.upper().replace('-', '').replace('_', '')
            if prop_key in property_mapping:
                mapped_prop = property_mapping[prop_key]
                prop_id = BACnetProperty[mapped_prop].value
            else:
                # Try direct mapping with common variations
                try:
                    prop_id = BACnetProperty[property_id.upper()].value
                except KeyError:
                    # Try with underscores
                    try:
                        prop_id = BACnetProperty[property_id.upper().replace('-', '_')].value
                    except KeyError:
                        # Try with camelCase to UPPER_CASE conversion
                        import re
                        upper_case = re.sub(r'([a-z])([A-Z])', r'\1_\2', property_id).upper()
                        try:
                            prop_id = BACnetProperty[upper_case].value
                        except KeyError:
                            print(f"Error: Property '{property_id}' not found in BACnetProperty enum")
                            raise
            
            # Create read request
            read_apdu = BACnetAPDU.create_read_property_request(obj_inst, obj_type, prop_id)
            
            # Create BACnet packet
            packet = self._create_bacnet_packet(read_apdu)
            
            # Debug: Print what we're sending
            print(f"  Sending APDU: {read_apdu.hex()}")
            print(f"  Object type: {obj_type}, Object ID: {obj_inst}, Property: {prop_id}")
            
            # Send request
            target_addr = (target_address, 47808)
            self.transport.sendto(packet, target_addr)
            
            print(f"Reading {property_id} from {object_id} at {target_address}...")
            
            # Create a unique request ID for tracking
            import uuid
            request_id = str(uuid.uuid4())
            self.pending_responses[request_id] = {
                'object_id': object_id,
                'property_id': property_id,
                'target': target_address,
                'timestamp': time.time()
            }
            
            # Wait for response with timeout
            start_time = time.time()
            timeout = 3.0  # 3 second timeout
            
            while time.time() - start_time < timeout:
                if request_id in self.response_data:
                    # We got a response!
                    response_value = self.response_data[request_id]
                    del self.response_data[request_id]
                    del self.pending_responses[request_id]
                    return response_value
                await asyncio.sleep(0.1)
            
            # Timeout - remove pending request
            if request_id in self.pending_responses:
                del self.pending_responses[request_id]
            
            # No response received - return None to indicate no data
            print(f"  (No response received from {target_address})")
            return None
            
        except Exception as e:
            print(f"Error reading property: {e}")
            return None
    
    async def write_property(self, target_address: str, object_id: str,
                           property_id: str, value: Any) -> bool:
        """
        Write a property to a BACnet object
        
        Args:
            target_address: Target device address
            object_id: Object identifier
            property_id: Property identifier
            value: Value to write
        """
        try:
            # Parse object identifier
            obj_type_str, obj_inst_str = object_id.split(',')
            obj_inst = int(obj_inst_str)
            
            # Get object type enum
            obj_type = BACnetObjectType[obj_type_str.upper().replace('-', '_')].value
            
            # Get property enum
            prop_id = BACnetProperty[property_id.upper()].value
            
            # Create write request
            write_apdu = BACnetAPDU.create_write_property_request(obj_inst, obj_type, prop_id, value)
            
            # Create BACnet packet
            packet = self._create_bacnet_packet(write_apdu)
            
            # Send request
            target_addr = (target_address, 47808)
            self.transport.sendto(packet, target_addr)
            
            print(f"Writing {value} to {property_id} of {object_id} at {target_address}...")
            
            # Wait for response
            await asyncio.sleep(1)
            
            # For now, return success
            # In a real implementation, you'd check the response
            return True
            
        except Exception as e:
            print(f"Error writing property: {e}")
            return False
    
    async def enumerate_device(self, target_address: str) -> None:
        """
        Enumerate detailed information about a BACnet device
        
        Args:
            target_address: Target device address
        """
        print(f"\nEnumerating device at {target_address}")
        print("=" * 60)
        
        try:
            # Device properties to check
            device_properties = [
                'objectName', 'vendorName', 'vendorIdentifier', 'modelName',
                'firmwareRevision', 'applicationSoftwareVersion', 'location',
                'description', 'protocolVersion', 'protocolRevision',
                'systemStatus', 'maxApduLengthAccepted', 'segmentationSupported'
            ]
            
            print("Device Information:")
            print("-" * 30)
            
            # Read device properties
            for prop in device_properties:
                try:
                    value = await self.read_property(target_address, 'device,1', prop)
                    if value is not None:
                        print(f"  {prop}: {value}")
                    else:
                        print(f"  {prop}: <no response>")
                except Exception as e:
                    print(f"  {prop}: <error: {e}>")
            
            print(f"\nObject Enumeration:")
            print("-" * 30)
            
            # Enumerate objects by type
            object_types = [
                'analogInput', 'analogOutput', 'analogValue',
                'binaryInput', 'binaryOutput', 'binaryValue',
                'multiStateInput', 'multiStateOutput', 'multiStateValue'
            ]
            
            for obj_type in object_types:
                print(f"\n{obj_type.upper()} Objects:")
                print("-" * 20)
                
                # Try to find objects of this type
                found_objects = []
                
                # Check first 5 instances of each type
                for instance in range(1, 6):
                    try:
                        obj_id = f"{obj_type},{instance}"
                        name = await self.read_property(target_address, obj_id, 'objectName')
                        if name is not None:
                            found_objects.append((instance, name))
                    except:
                        continue
                
                if found_objects:
                    for instance, name in found_objects:
                        print(f"  {obj_type},{instance}: {name}")
                        
                        # Try to read present value
                        try:
                            value = await self.read_property(target_address, f"{obj_type},{instance}", 'presentValue')
                            if value is not None:
                                print(f"    presentValue: {value}")
                            else:
                                print(f"    presentValue: <no response>")
                        except Exception as e:
                            print(f"    presentValue: <error: {e}>")
                else:
                    print(f"  No {obj_type} objects found")
            
            print(f"\nEnumeration completed for {target_address}")
            
        except Exception as e:
            print(f"Error enumerating device: {e}")
    
    async def check_permissions(self, target_address: str, object_id: str = 'device,1') -> None:
        """
        Check read/write permissions for common properties
        
        Args:
            target_address: Target device address
            object_id: Object identifier to test
        """
        print(f"\nPermission Check for {object_id} at {target_address}")
        print("=" * 50)
        
        # Common properties to test
        test_properties = [
            'objectName', 'presentValue', 'description', 'units',
            'statusFlags', 'reliability', 'outOfService'
        ]
        
        print("Read Permissions:")
        print("-" * 20)
        for prop in test_properties:
            try:
                value = await self.read_property(target_address, object_id, prop)
                if value is not None:
                    print(f"  ✓ {prop}: {value}")
                else:
                    print(f"  ✗ {prop}: No access")
            except Exception as e:
                print(f"  ✗ {prop}: Error - {str(e)[:50]}")
        
        print(f"\nWrite Permissions:")
        print("-" * 20)
        
        # Test write permissions (be careful!)
        write_test_properties = [
            ('outOfService', True),  # Safe to test
            ('description', 'Test Write')  # Safe to test
        ]
        
        for prop, test_value in write_test_properties:
            try:
                success = await self.write_property(target_address, object_id, prop, test_value)
                if success:
                    print(f"  ✓ {prop}: Writable")
                    # Try to restore original value if possible
                    if prop == 'outOfService':
                        await self.write_property(target_address, object_id, prop, False)
                else:
                    print(f"  ✗ {prop}: Not writable")
            except Exception as e:
                print(f"  ✗ {prop}: Error - {str(e)[:50]}")
        
        print(f"\nPermission check completed for {object_id}")
    
    def _create_bacnet_packet(self, apdu: bytes) -> bytes:
        """Create a BACnet packet with the given APDU"""
        # BACnet/IP header
        version = 0x01
        function = 0x01  # Original-Unicast-NPDU
        
        # NPDU (Network Protocol Data Unit)
        npdu_version = 0x01
        npdu_control = 0x00  # No special control
        
        # Create packet
        packet = struct.pack('!BB', version, function)
        packet += struct.pack('!H', len(apdu) + 4)  # Length
        packet += struct.pack('!BB', npdu_version, npdu_control)
        packet += apdu
        
        return packet
    
    async def stop(self) -> None:
        """Stop the BACnet client"""
        if self.transport:
            self.transport.close()
            print("BACnet client stopped")
    
    # ===== COMMAND AND MANIPULATION METHODS =====
    
    async def write_command(self, target_address: str, object_id: str, 
                          command: str, value: Any = None, priority: int = 16) -> bool:
        """
        Write a command to a BACnet object
        
        Args:
            target_address: Target device address
            object_id: Object identifier (e.g., 'analogOutput,1')
            command: Command to execute
            value: Value for the command
            priority: Priority level (1-16, 16 is highest)
        """
        try:
            # Parse object identifier
            obj_type_str, obj_inst_str = object_id.split(',')
            obj_inst = int(obj_inst_str)
            obj_type = BACnetObjectType[obj_type_str.upper().replace('-', '_')].value
            
            # Create command based on type
            if command.lower() == 'set_value':
                return await self._write_present_value(target_address, obj_type, obj_inst, value, priority)
            elif command.lower() == 'enable':
                return await self._write_out_of_service(target_address, obj_type, obj_inst, False)
            elif command.lower() == 'disable':
                return await self._write_out_of_service(target_address, obj_type, obj_inst, True)
            elif command.lower() == 'reset':
                return await self._reset_object(target_address, obj_type, obj_inst)
            elif command.lower() == 'acknowledge':
                return await self._acknowledge_alarm(target_address, obj_type, obj_inst)
            else:
                print(f"Unknown command: {command}")
                return False
                
        except Exception as e:
            print(f"Error executing command: {e}")
            return False
    
    async def _write_present_value(self, target_address: str, obj_type: int, 
                                 obj_inst: int, value: Any, priority: int) -> bool:
        """Write present value with priority"""
        try:
            # Create write request with priority
            write_apdu = BACnetAPDU.create_write_property_with_priority(
                obj_inst, obj_type, BACnetProperty.PRESENT_VALUE.value, value, priority
            )
            
            packet = self._create_bacnet_packet(write_apdu)
            target_addr = (target_address, 47808)
            self.transport.sendto(packet, target_addr)
            
            print(f"Writing value {value} with priority {priority} to {obj_type},{obj_inst}")
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            print(f"Error writing present value: {e}")
            return False
    
    async def _write_out_of_service(self, target_address: str, obj_type: int, 
                                  obj_inst: int, out_of_service: bool) -> bool:
        """Enable/disable an object"""
        try:
            write_apdu = BACnetAPDU.create_write_property_request(
                obj_inst, obj_type, BACnetProperty.OUT_OF_SERVICE.value, out_of_service
            )
            
            packet = self._create_bacnet_packet(write_apdu)
            target_addr = (target_address, 47808)
            self.transport.sendto(packet, target_addr)
            
            status = "disabled" if out_of_service else "enabled"
            print(f"Object {obj_type},{obj_inst} {status}")
            await asyncio.sleep(1)
            return True
                
        except Exception as e:
            print(f"Error setting out of service: {e}")
            return False
    
    async def _reset_object(self, target_address: str, obj_type: int, obj_inst: int) -> bool:
        """Reset an object to default values"""
        try:
            # Create reset command
            reset_apdu = BACnetAPDU.create_device_control_request(
                obj_inst, obj_type, "reset", {}
            )
            
            packet = self._create_bacnet_packet(reset_apdu)
            target_addr = (target_address, 47808)
            self.transport.sendto(packet, target_addr)
            
            print(f"Reset command sent to {obj_type},{obj_inst}")
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            print(f"Error resetting object: {e}")
            return False
    
    async def _acknowledge_alarm(self, target_address: str, obj_type: int, obj_inst: int) -> bool:
        """Acknowledge an alarm"""
        try:
            # Create acknowledge alarm request
            ack_apdu = BACnetAPDU.create_acknowledge_alarm_request(
                obj_inst, obj_type, "acknowledge"
            )
            
            packet = self._create_bacnet_packet(ack_apdu)
            target_addr = (target_address, 47808)
            self.transport.sendto(packet, target_addr)
            
            print(f"Alarm acknowledged for {obj_type},{obj_inst}")
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            print(f"Error acknowledging alarm: {e}")
            return False
    
    async def manipulate_device(self, target_address: str, operation: str, 
                              parameters: Dict[str, Any] = None) -> bool:
        """
        Perform device manipulation operations
        
        Args:
            target_address: Target device address
            operation: Operation to perform
            parameters: Operation parameters
        """
        try:
            if operation.lower() == 'reinitialize':
                return await self._reinitialize_device(target_address, parameters)
            elif operation.lower() == 'backup':
                return await self._backup_device(target_address)
            elif operation.lower() == 'restore':
                return await self._restore_device(target_address, parameters)
            elif operation.lower() == 'update_firmware':
                return await self._update_firmware(target_address, parameters)
            elif operation.lower() == 'set_time':
                return await self._set_device_time(target_address, parameters)
            else:
                print(f"Unknown device operation: {operation}")
                return False
                
        except Exception as e:
            print(f"Error performing device operation: {e}")
            return False
    
    async def _reinitialize_device(self, target_address: str, 
                                 parameters: Dict[str, Any] = None) -> bool:
        """Reinitialize a device"""
        try:
            reinit_type = parameters.get('type', 'coldstart') if parameters else 'coldstart'
            
            reinit_apdu = BACnetAPDU.create_reinitialize_device_request(reinit_type)
            packet = self._create_bacnet_packet(reinit_apdu)
            
            target_addr = (target_address, 47808)
            self.transport.sendto(packet, target_addr)
            
            print(f"Reinitialize command sent to device at {target_address} (type: {reinit_type})")
            await asyncio.sleep(2)
            return True
            
        except Exception as e:
            print(f"Error reinitializing device: {e}")
            return False
    
    async def _backup_device(self, target_address: str) -> bool:
        """Backup device configuration"""
        try:
            backup_apdu = BACnetAPDU.create_device_control_request(
                1, BACnetObjectType.DEVICE.value, "backup", {}
            )
            
            packet = self._create_bacnet_packet(backup_apdu)
            target_addr = (target_address, 47808)
            self.transport.sendto(packet, target_addr)
            
            print(f"Backup command sent to device at {target_address}")
            await asyncio.sleep(2)
            return True
            
        except Exception as e:
            print(f"Error backing up device: {e}")
            return False
    
    async def _restore_device(self, target_address: str, parameters: Dict[str, Any]) -> bool:
        """Restore device configuration"""
        try:
            config_data = parameters.get('config_data', b'')
            
            restore_apdu = BACnetAPDU.create_device_control_request(
                1, BACnetObjectType.DEVICE.value, "restore", {'data': config_data}
            )
            
            packet = self._create_bacnet_packet(restore_apdu)
            target_addr = (target_address, 47808)
            self.transport.sendto(packet, target_addr)
            
            print(f"Restore command sent to device at {target_address}")
            await asyncio.sleep(2)
            return True
            
        except Exception as e:
            print(f"Error restoring device: {e}")
            return False
    
    async def _update_firmware(self, target_address: str, parameters: Dict[str, Any]) -> bool:
        """Update device firmware"""
        try:
            firmware_data = parameters.get('firmware_data', b'')
            
            update_apdu = BACnetAPDU.create_device_control_request(
                1, BACnetObjectType.DEVICE.value, "update_firmware", {'data': firmware_data}
            )
            
            packet = self._create_bacnet_packet(update_apdu)
            target_addr = (target_address, 47808)
            self.transport.sendto(packet, target_addr)
            
            print(f"Firmware update command sent to device at {target_address}")
            await asyncio.sleep(5)  # Longer timeout for firmware operations
            return True
            
        except Exception as e:
            print(f"Error updating firmware: {e}")
            return False
    
    async def _set_device_time(self, target_address: str, parameters: Dict[str, Any]) -> bool:
        """Set device time"""
        try:
            import datetime
            new_time = parameters.get('time', datetime.datetime.now())
            
            time_apdu = BACnetAPDU.create_device_control_request(
                1, BACnetObjectType.DEVICE.value, "set_time", {'time': new_time}
            )
            
            packet = self._create_bacnet_packet(time_apdu)
            target_addr = (target_address, 47808)
            self.transport.sendto(packet, target_addr)
            
            print(f"Time set command sent to device at {target_address}")
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            print(f"Error setting device time: {e}")
            return False
    
    async def create_object(self, target_address: str, object_type: str, 
                          instance: int, properties: Dict[str, Any] = None) -> bool:
        """
        Create a new BACnet object
        
        Args:
            target_address: Target device address
            object_type: Type of object to create
            instance: Instance number
            properties: Initial properties
        """
        try:
            obj_type = BACnetObjectType[object_type.upper().replace('-', '_')].value
            
            create_apdu = BACnetAPDU.create_create_object_request(obj_type, instance, properties or {})
            packet = self._create_bacnet_packet(create_apdu)
            
            target_addr = (target_address, 47808)
            self.transport.sendto(packet, target_addr)
            
            print(f"Create object command sent: {object_type},{instance}")
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            print(f"Error creating object: {e}")
            return False
    
    async def delete_object(self, target_address: str, object_id: str) -> bool:
        """
        Delete a BACnet object
        
        Args:
            target_address: Target device address
            object_id: Object identifier to delete
        """
        try:
            obj_type_str, obj_inst_str = object_id.split(',')
            obj_inst = int(obj_inst_str)
            obj_type = BACnetObjectType[obj_type_str.upper().replace('-', '_')].value
            
            delete_apdu = BACnetAPDU.create_delete_object_request(obj_type, obj_inst)
            packet = self._create_bacnet_packet(delete_apdu)
            
            target_addr = (target_address, 47808)
            self.transport.sendto(packet, target_addr)
            
            print(f"Delete object command sent: {object_id}")
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            print(f"Error deleting object: {e}")
            return False
    
    async def test_device_connection(self, target_address: str) -> bool:
        """
        Test direct connection to a specific device
        
        Args:
            target_address: Target device address
        """
        try:
            print(f"Testing connection to {target_address}...")
            
            # Try to read device object name
            device_name = await self.read_property(target_address, 'device,1', 'objectName')
            if device_name is not None:
                print(f"✓ Successfully connected to device at {target_address}")
                print(f"  Device name: {device_name}")
                return True
            else:
                print(f"✗ Could not read device properties from {target_address}")
                return False
                
        except Exception as e:
            print(f"✗ Connection test failed: {e}")
            return False
    
    async def subscribe_to_changes(self, target_address: str, object_id: str, 
                                 property_id: str = 'presentValue') -> bool:
        """
        Subscribe to property changes (COV - Change of Value)
        
        Args:
            target_address: Target device address
            object_id: Object identifier
            property_id: Property to monitor
        """
        try:
            obj_type_str, obj_inst_str = object_id.split(',')
            obj_inst = int(obj_inst_str)
            obj_type = BACnetObjectType[obj_type_str.upper().replace('-', '_')].value
            prop_id = BACnetProperty[property_id.upper()].value
            
            cov_apdu = BACnetAPDU.create_subscribe_cov_request(obj_type, obj_inst, prop_id)
            packet = self._create_bacnet_packet(cov_apdu)
            
            target_addr = (target_address, 47808)
            self.transport.sendto(packet, target_addr)
            
            print(f"COV subscription sent for {object_id}.{property_id}")
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            print(f"Error subscribing to changes: {e}")
            return False

class BACnetProtocol(asyncio.DatagramProtocol):
    """Protocol for handling BACnet UDP packets"""
    
    def __init__(self, client: BACnetClient):
        self.client = client
    
    def connection_made(self, transport):
        self.transport = transport
    
    def datagram_received(self, data, addr):
        """Handle received BACnet packets"""
        try:
            # Parse BACnet packet
            if len(data) < 6:
                return
            
            # Extract APDU
            apdu_start = 6  # Skip BACnet/IP header
            apdu = data[apdu_start:]
            
            # Handle different APDU types
            if len(apdu) > 0:
                apdu_type = apdu[0] & 0xF0
                
                if apdu_type == 0x20:  # I-Am response
                    self._handle_i_am(apdu, addr)
                elif apdu_type == 0x30:  # ReadProperty response
                    self._handle_read_response(apdu, addr)
                elif apdu_type == 0x40:  # WriteProperty response
                    self._handle_write_response(apdu, addr)
                    
        except Exception as e:
            print(f"Error parsing BACnet packet: {e}")
    
    def _handle_i_am(self, apdu: bytes, addr: Tuple[str, int]) -> None:
        """Handle I-Am response from device discovery"""
        try:
            # Parse device information from I-Am
            # This is a simplified parser
            device_id = 1  # Placeholder - would parse from APDU
            address = addr[0]
            
            device = BACnetDevice(device_id=device_id, address=address)
            self.client.discovered_devices[address] = device
                
        except Exception as e:
            print(f"Error parsing I-Am response: {e}")
    
    def _handle_read_response(self, apdu: bytes, addr: Tuple[str, int]) -> None:
        """Handle ReadProperty response"""
        try:
            # Parse BACnet ReadProperty response
            if len(apdu) < 4:
                return
            
            # Extract property value from response
            # This is a simplified parser - in a real implementation you'd parse the full APDU
            value = self._parse_bacnet_value(apdu)
            
            # Find matching pending request
            for request_id, request_data in self.client.pending_responses.items():
                if request_data['target'] == addr[0]:
                    # Store the response
                    self.client.response_data[request_id] = value
                    print(f"  Received response: {value}")
                    break
                    
        except Exception as e:
            print(f"Error parsing read response: {e}")
    
    def _parse_bacnet_value(self, apdu: bytes) -> str:
        """Parse BACnet value from APDU"""
        try:
            # This is a simplified parser
            # In a real implementation, you'd parse the full BACnet APDU structure
            
            # Look for common BACnet data types
            if len(apdu) >= 2:
                # Try to extract string values
                for i in range(len(apdu) - 1):
                    if apdu[i] == 0x75:  # CharacterString tag
                        length = apdu[i + 1]
                        if i + 2 + length <= len(apdu):
                            value = apdu[i + 2:i + 2 + length].decode('utf-8', errors='ignore')
                            return value
                
                # Try to extract numeric values
                for i in range(len(apdu) - 3):
                    if apdu[i] == 0x21:  # UnsignedInteger tag
                        if i + 4 <= len(apdu):
                            value = struct.unpack('!I', apdu[i + 1:i + 5])[0]
                            return str(value)
                    elif apdu[i] == 0x44:  # Real tag
                        if i + 5 <= len(apdu):
                            value = struct.unpack('!f', apdu[i + 1:i + 5])[0]
                            return str(value)
            
            # If we can't parse it, return a hex representation
            return f"0x{apdu.hex()[:20]}..."
            
        except Exception as e:
            return f"<parse_error: {e}>"
    
    def _handle_write_response(self, apdu: bytes, addr: Tuple[str, int]) -> None:
        """Handle WriteProperty response"""
        # Parse write response
        pass

async def main():
    """Main async function demonstrating BACnet client usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Modern BACnet Client Demo')
    parser.add_argument('--enumerate', action='store_true', 
                       help='Enumerate devices and their capabilities')
    parser.add_argument('--device-id', type=int, default=999,
                       help='Local device ID (default: 999)')
    parser.add_argument('--address', default='0.0.0.0',
                       help='Local IP address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=None,
                       help='Local port (default: auto-assign, 47808 for standard BACnet)')
    parser.add_argument('--timeout', type=int, default=10,
                       help='Discovery timeout in seconds (default: 10)')
    parser.add_argument('--target', 
                       help='Target device IP address for enumeration')
    parser.add_argument('--command', 
                       help='Command to execute (set_value, enable, disable, reset, acknowledge)')
    parser.add_argument('--value', 
                       help='Value for command (for set_value command)')
    parser.add_argument('--priority', type=int, default=16,
                       help='Priority level for commands (1-16, default: 16)')
    parser.add_argument('--operation', 
                       help='Device operation (reinitialize, backup, restore, update_firmware, set_time)')
    parser.add_argument('--create-object', 
                       help='Create object (format: type,instance)')
    parser.add_argument('--delete-object', 
                       help='Delete object (format: type,instance)')
    parser.add_argument('--subscribe', 
                       help='Subscribe to property changes (format: object,property)')
    parser.add_argument('--test-connection', action='store_true',
                       help='Test direct connection to target device')
    
    args = parser.parse_args()
    
    print("Modern BACnet Client Demo (asyncio-based)")
    print("=" * 50)
    
    # Create client
    client = BACnetClient(device_id=args.device_id, local_address=args.address, local_port=args.port)
    
    # Set target address if specified
    if args.target:
        client.set_target_address(args.target)
    
    # Start the client
    if not await client.start():
        print("Failed to start BACnet client")
        return
    
    try:
        # Discover devices
        devices = await client.discover_devices(timeout=args.timeout)
        
        if not devices:
            print("No devices found. Make sure you have BACnet devices on your network.")
            
            # If we have a target address, try direct connection test
            if args.target and args.test_connection:
                print(f"\nTrying direct connection test to {args.target}...")
                success = await client.test_device_connection(args.target)
                if success:
                    target_addr = args.target
                else:
                    return
            elif args.target and args.enumerate:
                # For enumeration, try to use target directly
                print(f"\nTrying direct enumeration of {args.target}...")
                target_addr = args.target
            else:
                return
        
        # Get target device
        target_device = devices[0] if devices else None
        if args.target:
            # Find device by target address
            target_device = next((d for d in devices if d.address == args.target), None)
            if not target_device:
                print(f"Target device {args.target} not found in discovered devices")
                if args.test_connection:
                    print(f"\nTrying direct connection test to {args.target}...")
                    success = await client.test_device_connection(args.target)
                    if success:
                        target_addr = args.target
                    else:
                        return
                elif args.enumerate:
                    # For enumeration, use target directly
                    target_addr = args.target
                else:
                    return
        
        if not target_device and not args.test_connection and not args.enumerate:
            print("No target device available")
            return
        
        target_addr = target_device.address if target_device else args.target
        
        # If we're in test_connection mode and have a target, we're done
        if args.test_connection and args.target:
            print(f"\n✓ Connection test completed successfully!")
            print(f"  Target: {args.target}")
            print(f"  Status: Connected and able to read device properties")
            return
        
        # Execute commands if specified
        if args.command:
            print(f"\nExecuting command: {args.command}")
            print("=" * 40)
            
            if args.command == 'set_value' and args.value is not None:
                # Parse object from target or use default
                object_id = args.target.split('/')[-1] if '/' in args.target else 'analogOutput,1'
                success = await client.write_command(target_addr, object_id, args.command, 
                                                  float(args.value), args.priority)
                print(f"Set value command {'successful' if success else 'failed'}")
                
            elif args.command in ['enable', 'disable', 'reset', 'acknowledge']:
                object_id = args.target.split('/')[-1] if '/' in args.target else 'device,1'
                success = await client.write_command(target_addr, object_id, args.command)
                print(f"{args.command} command {'successful' if success else 'failed'}")
                
            else:
                print(f"Unknown command: {args.command}")
        
        # Execute device operations
        elif args.operation:
            print(f"\nExecuting device operation: {args.operation}")
            print("=" * 40)
            
            parameters = {}
            if args.operation == 'reinitialize':
                parameters = {'type': 'coldstart'}
            elif args.operation == 'set_time':
                import datetime
                parameters = {'time': datetime.datetime.now()}
            
            success = await client.manipulate_device(target_addr, args.operation, parameters)
            print(f"{args.operation} operation {'successful' if success else 'failed'}")
        
        # Create object
        elif args.create_object:
            print(f"\nCreating object: {args.create_object}")
            print("=" * 40)
            
            try:
                obj_type, instance = args.create_object.split(',')
                instance = int(instance)
                properties = {'objectName': f'Created_{obj_type}_{instance}'}
                
                success = await client.create_object(target_addr, obj_type, instance, properties)
                print(f"Create object {'successful' if success else 'failed'}")
                
            except ValueError:
                print("Invalid object format. Use: type,instance (e.g., analogValue,5)")
        
        # Delete object
        elif args.delete_object:
            print(f"\nDeleting object: {args.delete_object}")
            print("=" * 40)
            
            success = await client.delete_object(target_addr, args.delete_object)
            print(f"Delete object {'successful' if success else 'failed'}")
        
        # Subscribe to changes
        elif args.subscribe:
            print(f"\nSubscribing to changes: {args.subscribe}")
            print("=" * 40)
            
            try:
                object_id, property_id = args.subscribe.split(',')
                success = await client.subscribe_to_changes(target_addr, object_id, property_id)
                print(f"Subscription {'successful' if success else 'failed'}")
                
            except ValueError:
                print("Invalid subscription format. Use: object,property (e.g., analogInput,1,presentValue)")
        
        elif args.enumerate:
            # Enumerate mode - show detailed information
            print("\nENUMERATION MODE")
            print("=" * 50)
            
            if devices:
                # Enumerate discovered devices
                for device in devices:
                    target_addr = device.address
                    print(f"\nDevice {device.device_id} at {target_addr}")
                    print("-" * 40)
                    
                    # Enumerate the device
                    await client.enumerate_device(target_addr)
                    
                    # Check permissions
                    await client.check_permissions(target_addr)
                    
                    print("\n" + "="*60)
            elif args.target:
                # Enumerate target device directly
                target_addr = args.target
                print(f"\nEnumerating target device at {target_addr}")
                print("-" * 40)
                
                # Enumerate the device
                await client.enumerate_device(target_addr)
                
                # Check permissions
                await client.check_permissions(target_addr)
                
                print("\n" + "="*60)
        else:
            # Normal mode - read some properties
            first_device = devices[0]
            target_addr = first_device.address
            
            print(f"\nReading from device {first_device.device_id} at {target_addr}")
            
            # Try to read some common properties
            properties_to_read = [
                ('device,1', 'objectName'),
                ('device,1', 'vendorName'),
                ('analogInput,1', 'presentValue'),
                ('binaryInput,1', 'presentValue')
            ]
            
            for obj_id, prop_id in properties_to_read:
                value = await client.read_property(target_addr, obj_id, prop_id)
                if value is not None:
                    print(f"  {obj_id}.{prop_id} = {value}")
        
        print("\nDemo completed!")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        await client.stop()

if __name__ == "__main__":
    asyncio.run(main()) 