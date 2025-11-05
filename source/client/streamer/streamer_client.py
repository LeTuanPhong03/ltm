"""
Remote Desktop Control - Client B (Streamer)
Thành viên 3: Nguyễn Đình Tuấn (B22DCCN759)

Chức năng:
- Kết nối đến server qua TCP (nhận lệnh) và UDP (gửi màn hình)
- Capture màn hình và gửi qua UDP đến server
- Nhận và thực thi lệnh điều khiển từ server (qua Client A)
- Xử lý lệnh pause, continue để điều khiển stream
- Hướng dẫn chạy Client B
"""

import socket
import threading
import json
import time
from datetime import datetime
import sys
import io
import random
import string

try:
    import mss
    import mss.tools
except ImportError:
    print("Error: mss library not installed")
    print("Install with: pip install mss")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow library not installed")
    print("Install with: pip install Pillow")
    sys.exit(1)

try:
    import numpy as np
except ImportError:
    print("Error: numpy library not installed")
    print("Install with: pip install numpy")
    sys.exit(1)

try:
    import pyautogui
except ImportError:
    print("Warning: pyautogui not installed. Mouse/keyboard control will be disabled.")
    print("Install with: pip install pyautogui")
    pyautogui = None


class StreamerClient:
    def __init__(self, server_ip, tcp_port=5555, udp_port=5556):
        self.server_ip = server_ip
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        
        self.tcp_socket = None
        self.udp_socket = None
        
        self.connected = False
        self.running = False
        self.streaming = True  # Control stream on/off
        
        # Authentication credentials
        self.session_id = self.generate_session_id()
        self.password = self.generate_password()
        
        # Don't create mss here, create in thread
        self.screen_capturer = None
        
        # Statistics
        self.frames_sent = 0
        self.commands_received = 0
        
        # LEVEL 1 UPGRADE: Adaptive quality control
        self.jpeg_quality = 70  # Start with good quality
        self.target_fps = 30
        self.frame_times = []  # Track timing for adaptive adjustment
        self.max_frame_time_samples = 10
        
        # LEVEL 2 UPGRADE: Motion detection
        self.last_frame = None
        self.motion_threshold = 5.0  # % change threshold
        self.frames_since_last_send = 0
        self.max_skip_frames = 5  # Don't skip more than 5 frames even if no motion
        
        # P2P UPGRADE: Peer-to-peer connection
        self.p2p_enabled = False
        self.controller_ip = None
        self.controller_udp_port = None
        self.p2p_tested = False
    
    def generate_session_id(self):
        """Generate unique session ID (9 digits)"""
        return ''.join(random.choices(string.digits, k=9))
    
    def generate_password(self):
        """Generate random 6-character password"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        
    def log(self, message):
        """Log với timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")
        
    def connect(self):
        """Kết nối đến server"""
        try:
            # TCP connection để nhận lệnh
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.connect((self.server_ip, self.tcp_port))
            
            # Gửi thông tin client type với credentials
            client_info = json.dumps({
                'type': 'streamer',
                'session_id': self.session_id,
                'password': self.password
            })
            self.tcp_socket.send(client_info.encode('utf-8'))
            
            # UDP socket để gửi màn hình
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            self.connected = True
            self.running = True
            self.log(f"Connected to server at {self.server_ip}")
            self.log(f"TCP port: {self.tcp_port}, UDP port: {self.udp_port}")
            self.log(f"🔑 Session ID: {self.session_id}")
            self.log(f"🔑 Password: {self.password}")
            
            return True
            
        except Exception as e:
            self.log(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Ngắt kết nối khỏi server"""
        try:
            self.running = False
            self.connected = False
            
            if self.tcp_socket:
                self.tcp_socket.close()
                self.tcp_socket = None
            
            if self.udp_socket:
                self.udp_socket.close()
                self.udp_socket = None
            
            if self.screen_capturer:
                self.screen_capturer.close()
                self.screen_capturer = None
            
            self.log("Disconnected from server")
            return True
            
        except Exception as e:
            self.log(f"Error disconnecting: {e}")
            return False
    
    def detect_motion(self, current_img):
        """
        LEVEL 2: Detect if there's significant motion between frames
        Returns: (has_motion, change_percentage)
        """
        try:
            # Convert to grayscale numpy array for comparison
            current_gray = np.array(current_img.convert('L').resize((160, 120)))  # Small size for speed
            
            if self.last_frame is None:
                self.last_frame = current_gray
                return True, 100.0  # First frame always send
            
            # Calculate difference
            diff = np.abs(current_gray.astype(float) - self.last_frame.astype(float))
            change_percent = (np.sum(diff > 30) / diff.size) * 100  # Count pixels with >30 difference
            
            has_motion = change_percent > self.motion_threshold
            
            # Update last frame if motion detected
            if has_motion:
                self.last_frame = current_gray
            
            return has_motion, change_percent
            
        except Exception as e:
            self.log(f"Motion detection error: {e}")
            return True, 100.0  # On error, send frame
            
    def capture_screen(self):
        """Capture màn hình và nén thành JPEG"""
        try:
            # Create mss instance in this thread if not exists
            if self.screen_capturer is None:
                self.screen_capturer = mss.mss()
            
            # Capture toàn bộ màn hình
            monitor = self.screen_capturer.monitors[1]  # Monitor chính
            screenshot = self.screen_capturer.grab(monitor)
            
            # Convert sang PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            # Lưu kích thước gốc để tính tỷ lệ chính xác
            original_width = screenshot.size[0]
            original_height = screenshot.size[1]
            
            # Resize 800x600 với quality cao hơn cho hình ảnh sắc nét
            resized_img = img.resize((800, 600), Image.Resampling.LANCZOS)
            
            # LEVEL 1: Use adaptive quality
            buffer = io.BytesIO()
            resized_img.save(buffer, format='JPEG', quality=self.jpeg_quality, optimize=True, progressive=True)
            jpeg_data = buffer.getvalue()
            
            # Log warning nếu frame quá lớn
            if len(jpeg_data) > 65000:
                self.log(f"⚠️ Frame too large: {len(jpeg_data)} bytes - may drop!")
            
            return jpeg_data, resized_img  # Return both JPEG and PIL image for motion detection
            
        except Exception as e:
            self.log(f"Error capturing screen: {e}")
            return None
            
    def stream_screen(self):
        """Stream màn hình liên tục qua UDP"""
        frame_count = 0
        self.log("Stream thread started, waiting for streaming to be enabled...")
        
        while self.running:
            try:
                if not self.streaming:
                    time.sleep(0.1)
                    continue
                
                # Log lần đầu streaming
                if frame_count == 0:
                    self.log(f"🎬 Starting UDP streaming to {self.server_ip}:{self.udp_port}")
                
                # LEVEL 1: Track timing for adaptive quality
                frame_start = time.time()
                
                # Capture màn hình
                result = self.capture_screen()
                
                if result:
                    # Unpack result based on return type
                    if isinstance(result, tuple):
                        jpeg_data, pil_img = result
                    else:
                        # Backward compatibility if no tuple returned
                        jpeg_data = result
                        pil_img = None
                    
                    # LEVEL 2: Motion detection - skip if no motion
                    should_send = True
                    motion_percent = 0.0
                    
                    if pil_img is not None:
                        has_motion, motion_percent = self.detect_motion(pil_img)
                        self.frames_since_last_send += 1
                        
                        # Don't send if no motion, unless too many frames skipped
                        if not has_motion and self.frames_since_last_send < self.max_skip_frames:
                            should_send = False
                        else:
                            self.frames_since_last_send = 0
                    
                    if should_send:
                        # P2P UPGRADE: Gửi qua UDP - thử P2P trước, fallback relay
                        try:
                            # Try P2P if enabled and controller info available
                            if self.p2p_enabled and self.controller_ip and self.controller_udp_port:
                                try:
                                    # Send directly to Controller via P2P
                                    self.udp_socket.sendto(jpeg_data, (self.controller_ip, self.controller_udp_port))
                                    if frame_count % 100 == 0 and not self.p2p_tested:
                                        self.log(f"✅ P2P MODE ACTIVE: Sending directly to Controller {self.controller_ip}:{self.controller_udp_port}")
                                        self.p2p_tested = True
                                except Exception as p2p_error:
                                    # P2P failed, fallback to relay
                                    if self.p2p_enabled:
                                        self.log(f"⚠️  P2P failed, falling back to RELAY: {p2p_error}")
                                        self.p2p_enabled = False
                                    self.udp_socket.sendto(jpeg_data, (self.server_ip, self.udp_port))
                            else:
                                # No P2P, use relay through server
                                self.udp_socket.sendto(jpeg_data, (self.server_ip, self.udp_port))
                        
                            frame_count += 1
                            self.frames_sent += 1
                        
                            # LEVEL 1: Adaptive quality adjustment
                            frame_time = time.time() - frame_start
                            self.frame_times.append(frame_time)
                            if len(self.frame_times) > self.max_frame_time_samples:
                                self.frame_times.pop(0)
                        
                            # Adjust quality every 30 frames
                            if frame_count % 30 == 0:
                                avg_time = sum(self.frame_times) / len(self.frame_times)
                                target_time = 1.0 / self.target_fps
                            
                                # If too slow, reduce quality
                                if avg_time > target_time * 1.2 and self.jpeg_quality > 50:
                                    self.jpeg_quality = max(50, self.jpeg_quality - 5)
                                    self.log(f"📉 Reducing quality to {self.jpeg_quality} (avg time: {avg_time:.3f}s)")
                                # If fast enough, increase quality
                                elif avg_time < target_time * 0.8 and self.jpeg_quality < 85:
                                    self.jpeg_quality = min(85, self.jpeg_quality + 5)
                                    self.log(f"📈 Increasing quality to {self.jpeg_quality} (avg time: {avg_time:.3f}s)")
                            
                                self.log(f"📊 Frames: {frame_count}, Size: {len(jpeg_data)}B, Q: {self.jpeg_quality}, Motion: {motion_percent:.1f}%")
                        except Exception as e:
                            self.log(f"❌ Error sending UDP packet: {e}")
                    
                    # FPS control: ~30 FPS cho mượt mà hơn
                    time.sleep(0.033)  # 1/30 = 0.033s - Level 1 upgrade
                    
            except Exception as e:
                self.log(f"Stream error: {e}")
                break
                
        self.log("Screen streaming stopped")
        
    def handle_commands(self):
        """Nhận và xử lý lệnh từ server"""
        while self.running:
            try:
                data = self.tcp_socket.recv(4096)
                if not data:
                    break
                    
                command = json.loads(data.decode('utf-8'))
                cmd_type = command.get('command', 'unknown')
                payload = command.get('payload', {})
                
                self.commands_received += 1
                self.log(f"Received command: {cmd_type}")
                
                # Xử lý các lệnh
                if cmd_type == 'PEER_INFO':
                    # P2P: Nhận thông tin Controller để kết nối trực tiếp
                    self.controller_ip = payload.get('peer_ip')
                    self.controller_udp_port = self.udp_port  # Assume same port
                    self.p2p_enabled = True
                    self.log(f"🔗 P2P: Received Controller info - {self.controller_ip}:{self.controller_udp_port}")
                    self.log(f"✅ P2P MODE ENABLED - Will send directly to Controller")
                    
                elif cmd_type == 'MOUSE_CLICK':
                    self.handle_mouse_click(payload)
                    
                elif cmd_type == 'MOUSE_MOVE':
                    self.handle_mouse_move(payload)
                    
                elif cmd_type == 'KEY_PRESS':
                    self.handle_key_press(payload)
                    
                elif cmd_type == 'PAUSE':
                    self.streaming = False
                    self.log("Stream paused")
                    
                elif cmd_type == 'CONTINUE':
                    self.streaming = True
                    self.log("Stream resumed")
                    
                elif cmd_type == 'DISCONNECT':
                    self.log("Disconnect requested")
                    self.running = False
                    break
                    
            except Exception as e:
                if self.running:
                    self.log(f"Error handling command: {e}")
                break
                
        self.log("Command handler stopped")
        
    def handle_mouse_click(self, payload):
        """Xử lý lệnh click chuột"""
        if not pyautogui:
            return
            
        try:
            x = payload.get('x', 0)
            y = payload.get('y', 0)
            button = payload.get('button', 'left')
            
            # Scale coordinates từ 800x600 (stream size) về resolution thực
            screen_width, screen_height = pyautogui.size()
            real_x = int(x * screen_width / 800)
            real_y = int(y * screen_height / 600)
            
            # Click tại vị trí thực
            pyautogui.click(real_x, real_y, button=button)
            self.log(f"✅ Clicked at ({real_x}, {real_y}) with {button} button")
            
        except Exception as e:
            self.log(f"Error handling mouse click: {e}")
            
    def handle_mouse_move(self, payload):
        """Xử lý lệnh di chuyển chuột"""
        if not pyautogui:
            return
            
        try:
            x = payload.get('x', 0)
            y = payload.get('y', 0)
            
            # Scale coordinates từ 800x600 về resolution thực
            screen_width, screen_height = pyautogui.size()
            real_x = int(x * screen_width / 800)
            real_y = int(y * screen_height / 600)
            
            pyautogui.moveTo(real_x, real_y)
            self.log(f"✅ Moved mouse to ({real_x}, {real_y})")
            
        except Exception as e:
            self.log(f"Error handling mouse move: {e}")
            
    def handle_key_press(self, payload):
        """Xử lý lệnh nhấn phím"""
        if not pyautogui:
            return
            
        try:
            key = payload.get('key', '')
            
            pyautogui.press(key)
            self.log(f"✅ Pressed key: '{key}'")
            
        except Exception as e:
            self.log(f"Error handling key press: {e}")
            
    def start(self):
        """Khởi động client"""
        if not self.connect():
            return False
            
        # Start threads
        stream_thread = threading.Thread(target=self.stream_screen, daemon=True)
        command_thread = threading.Thread(target=self.handle_commands, daemon=True)
        
        stream_thread.start()
        command_thread.start()
        
        self.log("Streamer client started successfully")
        self.log("Press Ctrl+C to stop")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.log("Interrupted by user")
            
        self.stop()
        return True
        
    def stop(self):
        """Dừng client"""
        self.running = False
        self.streaming = False
        
        if self.tcp_socket:
            try:
                self.tcp_socket.close()
            except:
                pass
                
        if self.udp_socket:
            try:
                self.udp_socket.close()
            except:
                pass
                
        self.log("Streamer client stopped")


def main():
    print("="*60)
    print("REMOTE DESKTOP CONTROL - CLIENT B (STREAMER)")
    print("Thành viên 3: Nguyễn Đình Tuấn (B22DCCN759)")
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
    client = StreamerClient(server_ip, tcp_port=5555, udp_port=5556)
    
    # Chạy
    client.start()


if __name__ == "__main__":
    main()
