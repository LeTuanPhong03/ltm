"""
Remote Desktop Control - Server (Hybrid P2P + Relay)
Thành viên 1: Lê Tuấn Phong (B22DCCN615)

Chức năng:
- P2P Signaling: Giúp clients trao đổi IP/port để kết nối trực tiếp
- Relay fallback: Chuyển tiếp dữ liệu nếu P2P không thành công
- Nhận lệnh điều khiển từ Client A qua TCP (port 5555)
- Nhận dữ liệu màn hình từ Client B qua UDP (port 5556)
- Chuyển tiếp dữ liệu giữa 2 clients
- Log thông tin kết nối (IP, port, client ID)
"""

import socket
import threading
import json
import time
from datetime import datetime

class RemoteDesktopServer:
    def __init__(self, tcp_port=5555, udp_port=5556):
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        
        # Socket servers
        self.tcp_socket = None
        self.udp_socket = None
        
        # Client connections
        self.controller_client = None  # Client A (Controller)
        self.streamer_client = None    # Client B (Streamer)
        
        # Authentication - store streamer credentials
        self.streamer_credentials = {
            'session_id': None,
            'password': None
        }
        
        # Client info for logging
        self.client_info = {
            'controller': {'ip': None, 'port': None, 'udp_port': None, 'udp_addr': None, 'socket': None, 'id': 'ClientA', 'connected_at': None, 'external_udp_port': None},
            'streamer': {'ip': None, 'port': None, 'id': 'ClientB', 'connected_at': None, 'udp_addr': None}
        }
        
        # P2P mode tracking
        self.p2p_mode = False  # Track if clients are using P2P
        
        self.running = False
        
    def log(self, message):
        """Log với timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")
        
    def start(self):
        """Khởi động server"""
        self.running = True
        
        # Khởi tạo TCP socket
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.bind(('0.0.0.0', self.tcp_port))
        self.tcp_socket.listen(5)
        self.log(f"TCP Server started on port {self.tcp_port}")
        
        # Khởi tạo UDP socket
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Tăng buffer size cho UDP
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2 * 1024 * 1024)  # 2MB recv buffer
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2 * 1024 * 1024)  # 2MB send buffer
        self.udp_socket.bind(('0.0.0.0', self.udp_port))
        self.log(f"UDP Server started on port {self.udp_port}")
        
        # Start threads
        tcp_thread = threading.Thread(target=self.handle_tcp_connections, daemon=True)
        udp_thread = threading.Thread(target=self.handle_udp_data, daemon=True)
        
        tcp_thread.start()
        udp_thread.start()
        
        self.log("Server is ready to accept connections")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.log("Server shutting down...")
            self.stop()
            
    def handle_tcp_connections(self):
        """Xử lý kết nối TCP từ clients"""
        while self.running:
            try:
                client_socket, client_address = self.tcp_socket.accept()
                
                # Nhận thông tin client type (controller hoặc streamer)
                client_type_data = client_socket.recv(1024).decode('utf-8')
                client_info_json = json.loads(client_type_data)
                client_type = client_info_json.get('type', 'unknown')
                
                if client_type == 'controller':
                    # Verify credentials for controller
                    session_id = client_info_json.get('session_id', '')
                    password = client_info_json.get('password', '')
                    
                    if self.verify_credentials(session_id, password):
                        self.controller_client = client_socket
                        self.client_info['controller']['ip'] = client_address[0]
                        self.client_info['controller']['port'] = client_address[1]
                        self.client_info['controller']['connected_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        self.log(f"✅ TCP Client A (Controller) authenticated and connected: {client_address[0]}:{client_address[1]}")
                        
                        # Send success response with P2P peer info
                        response = {
                            'status': 'success',
                            'message': 'Authentication successful',
                            'peer_info': self.get_streamer_peer_info()
                        }
                        client_socket.send(json.dumps(response).encode('utf-8'))
                        
                        # Send Controller's info to Streamer for P2P
                        self.send_controller_info_to_streamer(client_address)
                        
                        # Start thread để nhận lệnh từ controller
                        threading.Thread(target=self.handle_controller_commands, 
                                       args=(client_socket,), daemon=True).start()
                    else:
                        self.log(f"❌ Authentication failed for {client_address[0]}:{client_address[1]}")
                        # Send failure response
                        response = json.dumps({'status': 'error', 'message': 'Invalid Session ID or Password'})
                        client_socket.send(response.encode('utf-8'))
                        client_socket.close()
                    
                elif client_type == 'streamer':
                    # Store streamer credentials
                    session_id = client_info_json.get('session_id', '')
                    password = client_info_json.get('password', '')
                    
                    self.streamer_credentials['session_id'] = session_id
                    self.streamer_credentials['password'] = password
                    
                    self.streamer_client = client_socket
                    self.client_info['streamer']['ip'] = client_address[0]
                    self.client_info['streamer']['port'] = client_address[1]
                    self.client_info['streamer']['connected_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    self.log(f"TCP Client B (Streamer) connected: {client_address[0]}:{client_address[1]}")
                    self.log(f"🔑 Session ID: {session_id}, Password: {password}")
                    
            except Exception as e:
                if self.running:
                    self.log(f"Error accepting TCP connection: {e}")
    
    def verify_credentials(self, session_id, password):
        """Verify controller credentials against streamer credentials"""
        if not self.streamer_credentials['session_id']:
            self.log("⚠️  No streamer connected yet")
            return False
        
        is_valid = (session_id == self.streamer_credentials['session_id'] and 
                   password == self.streamer_credentials['password'])
        
        return is_valid
    
    def get_streamer_peer_info(self):
        """Get Streamer's connection info for P2P"""
        if not self.client_info['streamer']['ip']:
            return None
        
        return {
            'ip': self.client_info['streamer']['ip'],
            'udp_addr': self.client_info['streamer'].get('udp_addr'),
            'connected': self.streamer_client is not None
        }
    
    def send_controller_info_to_streamer(self, controller_addr):
        """Send Controller's info to Streamer for P2P connection"""
        if not self.streamer_client:
            return
        
        try:
            peer_info = {
                'command': 'PEER_INFO',
                'payload': {
                    'peer_ip': controller_addr[0],
                    'peer_port': controller_addr[1],
                    'message': 'Controller connected, you can try P2P'
                }
            }
            self.streamer_client.send(json.dumps(peer_info).encode('utf-8'))
            self.log(f"📡 Sent Controller info to Streamer for P2P attempt")
        except Exception as e:
            self.log(f"Error sending peer info to Streamer: {e}")
                    
    def handle_controller_commands(self, client_socket):
        """Nhận lệnh từ Controller và chuyển đến Streamer"""
        while self.running:
            try:
                data = client_socket.recv(4096)
                if not data:
                    break
                    
                # Parse command
                command = json.loads(data.decode('utf-8'))
                self.log(f"Received command from Controller: {command.get('command', 'unknown')}")
                
                # Chuyển tiếp lệnh đến Streamer
                if self.streamer_client:
                    try:
                        self.streamer_client.send(data)
                        self.log(f"Command forwarded to Streamer")
                    except Exception as e:
                        self.log(f"Error forwarding to Streamer: {e}")
                else:
                    self.log("Warning: No Streamer connected to receive command")
                    
            except Exception as e:
                self.log(f"Error handling controller command: {e}")
                break
                
        self.log("Controller disconnected")
        self.controller_client = None
        
    def handle_udp_data(self):
        """Nhận dữ liệu màn hình từ Streamer qua UDP và forward qua UDP (Relay mode)"""
        relay_packet_count = 0
        while self.running:
            try:
                data, address = self.udp_socket.recvfrom(65535)
                
                # Kiểm tra nếu là registration packet từ Controller
                try:
                    msg = json.loads(data.decode('utf-8'))
                    if msg.get('type') == 'controller_udp':
                        # Lưu địa chỉ UDP của Controller
                        self.client_info['controller']['udp_port'] = address[1]
                        self.client_info['controller']['udp_addr'] = address
                        self.client_info['controller']['external_udp_port'] = address[1]
                        print(f"📡 Controller UDP registered: {address}")
                        continue
                    elif msg.get('type') == 'p2p_active':
                        # Client báo đang dùng P2P
                        self.p2p_mode = True
                        self.log(f"✅ P2P mode activated! Server will reduce relay load.")
                        continue
                except:
                    pass
                
                # Log lần đầu nhận từ Streamer
                if not self.client_info['streamer']['udp_addr']:
                    self.client_info['streamer']['udp_addr'] = address
                    self.log(f"📡 UDP Client B (Streamer) sending from: {address[0]}:{address[1]}")
                
                # Forward screen data qua UDP đến Controller (Relay mode)
                if not self.p2p_mode and self.client_info['controller']['udp_addr']:
                    relay_packet_count += 1
                    if relay_packet_count % 100 == 0:
                        self.log(f"🔄 RELAY MODE: Forwarded {relay_packet_count} packets (fallback active)")
                        
                # Forward screen data qua UDP đến Controller
                if self.client_info['controller']['udp_addr']:
                    try:
                        self.udp_socket.sendto(data, self.client_info['controller']['udp_addr'])
                    except Exception as e:
                        # Không log error UDP vì sẽ spam console
                        pass
                        
            except Exception as e:
                if self.running:
                    # Không log UDP errors vì Windows UDP có thể gây spam
                    pass
                    
    def stop(self):
        """Dừng server"""
        self.running = False
        
        if self.tcp_socket:
            self.tcp_socket.close()
        if self.udp_socket:
            self.udp_socket.close()
        if self.controller_client:
            self.controller_client.close()
        if self.streamer_client:
            self.streamer_client.close()
            
        self.log("Server stopped")
        
    def print_status(self):
        """In ra trạng thái kết nối"""
        print("\n" + "="*60)
        print("SERVER STATUS")
        print("="*60)
        print(f"Controller (Client A): {self.client_info['controller']['ip'] or 'Not connected'}")
        if self.client_info['controller']['ip']:
            print(f"  - Port: {self.client_info['controller']['port']}")
            print(f"  - Connected at: {self.client_info['controller']['connected_at']}")
        print(f"\nStreamer (Client B): {self.client_info['streamer']['ip'] or 'Not connected'}")
        if self.client_info['streamer']['ip']:
            print(f"  - Port: {self.client_info['streamer']['port']}")
            print(f"  - Connected at: {self.client_info['streamer']['connected_at']}")
        print("="*60 + "\n")


if __name__ == "__main__":
    print("="*60)
    print("REMOTE DESKTOP CONTROL - SERVER")
    print("Thành viên 1: Lê Tuấn Phong (B22DCCN615)")
    print("="*60)
    print()
    
    server = RemoteDesktopServer(tcp_port=5555, udp_port=5556)
    
    # Print status every 10 seconds
    def status_printer():
        while server.running:
            time.sleep(10)
            server.print_status()
    
    status_thread = threading.Thread(target=status_printer, daemon=True)
    status_thread.start()
    
    server.start()
