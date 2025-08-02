# OPC-UA Client

A modern Python OPC-UA client implementation using the [python-opcua](https://python-opcua.readthedocs.io/en/latest/client.html) library. This client provides comprehensive functionality for interacting with OPC-UA servers including browsing, reading, writing, and subscribing to nodes.

## Features

- **Server Discovery**: Discover OPC-UA servers on the network
- **Endpoint Management**: Get and analyze server endpoints
- **Node Browsing**: Browse the OPC-UA address space
- **Read Operations**: Read single or multiple nodes
- **Write Operations**: Write values to single or multiple nodes
- **Method Calls**: Call methods on OPC-UA objects
- **Subscriptions**: Create and manage data change subscriptions
- **Security Support**: Support for various security policies and modes
- **Authentication**: Username/password and certificate-based authentication
- **Async Support**: Full async/await support for modern Python applications

## Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Install Dependencies

```bash
# Install the python-opcua library
pip install opcua

# For development (optional)
pip install -r requirements.txt
```

## Quick Start

### Basic Connection

```python
import asyncio
from opcua_client import OPCUAClient

async def main():
    # Create client
    client = OPCUAClient(url="opc.tcp://localhost:4840")
    
    # Start client
    await client.start()
    
    # Test connection
    if await client.test_connection():
        print("Connected successfully!")
    
    # Stop client
    await client.stop()

asyncio.run(main())
```

### Command Line Usage

```bash
# Test connection to a server
python opcua_client.py --url opc.tcp://localhost:4840 --test-connection

# Browse nodes starting from the root
python opcua_client.py --url opc.tcp://localhost:4840 --browse

# Read a specific node
python opcua_client.py --url opc.tcp://localhost:4840 --read-node "i=84"

# Write to a node
python opcua_client.py --url opc.tcp://localhost:4840 --write-node "i=84,123"

# Create a subscription
python opcua_client.py --url opc.tcp://localhost:4840 --create-subscription "my_sub,ns=2;s=MyVariable"

# Brute force credentials
python opcua_client.py --url opc.tcp://localhost:4840 --password-wordlist passwords.txt

# Brute force with custom usernames and delay
python opcua_client.py --url opc.tcp://localhost:4840 --password-wordlist passwords.txt --username-wordlist usernames.txt --brute-force-delay 2.0

### Testing with Docker OPC-UA Server

You can test the client using Microsoft's OPC-UA test server:

```bash
# Start the test server
docker run --name opc-ua-test-server -p 51210:51210 -p 51211:51211 mcr.microsoft.com/iot/opc-ua-test-server -p 51210

# Test connection to the Docker server
python opcua_client.py --url opc.tcp://localhost:51210 --test-connection

# Browse nodes on the test server
python opcua_client.py --url opc.tcp://localhost:51210 --browse

# Read a specific node from the test server
python opcua_client.py --url opc.tcp://localhost:51210 --read-node "ns=2;s=Device1_ProductionStatus"
```

## API Reference

### OPCUAClient Class

The main client class for OPC-UA operations.

#### Constructor

```python
OPCUAClient(
    url: str = None,
    timeout: int = 4,
    security_policy: str = "None",
    security_mode: str = "None",
    username: str = None,
    password: str = None,
    certificate_path: str = None,
    private_key_path: str = None
)
```

**Parameters:**
- `url`: OPC-UA server URL (e.g., "opc.tcp://localhost:4840")
- `timeout`: Connection timeout in seconds
- `security_policy`: Security policy ("None", "Basic128Rsa15", "Basic256", "Basic256Sha256")
- `security_mode`: Security mode ("None", "Sign", "SignAndEncrypt")
- `username`: Username for authentication
- `password`: Password for authentication
- `certificate_path`: Path to client certificate
- `private_key_path`: Path to client private key

#### Methods

##### Connection Management

```python
async def start() -> bool
async def connect() -> bool
async def disconnect() -> None
async def stop() -> None
```

##### Server Discovery and Information

```python
async def discover_servers() -> List[OPCUAServer]
async def get_endpoints() -> List[Dict[str, Any]]
async def get_server_info() -> Optional[Dict[str, Any]]
async def test_connection() -> bool
```

##### Node Operations

```python
async def browse_nodes(node_id: str = "i=84", max_results: int = 100) -> List[OPCUANode]
async def read_node(node_id: str) -> Optional[OPCUANode]
async def read_nodes(node_ids: List[str]) -> List[Optional[OPCUANode]]
async def write_node(node_id: str, value: Any) -> bool
async def write_nodes(node_ids: List[str], values: List[Any]) -> List[bool]
```

##### Method Calls

```python
async def call_method(object_node_id: str, method_node_id: str, arguments: List[Any] = None) -> Optional[Any]
```

##### Subscriptions

```python
async def create_subscription(subscription_name: str, nodes: List[str], period: int = 1000) -> Optional[str]
async def delete_subscription(subscription_name: str) -> bool
```

## Data Structures

### OPCUAServer

Represents an OPC-UA server discovered on the network.

```python
@dataclass
class OPCUAServer:
    url: str
    name: str
    application_uri: str
    product_uri: str
    server_uri: str
    security_policy_uri: str
    security_mode: str
    transport_profile_uri: str
```

### OPCUANode

Represents an OPC-UA node in the address space.

```python
@dataclass
class OPCUANode:
    node_id: str
    browse_name: str
    display_name: str
    node_class: str
    data_type: Optional[str] = None
    value: Optional[Any] = None
    access_level: Optional[int] = None
    user_access_level: Optional[int] = None
```

## Usage Examples

### 1. Server Discovery

```python
async def discover_servers_example():
    client = OPCUAClient(url="opc.tcp://localhost:4840")
    await client.start()
    
    servers = await client.discover_servers()
    for server in servers:
        print(f"Found server: {server.name} at {server.url}")
    
    await client.stop()
```

### 2. Browsing the Address Space

```python
async def browse_example():
    client = OPCUAClient(url="opc.tcp://localhost:4840")
    await client.start()
    
    # Browse nodes starting from the Objects folder
    nodes = await client.browse_nodes("i=85", max_results=50)
    
    for node in nodes:
        print(f"Node: {node.browse_name} ({node.node_id})")
        if node.value is not None:
            print(f"  Value: {node.value}")
    
    await client.stop()
```

### 3. Reading and Writing Values

```python
async def read_write_example():
    client = OPCUAClient(url="opc.tcp://localhost:4840")
    await client.start()
    
    # Read a node
    node = await client.read_node("ns=2;s=MyVariable")
    if node:
        print(f"Current value: {node.value}")
    
    # Write to a node
    success = await client.write_node("ns=2;s=MyVariable", 42)
    if success:
        print("Write successful!")
    
    await client.stop()
```

### 4. Batch Operations

```python
async def batch_operations_example():
    client = OPCUAClient(url="opc.tcp://localhost:4840")
    await client.start()
    
    # Read multiple nodes
    node_ids = ["ns=2;s=Var1", "ns=2;s=Var2", "ns=2;s=Var3"]
    nodes = await client.read_nodes(node_ids)
    
    for i, node in enumerate(nodes):
        if node:
            print(f"Node {i+1}: {node.value}")
    
    # Write multiple nodes
    values = [10, 20, 30]
    results = await client.write_nodes(node_ids, values)
    
    success_count = sum(results)
    print(f"Successfully wrote {success_count}/{len(node_ids)} nodes")
    
    await client.stop()
```

### 5. Subscriptions

```python
async def subscription_example():
    client = OPCUAClient(url="opc.tcp://localhost:4840")
    await client.start()
    
    # Create subscription
    subscription_name = await client.create_subscription(
        "my_subscription",
        ["ns=2;s=MyVariable", "ns=2;s=AnotherVariable"]
    )
    
    if subscription_name:
        print(f"Subscription '{subscription_name}' created")
        
        # Keep connection alive to receive notifications
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Stopping subscription...")
    
    await client.stop()
```

### 6. Method Calls

```python
async def method_call_example():
    client = OPCUAClient(url="opc.tcp://localhost:4840")
    await client.start()
    
    # Call a method
    result = await client.call_method(
        object_node_id="ns=2;s=MyObject",
        method_node_id="ns=2;s=MyMethod",
        arguments=["param1", 42]
    )
    
    if result is not None:
        print(f"Method call result: {result}")
    
    await client.stop()
```

### 7. Security and Authentication

```python
async def secure_connection_example():
    client = OPCUAClient(
        url="opc.tcp://localhost:4840",
        security_policy="Basic256Sha256",
        security_mode="SignAndEncrypt",
        username="admin",
        password="password",
        certificate_path="/path/to/cert.pem",
        private_key_path="/path/to/key.pem"
    )
    
    await client.start()
    
    if await client.test_connection():
        print("Secure connection established!")
    
    await client.stop()
```

## Command Line Options

The client supports extensive command line options:

### Connection Options
- `--url`: OPC-UA server URL (required)
- `--timeout`: Connection timeout in seconds
- `--security-policy`: Security policy
- `--security-mode`: Security mode
- `--username`: Username for authentication
- `--password`: Password for authentication
- `--certificate`: Path to client certificate
- `--private-key`: Path to client private key

### Operation Options
- `--discover-servers`: Discover OPC-UA servers
- `--get-endpoints`: Get server endpoints
- `--test-connection`: Test connection to server
- `--get-server-info`: Get server information
- `--browse`: Browse nodes (optional start node ID)
- `--read-node`: Read a single node
- `--read-nodes`: Read multiple nodes (comma-separated)
- `--write-node`: Write to a node (format: node_id,value)
- `--write-nodes`: Write to multiple nodes (format: node_id1,value1,node_id2,value2,...)
- `--call-method`: Call a method (format: object_id,method_id,arg1,arg2,...)
- `--create-subscription`: Create subscription (format: name,node_id1,node_id2,...)
- `--delete-subscription`: Delete subscription by name
- `--password-wordlist`: Path to password wordlist file for brute force testing
- `--username-wordlist`: Path to username wordlist file for brute force testing (optional)
- `--brute-force-delay`: Delay between brute force attempts in seconds (default: 1.0)
- `--max-results`: Maximum results for browse operations

## Error Handling

The client includes comprehensive error handling:

```python
try:
    client = OPCUAClient(url="opc.tcp://localhost:4840")
    await client.start()
    
    if not await client.connect():
        print("Failed to connect to server")
        return
    
    # Perform operations...
    
except Exception as e:
    print(f"Error: {e}")
finally:
    await client.stop()
```

## Logging

The client uses Python's logging module for detailed operation tracking:

```python
import logging

# Set log level
logging.basicConfig(level=logging.INFO)

# Create client (logging is automatically configured)
client = OPCUAClient(url="opc.tcp://localhost:4840")
```

## Security Testing

### Brute Force Testing

The client includes a brute force testing feature for security assessment:

```bash
# Basic brute force with default usernames
python opcua_client.py --url opc.tcp://localhost:4840 --password-wordlist passwords.txt

# Brute force with custom usernames
python opcua_client.py --url opc.tcp://localhost:4840 --password-wordlist passwords.txt --username-wordlist usernames.txt

# Brute force with custom delay (to avoid overwhelming the server)
python opcua_client.py --url opc.tcp://localhost:4840 --password-wordlist passwords.txt --brute-force-delay 2.0
```

### Sample Wordlists

The client includes sample wordlists for testing:

- `sample_passwords.txt` - Common industrial passwords
- Create custom wordlists for specific environments

### Brute Force Features

- **Progress tracking**: Shows current attempt and total attempts
- **Rate limiting**: Configurable delay between attempts
- **Success detection**: Validates credentials and tests data access
- **Detailed logging**: Shows successful and failed attempts
- **Multiple usernames**: Supports custom username lists

## Security Considerations

1. **Certificates**: Use proper certificates for production environments
2. **Authentication**: Implement strong authentication mechanisms
3. **Network Security**: Use VPNs or firewalls to protect OPC-UA traffic
4. **Access Control**: Configure proper access controls on OPC-UA servers
5. **Monitoring**: Monitor connections and activities for security threats
6. **Brute Force Protection**: Implement account lockout and rate limiting on OPC-UA servers

## Troubleshooting

### Common Issues

1. **Connection Refused**: Check if the OPC-UA server is running and accessible
2. **Authentication Failed**: Verify username/password or certificate credentials
3. **Security Policy Mismatch**: Ensure client and server support the same security policies
4. **Node Not Found**: Verify node IDs are correct and accessible
5. **Permission Denied**: Check access rights for read/write operations

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## References

- [python-opcua Documentation](https://python-opcua.readthedocs.io/en/latest/client.html)
- [OPC Foundation](https://opcfoundation.org/)
- [OPC-UA Specification](https://opcfoundation.org/developer-tools/specifications-unified-architecture)
- [OPC-UA Exploit Framework](https://github.com/claroty/opcua-exploit-framework) - Security testing and exploitation framework for OPC-UA 