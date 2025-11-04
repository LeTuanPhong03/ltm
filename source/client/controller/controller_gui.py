"""
Remote Desktop Control - Controller GUI (Modern UI)
Thành viên 2: Phạm Hồng Quang (B22DCCN652)

Giao diện GUI hiện đại để điều khiển máy từ xa
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import socket
import json
import time
from datetime import datetime
from controller_client import ControllerClient

try:
    from PIL import Image, ImageTk
    import io
except ImportError:
    Image = None
    ImageTk = None


class ModernButton(tk.Canvas):
    """Custom modern button with hover effects"""
    def __init__(self, parent, text, command, bg_color="#0078D4", hover_color="#005A9E", 
                 text_color="white", width=120, height=40, **kwargs):
        super().__init__(parent, width=width, height=height, bg=parent['bg'], 
                        highlightthickness=0, **kwargs)
        
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.command = command
        self.text = text
        self._enabled = True
        
        self.rect = self.create_rectangle(2, 2, width-2, height-2, 
                                         fill=bg_color, outline="", width=0)
        self.text_id = self.create_text(width//2, height//2, text=text, 
                                       fill=text_color, font=("Segoe UI", 10, "bold"))
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        
    def on_enter(self, e):
        if self._enabled:
            self.itemconfig(self.rect, fill=self.hover_color)
        
    def on_leave(self, e):
        if self._enabled:
            self.itemconfig(self.rect, fill=self.bg_color)
        
    def on_click(self, e):
        if self._enabled and self.command:
            self.command()
    
    def set_state(self, state):
        if state == "disabled":
            self._enabled = False
            self.itemconfig(self.rect, fill="#4a4a4a")
            self.itemconfig(self.text_id, fill="#8a8a8a")
        else:
            self._enabled = True
            self.itemconfig(self.rect, fill=self.bg_color)
            self.itemconfig(self.text_id, fill=self.text_color)


class ControllerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Remote Desktop Control - Controller")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e1e')
        self.root.resizable(True, True)
        
        # Modern color scheme
        self.colors = {
            'bg_dark': '#1e1e1e',
            'bg_medium': '#252526',
            'bg_light': '#2d2d30',
            'accent': '#0078D4',
            'accent_hover': '#005A9E',
            'success': '#107C10',
            'danger': '#E81123',
            'text_primary': '#ffffff',
            'text_secondary': '#cccccc',
            'border': '#3e3e42'
        }
        
        self.client = None
        self.connected = False
        self.screen_label = None
        self.last_image = None
        self.remote_width = 1920
        self.remote_height = 1080
        
        # Statistics
        self.frames_received = 0
        self.commands_sent = 0
        self.start_time = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Tạo giao diện hiện đại"""
        # Top Bar
        top_bar = tk.Frame(self.root, bg=self.colors['bg_medium'], height=70)
        top_bar.pack(fill=tk.X, padx=0, pady=0)
        top_bar.pack_propagate(False)
        
        # Logo and Title
        title_frame = tk.Frame(top_bar, bg=self.colors['bg_medium'])
        title_frame.pack(side=tk.LEFT, padx=20, pady=15)
        
        tk.Label(
            title_frame,
            text="🖥️",
            font=("Segoe UI", 24),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_primary']
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(
            title_frame,
            text="Remote Desktop Controller",
            font=("Segoe UI", 16, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_primary']
        ).pack(side=tk.LEFT)
        
        # Status indicator
        self.status_frame = tk.Frame(top_bar, bg=self.colors['bg_medium'])
        self.status_frame.pack(side=tk.RIGHT, padx=20)
        
        self.status_dot = tk.Canvas(self.status_frame, width=12, height=12, 
                                   bg=self.colors['bg_medium'], highlightthickness=0)
        self.status_dot.pack(side=tk.LEFT, padx=(0, 8))
        self.status_circle = self.status_dot.create_oval(2, 2, 10, 10, fill="#666666", outline="")
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Disconnected",
            font=("Segoe UI", 10),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_secondary']
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Main Content
        content_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Left Panel - Connection & Controls
        left_panel = tk.Frame(content_frame, bg=self.colors['bg_light'], width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        left_panel.pack_propagate(False)
        
        # Connection Section
        conn_label = tk.Label(
            left_panel,
            text="🔌 SERVER CONNECTION",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg_light'],
            fg=self.colors['text_primary'],
            anchor="w"
        )
        conn_label.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        # Server IP
        tk.Label(
            left_panel,
            text="Server IP Address:",
            font=("Segoe UI", 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text_secondary'],
            anchor="w"
        ).pack(fill=tk.X, padx=15, pady=(5, 2))
        
        ip_frame = tk.Frame(left_panel, bg=self.colors['bg_medium'])
        ip_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        self.ip_entry = tk.Entry(
            ip_frame,
            font=("Segoe UI", 11),
            bg=self.colors['bg_dark'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            relief=tk.FLAT,
            bd=0
        )
        self.ip_entry.pack(fill=tk.X, padx=2, pady=2, ipady=8)
        self.ip_entry.insert(0, "localhost")
        
        # Session ID
        tk.Label(
            left_panel,
            text="Session ID:",
            font=("Segoe UI", 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text_secondary'],
            anchor="w"
        ).pack(fill=tk.X, padx=15, pady=(5, 2))
        
        session_frame = tk.Frame(left_panel, bg=self.colors['bg_medium'])
        session_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        self.session_entry = tk.Entry(
            session_frame,
            font=("Segoe UI", 11),
            bg=self.colors['bg_dark'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            relief=tk.FLAT,
            bd=0
        )
        self.session_entry.pack(fill=tk.X, padx=2, pady=2, ipady=8)
        
        # Password
        tk.Label(
            left_panel,
            text="Password:",
            font=("Segoe UI", 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text_secondary'],
            anchor="w"
        ).pack(fill=tk.X, padx=15, pady=(5, 2))
        
        password_frame = tk.Frame(left_panel, bg=self.colors['bg_medium'])
        password_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.password_entry = tk.Entry(
            password_frame,
            font=("Segoe UI", 11),
            bg=self.colors['bg_dark'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            relief=tk.FLAT,
            bd=0,
            show="●"
        )
        self.password_entry.pack(fill=tk.X, padx=2, pady=2, ipady=8)
        
        # Connect Button
        self.connect_btn = ModernButton(
            left_panel,
            "🔌 CONNECT",
            self.toggle_connection,
            bg_color=self.colors['accent'],
            hover_color=self.colors['accent_hover'],
            width=270,
            height=45
        )
        self.connect_btn.pack(padx=15, pady=(0, 20))
        
        # Separator
        tk.Frame(left_panel, bg=self.colors['border'], height=1).pack(fill=tk.X, padx=15, pady=10)
        
        # Statistics Section
        stats_label = tk.Label(
            left_panel,
            text="📊 STATISTICS",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg_light'],
            fg=self.colors['text_primary'],
            anchor="w"
        )
        stats_label.pack(fill=tk.X, padx=15, pady=(10, 10))
        
        # Stats Display
        stats_container = tk.Frame(left_panel, bg=self.colors['bg_light'])
        stats_container.pack(fill=tk.X, padx=15)
        
        self.stats_labels = {}
        stats_info = [
            ("Frames Received:", "frames"),
            ("Commands Sent:", "commands"),
            ("Connection Time:", "time"),
            ("Frame Rate:", "fps")
        ]
        
        for label_text, key in stats_info:
            stat_frame = tk.Frame(stats_container, bg=self.colors['bg_light'])
            stat_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(
                stat_frame,
                text=label_text,
                font=("Segoe UI", 9),
                bg=self.colors['bg_light'],
                fg=self.colors['text_secondary'],
                anchor="w"
            ).pack(side=tk.LEFT)
            
            value_label = tk.Label(
                stat_frame,
                text="0" if key != "time" else "00:00:00",
                font=("Segoe UI", 9, "bold"),
                bg=self.colors['bg_light'],
                fg=self.colors['accent'],
                anchor="e"
            )
            value_label.pack(side=tk.RIGHT)
            self.stats_labels[key] = value_label
        
        # Separator
        tk.Frame(left_panel, bg=self.colors['border'], height=1).pack(fill=tk.X, padx=15, pady=15)
        
        # Controls Section
        controls_label = tk.Label(
            left_panel,
            text="⚙️ CONTROLS",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg_light'],
            fg=self.colors['text_primary'],
            anchor="w"
        )
        controls_label.pack(fill=tk.X, padx=15, pady=(5, 10))
        
        # Control buttons - Single toggle button
        self.toggle_stream_btn = ModernButton(
            left_panel,
            "⏸️ PAUSE",
            self.toggle_streaming,
            bg_color="#666666",
            hover_color="#555555",
            width=270,
            height=40
        )
        self.toggle_stream_btn.pack(padx=15, pady=5)
        self.toggle_stream_btn.set_state("disabled")
        
        # Track streaming state
        self.is_streaming = True
        
        # Right Panel - Screen Display
        right_panel = tk.Frame(content_frame, bg=self.colors['bg_light'])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Screen Header
        screen_header = tk.Frame(right_panel, bg=self.colors['bg_medium'], height=45)
        screen_header.pack(fill=tk.X)
        screen_header.pack_propagate(False)
        
        tk.Label(
            screen_header,
            text="🖼️ Remote Screen",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_primary']
        ).pack(side=tk.LEFT, padx=15, pady=10)
        
        self.resolution_label = tk.Label(
            screen_header,
            text="No signal",
            font=("Segoe UI", 9),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_secondary']
        )
        self.resolution_label.pack(side=tk.RIGHT, padx=15)
        
        # Screen Canvas (thay Label để tránh nháy)
        canvas_frame = tk.Frame(right_panel, bg=self.colors['bg_dark'])
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Canvas với double buffering
        self.canvas = tk.Canvas(
            canvas_frame,
            bg='#000000',
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder
        self.placeholder_id = self.canvas.create_text(
            400, 300,
            text="Connect to a server to view remote screen",
            font=("Segoe UI", 12),
            fill=self.colors['text_secondary'],
            tags="placeholder"
        )
        
        # Image item for streaming
        self.canvas_image_id = None
        
        # Bind mouse and keyboard events
        self.canvas.bind("<Button-1>", self.on_canvas_left_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)
        self.canvas.bind("<KeyPress>", self.on_canvas_key_press)
        self.canvas.focus_set()
        
        # Bottom Bar
        bottom_bar = tk.Frame(self.root, bg=self.colors['bg_medium'], height=30)
        bottom_bar.pack(fill=tk.X)
        bottom_bar.pack_propagate(False)
        
        self.footer_label = tk.Label(
            bottom_bar,
            text="Nhóm 12 - Lê Tuấn Phong (B22DCCN615) | Phạm Hồng Quang (B22DCCN652) | Trần Đức Mạnh (B22DCCN544)",
            font=("Segoe UI", 8),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_secondary']
        )
        self.footer_label.pack(pady=5)
        
    def update_status(self, connected):
        """Update connection status indicator"""
        if connected:
            self.status_dot.itemconfig(self.status_circle, fill=self.colors['success'])
            self.status_label.config(text="Connected", fg=self.colors['success'])
        else:
            self.status_dot.itemconfig(self.status_circle, fill="#666666")
            self.status_label.config(text="Disconnected", fg=self.colors['text_secondary'])
    
    def toggle_connection(self):
        """Connect or disconnect from server"""
        if not self.connected:
            self.connect()
        else:
            self.disconnect()
    
    def connect(self):
        """Connect to server with authentication"""
        server_ip = self.ip_entry.get().strip()
        session_id = self.session_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not server_ip:
            messagebox.showerror("Error", "Please enter server IP address")
            return
        
        if not session_id or not password:
            messagebox.showerror("Error", "Please enter Session ID and Password")
            return
        
        try:
            self.client = ControllerClient(server_ip)
            if not self.client.connect(session_id, password):
                messagebox.showerror("Authentication Failed", 
                                   "Invalid Session ID or Password.\nPlease check your credentials.")
                return
            
            self.connected = True
            self.start_time = time.time()
            
            # Update UI
            self.update_status(True)
            self.connect_btn.itemconfig(self.connect_btn.text_id, text="🔌 DISCONNECT")
            self.connect_btn.bg_color = self.colors['danger']
            self.connect_btn.hover_color = "#c50f1f"
            self.connect_btn.itemconfig(self.connect_btn.rect, fill=self.colors['danger'])
            self.ip_entry.config(state='disabled')
            self.session_entry.config(state='disabled')
            self.password_entry.config(state='disabled')
            self.toggle_stream_btn.set_state("normal")  # Enable toggle button
            self.is_streaming = True  # Initially streaming
            self.canvas.delete("placeholder")
            
            # Start receiving frames - start the receiver thread in client
            threading.Thread(target=self.client.receive_screen_data, daemon=True).start()
            # Start display thread in GUI
            threading.Thread(target=self.receive_frames, daemon=True).start()
            threading.Thread(target=self.update_statistics, daemon=True).start()
            
            messagebox.showinfo("Success", f"Connected to {server_ip}")
            
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
    
    def disconnect(self):
        """Disconnect from server"""
        if self.client:
            self.client.disconnect()
            self.client = None
        
        self.connected = False
        self.update_status(False)
        self.connect_btn.itemconfig(self.connect_btn.text_id, text="🔌 CONNECT")
        self.connect_btn.bg_color = self.colors['accent']
        self.connect_btn.hover_color = self.colors['accent_hover']
        self.connect_btn.itemconfig(self.connect_btn.rect, fill=self.colors['accent'])
        self.ip_entry.config(state='normal')
        self.session_entry.config(state='normal')
        self.password_entry.config(state='normal')
        self.toggle_stream_btn.set_state("disabled")  # Disable toggle button
        self.is_streaming = True  # Reset state
        
        # Reset canvas
        self.canvas.delete("all")
        self.placeholder_id = self.canvas.create_text(
            400, 300,
            text="Connect to a server to view remote screen",
            font=("Segoe UI", 12),
            fill=self.colors['text_secondary'],
            tags="placeholder"
        )
        self.canvas_image_id = None
        
        self.resolution_label.config(text="No signal")
    
    def receive_frames(self):
        """Receive and display frames - PROPER THREAD-SAFE VERSION"""
        last_update = 0
        frame_buffer = None
        pending_update = False
        
        while self.connected and self.client:
            try:
                # Read screen_data from client (which is updated by receive_screen_data thread)
                if hasattr(self.client, 'screen_data') and self.client.screen_data and Image:
                    current_time = time.time()
                    # Throttle updates to 15 FPS (mượt hơn nhưng vẫn không nháy)
                    if current_time - last_update >= 0.066 and not pending_update:
                        frame_data = self.client.screen_data
                        
                        # Only process if actually new data
                        if frame_data != frame_buffer:
                            try:
                                data_copy = bytes(frame_data)
                                image = Image.open(io.BytesIO(data_copy))
                                # CRITICAL FIX: Schedule update in main thread with flag to prevent queue buildup
                                pending_update = True
                                def update_wrapper(img=image):
                                    nonlocal pending_update
                                    self.display_frame(img)
                                    pending_update = False
                                self.root.after(0, update_wrapper)
                                self.frames_received += 1
                                last_update = current_time
                                frame_buffer = frame_data
                            except:
                                pending_update = False
                                
                time.sleep(0.03)  # Check rate - nhanh hơn để catch frames kịp
            except Exception as e:
                # Silent error, just continue
                time.sleep(0.1)
                continue
    
    def display_frame(self, image):
        """Display frame on canvas với proper buffering (NO FLICKER)"""
        try:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width < 10 or canvas_height < 10:
                return
            
            img_width, img_height = image.size
            self.remote_width = img_width
            self.remote_height = img_height
            
            # Update resolution display
            if not hasattr(self, '_last_resolution') or self._last_resolution != (img_width, img_height):
                self.resolution_label.config(
                    text=f"{img_width} × {img_height}",
                    fg=self.colors['accent']
                )
                self._last_resolution = (img_width, img_height)
            
            # Calculate scaling
            scale_w = canvas_width / img_width
            scale_h = canvas_height / img_height
            scale = min(scale_w, scale_h)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Resize image với LANCZOS quality
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(resized_image)
            
            # Keep reference to prevent garbage collection
            self.last_image = photo
            
            # Calculate center position
            x = canvas_width // 2
            y = canvas_height // 2
            
            # ATOMIC UPDATE - no flicker!
            if self.canvas_image_id is None:
                # First time - create image
                self.canvas_image_id = self.canvas.create_image(
                    x, y, 
                    image=photo, 
                    anchor=tk.CENTER
                )
            else:
                # Update existing image in single atomic operation
                self.canvas.itemconfig(self.canvas_image_id, image=photo)
                # Only update position if changed
                current_coords = self.canvas.coords(self.canvas_image_id)
                if not current_coords or current_coords[0] != x or current_coords[1] != y:
                    self.canvas.coords(self.canvas_image_id, x, y)
            
        except Exception as e:
            pass
    
    def update_statistics(self):
        """Update statistics display"""
        while self.connected:
            try:
                # Update frame count
                self.stats_labels['frames'].config(text=str(self.frames_received))
                self.stats_labels['commands'].config(text=str(self.commands_sent))
                
                # Update connection time
                if self.start_time:
                    elapsed = int(time.time() - self.start_time)
                    hours = elapsed // 3600
                    minutes = (elapsed % 3600) // 60
                    seconds = elapsed % 60
                    self.stats_labels['time'].config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
                
                # Calculate FPS (approximate)
                if self.start_time:
                    elapsed = time.time() - self.start_time
                    if elapsed > 0:
                        fps = self.frames_received / elapsed
                        self.stats_labels['fps'].config(text=f"{fps:.1f} fps")
                
                time.sleep(1)
            except:
                break
    
    def on_canvas_left_click(self, event):
        """Handle left mouse click"""
        if not self.connected or not self.client:
            return
        
        x, y = self.canvas_to_remote_coords(event.x, event.y)
        if x is not None and y is not None:
            self.client.mouse_click(x, y, "left")
            self.commands_sent += 1
            self.show_click_feedback(event.x, event.y, "left")
    
    def on_canvas_right_click(self, event):
        """Handle right mouse click"""
        if not self.connected or not self.client:
            return
        
        x, y = self.canvas_to_remote_coords(event.x, event.y)
        if x is not None and y is not None:
            self.client.mouse_click(x, y, "right")
            self.commands_sent += 1
            self.show_click_feedback(event.x, event.y, "right")
    
    def on_canvas_key_press(self, event):
        """Handle keyboard input"""
        if not self.connected or not self.client:
            return
        
        key = event.keysym
        self.client.key_press(key)
        self.commands_sent += 1
    
    def canvas_to_remote_coords(self, canvas_x, canvas_y):
        """Convert canvas coordinates to remote screen coordinates"""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        scale_w = canvas_width / self.remote_width
        scale_h = canvas_height / self.remote_height
        scale = min(scale_w, scale_h)
        
        display_width = int(self.remote_width * scale)
        display_height = int(self.remote_height * scale)
        
        offset_x = (canvas_width - display_width) // 2
        offset_y = (canvas_height - display_height) // 2
        
        if (canvas_x < offset_x or canvas_x > offset_x + display_width or
            canvas_y < offset_y or canvas_y > offset_y + display_height):
            return None, None
        
        relative_x = (canvas_x - offset_x) / display_width
        relative_y = (canvas_y - offset_y) / display_height
        
        remote_x = int(relative_x * self.remote_width)
        remote_y = int(relative_y * self.remote_height)
        
        return remote_x, remote_y
    
    def show_click_feedback(self, x, y, button):
        """Show visual feedback for click - disabled cho Label"""
        pass  # Không dùng visual feedback với Label
    
    def toggle_streaming(self):
        """Toggle between pause and resume streaming"""
        if not self.client or not self.connected:
            return
        
        if self.is_streaming:
            # Currently streaming → PAUSE it
            self.client.pause_stream()
            self.commands_sent += 1
            self.is_streaming = False
            
            # Update button to show RESUME
            self.toggle_stream_btn.itemconfig(self.toggle_stream_btn.text_id, text="▶️ RESUME")
            self.toggle_stream_btn.bg_color = self.colors['success']
            self.toggle_stream_btn.hover_color = "#0e6b0e"
            self.toggle_stream_btn.itemconfig(self.toggle_stream_btn.rect, fill=self.colors['success'])
            
            # Visual feedback: Add PAUSED text on canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Remove old pause text if exists
            if hasattr(self, 'pause_text_id'):
                self.canvas.delete(self.pause_text_id)
            
            # Add large PAUSED text in center
            self.pause_text_id = self.canvas.create_text(
                canvas_width // 2, canvas_height // 2,
                text="⏸️ STREAM PAUSED",
                font=("Segoe UI", 48, "bold"),
                fill=self.colors['danger'],
                tags='pause_text'
            )
            
            # Add instruction text below
            self.pause_instruction_id = self.canvas.create_text(
                canvas_width // 2, canvas_height // 2 + 60,
                text="Click RESUME button to continue",
                font=("Segoe UI", 16),
                fill=self.colors['accent'],
                tags='pause_text'
            )
            
            self.resolution_label.config(text="Stream Paused", fg=self.colors['danger'])
            
        else:
            # Currently paused → RESUME it
            self.client.continue_stream()
            self.commands_sent += 1
            self.is_streaming = True
            
            # Update button to show PAUSE
            self.toggle_stream_btn.itemconfig(self.toggle_stream_btn.text_id, text="⏸️ PAUSE")
            self.toggle_stream_btn.bg_color = "#666666"
            self.toggle_stream_btn.hover_color = "#555555"
            self.toggle_stream_btn.itemconfig(self.toggle_stream_btn.rect, fill="#666666")
            
            # Remove pause text
            if hasattr(self, 'pause_text_id'):
                self.canvas.delete(self.pause_text_id)
                delattr(self, 'pause_text_id')
            
            if hasattr(self, 'pause_instruction_id'):
                self.canvas.delete(self.pause_instruction_id)
                delattr(self, 'pause_instruction_id')
            
            # Restore resolution label
            if hasattr(self, '_last_resolution'):
                w, h = self._last_resolution
                self.resolution_label.config(text=f"{w} × {h}", fg=self.colors['accent'])


def main():
    root = tk.Tk()
    app = ControllerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
