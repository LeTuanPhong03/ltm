"""
Remote Desktop Control - Streamer GUI (Modern UI)
Thành viên 3: Trần Đức Mạnh (B22DCCN544)

Giao diện GUI hiện đại để chia sẻ màn hình và cho phép điều khiển
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import socket
from datetime import datetime
from streamer_client import StreamerClient


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
    
    def update_text(self, new_text):
        self.text = new_text
        self.itemconfig(self.text_id, text=new_text)


class StreamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Remote Desktop Control - Allow Remote Control")
        self.root.geometry("650x750")
        self.root.configure(bg='#1e1e1e')
        self.root.resizable(False, False)
        
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
        self.sharing = False
        
        # Statistics
        self.frames_sent = 0
        self.commands_received = 0
        self.start_time = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Tạo giao diện hiện đại"""
        # Top Bar
        top_bar = tk.Frame(self.root, bg=self.colors['accent'], height=70)
        top_bar.pack(fill=tk.X, padx=0, pady=0)
        top_bar.pack_propagate(False)
        
        # Logo and Title
        title_frame = tk.Frame(top_bar, bg=self.colors['accent'])
        title_frame.pack(side=tk.LEFT, padx=20, pady=15)
        
        tk.Label(
            title_frame,
            text="📺",
            font=("Segoe UI", 24),
            bg=self.colors['accent'],
            fg=self.colors['text_primary']
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(
            title_frame,
            text="Allow Remote Control",
            font=("Segoe UI", 16, "bold"),
            bg=self.colors['accent'],
            fg=self.colors['text_primary']
        ).pack(side=tk.LEFT)
        
        # Main Content
        content_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Computer ID Section
        id_section = tk.Frame(content_frame, bg=self.colors['bg_light'])
        id_section.pack(fill=tk.X, pady=(0, 15))
        
        # Section Header
        header_frame = tk.Frame(id_section, bg=self.colors['bg_medium'], height=50)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🔑 Your Computer ID",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_primary']
        ).pack(side=tk.LEFT, padx=15, pady=12)
        
        # Info text
        info_frame = tk.Frame(id_section, bg=self.colors['bg_light'])
        info_frame.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        tk.Label(
            info_frame,
            text="Share this information with the person who wants to control your computer:",
            font=("Segoe UI", 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text_secondary'],
            wraplength=550,
            justify=tk.LEFT
        ).pack(anchor='w')
        
        # IP Display
        ip_display_frame = tk.Frame(id_section, bg=self.colors['bg_dark'])
        ip_display_frame.pack(fill=tk.X, padx=20, pady=(5, 10))
        
        self.ip_label = tk.Label(
            ip_display_frame,
            text=self.get_local_ip(),
            font=("Segoe UI", 20, "bold"),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent'],
            pady=15
        )
        self.ip_label.pack()
        
        # Session ID and Password Display
        credentials_frame = tk.Frame(id_section, bg=self.colors['bg_light'])
        credentials_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Session ID row
        session_row = tk.Frame(credentials_frame, bg=self.colors['bg_dark'])
        session_row.pack(fill=tk.X, pady=3)
        
        tk.Label(
            session_row,
            text="Session ID:",
            font=("Segoe UI", 10),
            bg=self.colors['bg_dark'],
            fg=self.colors['text_secondary'],
            width=12,
            anchor='w'
        ).pack(side=tk.LEFT, padx=10)
        
        self.session_id_label = tk.Label(
            session_row,
            text="Not connected",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent']
        )
        self.session_id_label.pack(side=tk.LEFT, padx=5)
        
        # Password row
        password_row = tk.Frame(credentials_frame, bg=self.colors['bg_dark'])
        password_row.pack(fill=tk.X, pady=3)
        
        tk.Label(
            password_row,
            text="Password:",
            font=("Segoe UI", 10),
            bg=self.colors['bg_dark'],
            fg=self.colors['text_secondary'],
            width=12,
            anchor='w'
        ).pack(side=tk.LEFT, padx=10)
        
        self.password_label = tk.Label(
            password_row,
            text="Not connected",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['bg_dark'],
            fg=self.colors['accent']
        )
        self.password_label.pack(side=tk.LEFT, padx=5)
        
        # Copy button
        copy_btn = ModernButton(
            id_section,
            "📋 Copy Credentials",
            self.copy_credentials,
            bg_color=self.colors['bg_medium'],
            hover_color="#3a3a3d",
            width=200,
            height=35
        )
        copy_btn.pack(pady=(5, 15))
        
        # Server Connection Section
        server_section = tk.Frame(content_frame, bg=self.colors['bg_light'])
        server_section.pack(fill=tk.X, pady=(0, 15))
        
        # Section Header
        server_header = tk.Frame(server_section, bg=self.colors['bg_medium'], height=50)
        server_header.pack(fill=tk.X)
        server_header.pack_propagate(False)
        
        tk.Label(
            server_header,
            text="🔗 Server Connection",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_primary']
        ).pack(side=tk.LEFT, padx=15, pady=12)
        
        # Server IP input
        server_input_frame = tk.Frame(server_section, bg=self.colors['bg_light'])
        server_input_frame.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        tk.Label(
            server_input_frame,
            text="Server IP:",
            font=("Segoe UI", 10),
            bg=self.colors['bg_light'],
            fg=self.colors['text_secondary'],
            width=10,
            anchor='w'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ip_entry_frame = tk.Frame(server_input_frame, bg=self.colors['bg_dark'])
        ip_entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.server_ip_entry = tk.Entry(
            ip_entry_frame,
            font=("Segoe UI", 11),
            bg=self.colors['bg_dark'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            relief=tk.FLAT,
            bd=0
        )
        self.server_ip_entry.pack(fill=tk.X, padx=5, pady=5, ipady=5)
        self.server_ip_entry.insert(0, "localhost")
        
        # Start/Stop Button
        button_frame = tk.Frame(server_section, bg=self.colors['bg_light'])
        button_frame.pack(pady=(10, 15))
        
        self.share_btn = ModernButton(
            button_frame,
            "🟢 Start Sharing",
            self.toggle_sharing,
            bg_color=self.colors['success'],
            hover_color="#0e6b0e",
            width=300,
            height=50
        )
        self.share_btn.pack()
        
        # Status indicator
        self.status_frame = tk.Frame(server_section, bg=self.colors['bg_light'])
        self.status_frame.pack(pady=(5, 15))
        
        self.status_dot = tk.Canvas(self.status_frame, width=12, height=12, 
                                   bg=self.colors['bg_light'], highlightthickness=0)
        self.status_dot.pack(side=tk.LEFT, padx=(0, 8))
        self.status_circle = self.status_dot.create_oval(2, 2, 10, 10, fill="#666666", outline="")
        
        self.status_text = tk.Label(
            self.status_frame,
            text="Not Sharing",
            font=("Segoe UI", 10),
            bg=self.colors['bg_light'],
            fg=self.colors['text_secondary']
        )
        self.status_text.pack(side=tk.LEFT)
        
        # Statistics Section
        stats_section = tk.Frame(content_frame, bg=self.colors['bg_light'])
        stats_section.pack(fill=tk.BOTH, expand=True)
        
        # Section Header
        stats_header = tk.Frame(stats_section, bg=self.colors['bg_medium'], height=50)
        stats_header.pack(fill=tk.X)
        stats_header.pack_propagate(False)
        
        tk.Label(
            stats_header,
            text="📊 Statistics",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_primary']
        ).pack(side=tk.LEFT, padx=15, pady=12)
        
        # Stats Display
        stats_container = tk.Frame(stats_section, bg=self.colors['bg_light'])
        stats_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        self.stats_labels = {}
        stats_info = [
            ("Frames Sent:", "frames", "0"),
            ("Commands Received:", "commands", "0"),
            ("Sharing Time:", "time", "00:00:00"),
            ("Data Sent:", "data", "0 MB")
        ]
        
        for label_text, key, default_val in stats_info:
            stat_frame = tk.Frame(stats_container, bg=self.colors['bg_light'])
            stat_frame.pack(fill=tk.X, pady=8)
            
            tk.Label(
                stat_frame,
                text=label_text,
                font=("Segoe UI", 10),
                bg=self.colors['bg_light'],
                fg=self.colors['text_secondary'],
                anchor="w",
                width=18
            ).pack(side=tk.LEFT)
            
            value_label = tk.Label(
                stat_frame,
                text=default_val,
                font=("Segoe UI", 11, "bold"),
                bg=self.colors['bg_light'],
                fg=self.colors['accent'],
                anchor="e"
            )
            value_label.pack(side=tk.RIGHT)
            self.stats_labels[key] = value_label
        
        # Bottom Bar
        bottom_bar = tk.Frame(self.root, bg=self.colors['bg_medium'], height=35)
        bottom_bar.pack(fill=tk.X)
        bottom_bar.pack_propagate(False)
        
        tk.Label(
            bottom_bar,
            text="Nhóm 12 - Lê Tuấn Phong (B22DCCN615) | Phạm Hồng Quang (B22DCCN652) | Trần Đức Mạnh (B22DCCN544)",
            font=("Segoe UI", 8),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_secondary']
        ).pack(pady=8)
    
    def get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "192.168.0.100"
    
    def copy_id(self):
        """Copy ID to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.ip_label.cget("text"))
        messagebox.showinfo("Copied", "Computer ID copied to clipboard!")
    
    def copy_credentials(self):
        """Copy Session ID and Password to clipboard"""
        if self.client and self.sharing:
            credentials = f"Session ID: {self.client.session_id}\nPassword: {self.client.password}"
            self.root.clipboard_clear()
            self.root.clipboard_append(credentials)
            messagebox.showinfo("Copied", "Credentials copied to clipboard!")
        else:
            messagebox.showwarning("Warning", "Please start sharing first to get credentials")
    
    def toggle_sharing(self):
        """Start or stop sharing"""
        if not self.sharing:
            self.start_sharing()
        else:
            self.stop_sharing()
    
    def start_sharing(self):
        """Start screen sharing"""
        server_ip = self.server_ip_entry.get().strip()
        if not server_ip:
            messagebox.showerror("Error", "Please enter server IP address")
            return
        
        try:
            self.client = StreamerClient(server_ip)
            self.client.connect()
            self.sharing = True
            self.start_time = time.time()
            
            # Update credentials display
            self.session_id_label.config(text=self.client.session_id)
            self.password_label.config(text=self.client.password)
            
            # Update UI
            self.share_btn.update_text("🔴 Stop Sharing")
            self.share_btn.bg_color = self.colors['danger']
            self.share_btn.hover_color = "#c50f1f"
            self.share_btn.itemconfig(self.share_btn.rect, fill=self.colors['danger'])
            self.server_ip_entry.config(state='disabled')
            
            self.status_dot.itemconfig(self.status_circle, fill=self.colors['success'])
            self.status_text.config(text="Sharing Active", fg=self.colors['success'])
            
            # Start threads
            threading.Thread(target=self.client.stream_screen, daemon=True).start()
            threading.Thread(target=self.client.handle_commands, daemon=True).start()
            threading.Thread(target=self.update_statistics, daemon=True).start()
            
            messagebox.showinfo("Success", f"Started sharing to {server_ip}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start sharing: {str(e)}")
    
    def stop_sharing(self):
        """Stop screen sharing"""
        if self.client:
            self.client.disconnect()
            self.client = None
        
        self.sharing = False
        
        # Update UI
        self.share_btn.update_text("🟢 Start Sharing")
        self.share_btn.bg_color = self.colors['success']
        self.share_btn.hover_color = "#0e6b0e"
        self.share_btn.itemconfig(self.share_btn.rect, fill=self.colors['success'])
        self.server_ip_entry.config(state='normal')
        
        self.status_dot.itemconfig(self.status_circle, fill="#666666")
        self.status_text.config(text="Not Sharing", fg=self.colors['text_secondary'])
        
        messagebox.showinfo("Stopped", "Screen sharing stopped")
    
    def update_statistics(self):
        """Update statistics display"""
        bytes_sent = 0
        while self.sharing:
            try:
                if self.client:
                    # Update frames and commands
                    self.frames_sent = getattr(self.client, 'frames_sent', 0)
                    self.commands_received = getattr(self.client, 'commands_received', 0)
                    
                    self.stats_labels['frames'].config(text=str(self.frames_sent))
                    self.stats_labels['commands'].config(text=str(self.commands_received))
                    
                    # Update time
                    if self.start_time:
                        elapsed = int(time.time() - self.start_time)
                        hours = elapsed // 3600
                        minutes = (elapsed % 3600) // 60
                        seconds = elapsed % 60
                        self.stats_labels['time'].config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
                    
                    # Estimate data sent (approximately 35KB per frame)
                    bytes_sent = self.frames_sent * 35000
                    mb_sent = bytes_sent / (1024 * 1024)
                    self.stats_labels['data'].config(text=f"{mb_sent:.2f} MB")
                
                time.sleep(1)
            except:
                break


def main():
    root = tk.Tk()
    app = StreamerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
