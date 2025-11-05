"""
Remote Desktop Control - Client A (Controller)
Thành viên 2: Phạm Hồng Quang (B22DCCN652)

Chức năng:
- Kết nối đến server qua TCP
- Gửi lệnh điều khiển (mouse, keyboard, pause, continue)
- Nhận và hiển thị màn hình từ Client B (qua server)
- Test độ trễ control (ping test)
"""

import socket
import threading
import json
import time
from datetime import datetime
import sys

try:
    from PIL import Image
    import io
except ImportError:
    print("Warning: PIL not installed. Screen display will be disabled.")
    print("Install with: pip install Pillow")
    Image = None

class ControllerClient:
    def __init__(self, server_ip, server_port=5555, udp_port=5556):
        self.server_ip = server_ip
        self.server_port = server_port
        self.udp_port = udp_port
        self.socket = None
        self.udp_socket = None
        self.connected = False
        self.running = False
        self.screen_data = None
        
        # P2P UPGRADE
        self.p2p_enabled = False
        self.streamer_ip = None
        self.p2p_receive_count = 0
    
    def log(self, message):
        """Log với timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")
        
    def connect(self, session_id="", password=""):
        """Kết nối đến server với authentication"""
        try:
            # TCP connection
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            
            # Gửi thông tin client type với credentials
            client_info = json.dumps({
                'type': 'controller',
                'session_id': session_id,
                'password': password
            })
            self.socket.send(client_info.encode('utf-8'))
            
            # Wait for authentication response
            response_data = self.socket.recv(1024).decode('utf-8')
            response = json.loads(response_data)
            
            if response.get('status') != 'success':
                self.log(f"❌ Authentication failed: {response.get('message', 'Unknown error')}")
                self.socket.close()
                return False
            
            self.log(f"✅ Authentication successful")
            
            # P2P: Check if peer info available
            peer_info = response.get('peer_info')
            if peer_info and peer_info.get('ip'):
                self.streamer_ip = peer_info['ip']
                self.p2p_enabled = True
                self.log(f"🔗 P2P: Streamer IP received - {self.streamer_ip}")
                self.log(f"✅ P2P MODE ENABLED - Will receive directly from Streamer")
            
            # UDP socket để nhận screen data
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
            self.udp_socket.bind(('0.0.0.0', 0))
            udp_local_port = self.udp_socket.getsockname()[1]
            
            # Gửi registration packet để server biết địa chỉ UDP
            register_msg = json.dumps({'type': 'controller_udp', 'port': udp_local_port}).encode('utf-8')
            self.udp_socket.sendto(register_msg, (self.server_ip, self.udp_port))
            
            self.connected = True
            self.running = True
            self.log(f"Connected to server at {self.server_ip}:{self.server_port}")
            self.log(f"UDP listening on port {udp_local_port}")
            
            # Start thread để nhận màn hình qua UDP
            threading.Thread(target=self.receive_screen_data, daemon=True).start()
            
            return True
            
        except Exception as e:
            self.log(f"Connection failed: {e}")
            return False
            
    def send_command(self, command, payload=None):
        """Gửi lệnh điều khiển đến server"""
        if not self.connected:
            self.log("Not connected to server")
            return False
            
        try:
            cmd_data = {
                'command': command,
                'payload': payload or {},
                'timestamp': time.time()
            }
            
            json_data = json.dumps(cmd_data)
            self.socket.send(json_data.encode('utf-8'))
            self.log(f"Sent command: {command}")
            return True
            
        except Exception as e:
            self.log(f"Error sending command: {e}")
            self.connected = False
            return False
            
    def receive_screen_data(self):
        """Nhận dữ liệu màn hình từ server qua UDP"""
        self.log("Screen receiver started (UDP)")
        # Set timeout để tránh block forever
        self.udp_socket.settimeout(1.0)
        
        while self.running:
            try:
                # Nhận data qua UDP
                data, address = self.udp_socket.recvfrom(65535)
                
                # P2P: Track if receiving directly from Streamer
                if self.p2p_enabled and address[0] == self.streamer_ip:
                    self.p2p_receive_count += 1
                    if self.p2p_receive_count == 1:
                        self.log(f"🎉 P2P SUCCESS! Receiving directly from Streamer {address[0]}:{address[1]}")
                        # Notify server that P2P is working
                        try:
                            p2p_msg = json.dumps({'type': 'p2p_active'}).encode('utf-8')
                            self.udp_socket.sendto(p2p_msg, (self.server_ip, self.udp_port))
                        except:
                            pass
                
                # Bỏ qua registration messages
                try:
                    msg = json.loads(data.decode('utf-8'))
                    continue
                except:
                    pass
                
                # Screen data (JPEG)
                if len(data) > 1000:  # Sanity check - JPEG phải > 1KB
                    self.screen_data = data
                    
                    if Image:
                        try:
                            img = Image.open(io.BytesIO(data))
                            mode_str = "P2P" if (self.p2p_enabled and address[0] == self.streamer_ip) else "RELAY"
                            print(f"\r[{mode_str}] Frame: {len(data)}B, {img.size}, from {address[0]}", end='')
                        except:
                            pass
                            
            except socket.timeout:
                # Timeout bình thường, continue
                continue
            except Exception as e:
                if self.running:
                    self.log(f"Error receiving screen data: {e}")
                time.sleep(0.1)
                continue
                
        self.log("Screen receiver stopped")
        
    def mouse_click(self, x, y, button='left'):
        """Gửi lệnh click chuột"""
        return self.send_command('MOUSE_CLICK', {'x': x, 'y': y, 'button': button})
        
    def mouse_move(self, x, y):
        """Gửi lệnh di chuyển chuột"""
        return self.send_command('MOUSE_MOVE', {'x': x, 'y': y})
        
    def key_press(self, key):
        """Gửi lệnh nhấn phím"""
        return self.send_command('KEY_PRESS', {'key': key})
        
    def pause_stream(self):
        """Tạm dừng stream"""
        return self.send_command('PAUSE')
        
    def continue_stream(self):
        """Tiếp tục stream"""
        return self.send_command('CONTINUE')
        
    def ping_test(self):
        """Test độ trễ"""
        if not self.connected:
            return None
            
        start_time = time.time()
        success = self.send_command('PING')
        
        if success:
            latency = (time.time() - start_time) * 1000  # ms
            self.log(f"Ping latency: {latency:.2f}ms")
            return latency
        return None
        
    def disconnect(self):
        """Ngắt kết nối"""
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.send_command('DISCONNECT')
                self.socket.close()
            except:
                pass
                
        self.log("Disconnected from server")
        
    def interactive_mode(self):
        """Chế độ tương tác với người dùng"""
        print("\n" + "="*60)
        print("CONTROLLER CLIENT - INTERACTIVE MODE")
        print("="*60)
        print("\nAvailable commands:")
        print("  1. click <x> <y> [button]  - Click mouse at position")
        print("  2. move <x> <y>            - Move mouse to position")
        print("  3. key <key>               - Press key")
        print("  4. pause                   - Pause stream")
        print("  5. continue                - Continue stream")
        print("  6. ping                    - Test latency")
        print("  7. quit                    - Disconnect and quit")
        print("\nExamples:")
        print("  click 100 200 left")
        print("  move 150 250")
        print("  key enter")
        print("="*60 + "\n")
        
        while self.running and self.connected:
            try:
                cmd = input(">>> ").strip().lower()
                
                if not cmd:
                    continue
                    
                parts = cmd.split()
                action = parts[0]
                
                if action == 'click' and len(parts) >= 3:
                    x = int(parts[1])
                    y = int(parts[2])
                    button = parts[3] if len(parts) > 3 else 'left'
                    self.mouse_click(x, y, button)
                    
                elif action == 'move' and len(parts) >= 3:
                    x = int(parts[1])
                    y = int(parts[2])
                    self.mouse_move(x, y)
                    
                elif action == 'key' and len(parts) >= 2:
                    key = parts[1]
                    self.key_press(key)
                    
                elif action == 'pause':
                    self.pause_stream()
                    
                elif action == 'continue':
                    self.continue_stream()
                    
                elif action == 'ping':
                    self.ping_test()
                    
                elif action == 'quit':
                    print("Disconnecting...")
                    break
                    
                else:
                    print("Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nInterrupted. Disconnecting...")
                break
            except Exception as e:
                print(f"Error: {e}")
                
        self.disconnect()


def main():
    print("="*60)
    print("REMOTE DESKTOP CONTROL - CLIENT A (CONTROLLER)")
    print("Thành viên 2: Phạm Hồng Quang (B22DCCN652)")
    print("="*60)
    print()
    
    # Nhập IP server
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
    else:
        server_ip = input("Enter server IP address [localhost]: ").strip()
        if not server_ip:
            server_ip = 'localhost'
    
    # Khởi tạo client
    client = ControllerClient(server_ip, server_port=5555)
    
    # Kết nối
    if client.connect():
        print("\nConnection successful!")
        time.sleep(1)
        
        # Chế độ tương tác
        client.interactive_mode()
    else:
        print("Failed to connect to server")
        sys.exit(1)


if __name__ == "__main__":
    main()
