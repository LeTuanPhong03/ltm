# BÀI TẬP LỚN: LẬP TRÌNH MẠNG  

## [Tên dự án của nhóm]

> 📘 *Mẫu README này là khung hướng dẫn. Sinh viên chỉ cần điền thông tin của nhóm và nội dung dự án theo từng mục.*

---

## 🧑‍💻 THÔNG TIN NHÓM

| STT | Họ và Tên | MSSV | Email | Đóng góp |
|-----|-----------|------|-------|----------|
| 1 | Lê Tuấn Phong | B22DCCN615 | tuanphong322003@gmail.com | Server Developer - Xử lý TCP/UDP, log kết nối |
| 2 | Phạm Hồng Quang | B22DCCN652 | hongquang02082004@gmail.com | Client A (Controller) - Gửi lệnh điều khiển qua TCP |
| 3 | Nguyễn Đình Tuấn | B22DCCN759 | dinhtuan27022004@gmail.com | Client B (Streamer) - Gửi dữ liệu màn hình qua UDP |

**Tên nhóm:** Nhóm 12 – Lập trình mạng  
**Chủ đề đã đăng ký:** Hệ thống điều khiển từ xa qua mạng nội bộ (Remote Desktop Control)

---

## 🧠 MÔ TẢ HỆ THỐNG

Hệ thống **Remote Desktop Control** cho phép điều khiển máy tính từ xa qua mạng nội bộ thông qua server trung gian.

### Kiến trúc hệ thống:

- **Client A (Controller)**: Máy tính điều khiển, gửi lệnh bàn phím/chuột đến server qua **TCP**
- **Server (Trung gian)**: Nhận lệnh từ Client A, chuyển tiếp đến Client B, và nhận dữ liệu màn hình từ Client B qua **UDP**
- **Client B (Streamer)**: Máy tính bị điều khiển, gửi ảnh màn hình qua UDP và thực thi lệnh nhận được

### Luồng hoạt động:

1. **Client A** kết nối đến Server qua TCP và gửi lệnh điều khiển (mouse click, keyboard, pause, continue)
2. **Server** log thông tin kết nối (IP, port, client ID) và chuyển tiếp lệnh đến Client B
3. **Client B** capture màn hình, gửi frames qua UDP đến Server, sau đó chuyển đến Client A
4. **Client B** thực thi các lệnh điều khiển nhận được từ Server (di chuyển chuột, click, nhấn phím)
5. **Client A** hiển thị màn hình real-time và cho phép điều khiển bằng cách:
   - **Click trực tiếp** lên màn hình hiển thị
   - **Nhấn phím** trên bàn phím
   - **Sử dụng các nút tắt** (Ctrl+C, Ctrl+V, Enter...)

### Tính năng điều khiển:

✅ **Chuột:**
- Click trái/phải trực tiếp trên màn hình hiển thị
- Click vào icon → Mở ứng dụng trên máy remote
- Click vào button → Button được nhấn trên máy remote
- Click vào text field → Cursor xuất hiện trên máy remote
- Double click
- Di chuyển con trỏ (track mouse position)

✅ **Bàn phím:**
- Nhập text tự do → Text xuất hiện trên máy remote
- Gõ "google.com" → Text hiển thị trong browser remote
- Phím tắt (Ctrl+C, Ctrl+V, Enter, ESC...)
- Tất cả các phím đặc biệt (Alt, Shift, Tab, F1-F12...)

✅ **Hiệu ứng trực quan:**
- Vòng tròn đỏ khi click trái
- Vòng tròn vàng khi click phải  
- Vòng tròn xanh khi double click

✅ **Use Cases thực tế:**
- Mở Edge/Chrome browser trên máy remote
- Điền form, nhập liệu từ xa
- Chơi game đơn giản
- Quản trị hệ thống từ xa
- Hỗ trợ kỹ thuật, training từ xa

**Cấu trúc logic tổng quát:**
```
Client A (Controller) <--TCP--> Server <--UDP--> Client B (Streamer)
      [Send Commands]         [Relay]         [Send Screen + Execute]
      [View Screen]                           [Execute Mouse/Keyboard]
        Click ───────────────────────────────────> pyautogui.click()
        Type ────────────────────────────────────> pyautogui.press()
        View <────────────────────────────────── Screen Capture
```

**Sơ đồ hệ thống:**

![System Diagram](./statics/diagram.png)

---

## ⚙️ CÔNG NGHỆ SỬ DỤNG

| Thành phần | Công nghệ | Ghi chú |
|------------|-----------|---------|
| Server | Python 3.11 + Socket | TCP/UDP Server, logging kết nối |
| Client A (Controller) | Python 3.11 + Socket | Gửi lệnh điều khiển qua TCP |
| Client B (Streamer) | Python 3.11 + Socket + PIL/mss | Capture màn hình, gửi qua UDP |
| Thư viện bổ sung | pyautogui, Pillow, mss | Điều khiển chuột/bàn phím, xử lý ảnh |
| Giao thức | TCP (Commands), UDP (Media) | Đảm bảo độ tin cậy và tốc độ |

---

## 🚀 HƯỚNG DẪN CHẠY DỰ ÁN

### 0. Cài đặt môi trường
```bash
# Cài đặt Python 3.11+
python --version

# Cài đặt thư viện cần thiết
pip install -r requirements.txt
```

### 1. Clone repository
```bash
git clone https://github.com/jnp2018/mid-project-615652759
cd BTL/mid-project-615652759
```

### 2. Chạy Server (Thành viên 1)
```bash
cd source/server
python server.py
# Server sẽ lắng nghe:
# - TCP port 5555 (nhận lệnh từ Client A)
# - UDP port 5556 (nhận media từ Client B)
```

### 3. Chạy Client B - Streamer (Thành viên 3) - GÓI GUI
```bash
cd source/client/streamer
python streamer_gui.py
# Giao diện sẽ hiển thị:
# - Your Computer ID (IP local)
# - Nhập Server IP và click "Start Sharing"
# - Màn hình sẽ được stream đến server
```

**Hoặc chạy CLI mode:**
```bash
python streamer_client.py
# Nhập IP server và bắt đầu stream màn hình
```

### 4. Chạy Client A - Controller (Thành viên 2) - GUI
```bash
cd source/client/controller
python controller_gui.py
# Giao diện sẽ hiển thị:
# - Nhập Server IP 
# - Click "Connect"
# - Xem màn hình từ xa và điều khiển
```

**Hoặc chạy CLI mode:**
```bash
python controller_client.py
# Nhập IP server và gửi lệnh điều khiển
```

### 5. Kiểm thử nhanh
```bash
# Test kết nối TCP
python -c "import socket; s=socket.socket(); s.connect(('localhost',5555)); print('TCP OK')"

# Test kết nối UDP
python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.sendto(b'test',('localhost',5556)); print('UDP OK')"
```

---

## 🔗 GIAO TIẾP (GIAO THỨC SỬ DỤNG)

### TCP - Lệnh điều khiển (Client A → Server → Client B)

| Lệnh | Payload | Mô tả |
|------|---------|-------|
| `MOUSE_CLICK` | `{"x": 100, "y": 200, "button": "left"}` | Click chuột tại vị trí (x,y) |
| `MOUSE_MOVE` | `{"x": 150, "y": 250}` | Di chuyển chuột |
| `KEY_PRESS` | `{"key": "enter"}` | Nhấn phím |
| `PAUSE` | `{}` | Tạm dừng stream |
| `CONTINUE` | `{}` | Tiếp tục stream |
| `DISCONNECT` | `{}` | Ngắt kết nối |

### UDP - Truyền dữ liệu màn hình (Client B → Server → Client A)

| Loại | Format | Mô tả |
|------|--------|-------|
| Screen Frame | JPEG bytes | Ảnh màn hình nén JPEG (800x600) |
| Frame Header | `{frame_id, timestamp, size}` | Metadata của frame |

### Log Server (IP, Port, Client ID)

Server ghi log mỗi khi có kết nối:
```
[2025-11-02 10:30:45] TCP Client A connected: 192.168.1.100:54321
[2025-11-02 10:30:47] UDP Client B connected: 192.168.1.101:54322
```

---

## 📊 KẾT QUẢ THỰC NGHIỆM

### Giao diện GUI

**Controller (Client A) - Điều khiển từ xa:**
```
┌─────────────────────────────────────────────────────────┐
│  🖥️ Remote Desktop Controller                          │
├─────────────────────────────────────────────────────────┤
│ 🔗 Connection                                           │
│ Server IP: [192.168.1.100]  [🔌 Connect] [❌ Disconnect]│
│ Status: 🟢 Connected                                    │
├─────────────────────────────────────────────────────────┤
│ 🎮 Remote Control                                       │
│ ┌─────────────────────┐  Quick Actions:                │
│ │  🖱️ CLICK ĐỂ        │  [🖱️ Mouse Test]              │
│ │  ĐIỀU KHIỂN!        │  [⌨️ Send Enter]              │
│ │                     │  [⌨️ Ctrl+C]                  │
│ │  Remote Screen      │  [⌨️ Ctrl+V]                  │
│ │  (Live View)        │  [⏸️ Pause Stream]            │
│ │  ⌨️ GÕ PHÍM ĐỂ      │  [▶️ Resume Stream]           │
│ │  NHẬP TEXT          │  [📊 Ping Test]               │
│ └─────────────────────┘                                 │
├─────────────────────────────────────────────────────────┤
│ 📋 Activity Log                                         │
│ [21:45:00] Connected successfully!                      │
│ [21:45:05] 🖱️ Left click at (320, 240)                │
│ [21:45:07] ⌨️ Key press: enter                         │
│ [21:45:10] Ping: 15.24ms                               │
└─────────────────────────────────────────────────────────┘

💡 CÁCH ĐIỀU KHIỂN:
• Click trực tiếp lên màn hình → Chuột trên máy remote sẽ click
• Gõ phím bất kỳ → Phím được gửi đến máy remote
• Click phải → Menu context trên máy remote
• Double click → Double click trên máy remote
```

**Streamer (Client B) - Cho phép điều khiển:**
```
┌─────────────────────────────────────────────────────────┐
│  🖥️ Allow Remote Control                               │
├─────────────────────────────────────────────────────────┤
│ 📍 Your Computer ID                                     │
│ Share this with the person controlling your computer:   │
│ ┌───────────────────────────────────────────────────┐  │
│ │           192.168.1.100                           │  │
│ └───────────────────────────────────────────────────┘  │
│                    [📋 Copy ID]                         │
├─────────────────────────────────────────────────────────┤
│ 🔗 Server Connection                                    │
│ Server IP: [localhost]  [🟢 Start] [🔴 Stop]           │
│ Status: 🟢 Sharing Active                               │
├─────────────────────────────────────────────────────────┤
│ 📊 Statistics                                           │
│ Frames Sent: 240    Commands Received: 5               │
├─────────────────────────────────────────────────────────┤
│ 📋 Activity Log                                         │
│ [21:45:00] Connected successfully!                      │
│ [21:45:30] Streamed 30 frames, size: 35KB             │
│ [21:45:35] Received command: MOUSE_CLICK               │
└─────────────────────────────────────────────────────────┘
```

### Kết quả test
- ✅ **Kết nối**: TCP và UDP hoạt động ổn định
- ✅ **Stream**: ~10 FPS, JPEG 640x480, ~35KB/frame
- ✅ **Latency**: ~15-30ms trên LAN
- ✅ **Commands**: Mouse, keyboard được thực thi chính xác
- ✅ **GUI**: Giao diện thân thiện, dễ sử dụng

---

## 🧩 CẤU TRÚC DỰ ÁN
```
assignment-network-project/
├── README.md
├── INSTRUCTION.md
├── statics/
│   ├── diagram.png
│   └── dataset_sample.csv
└── source/
    ├── .gitignore
    ├── client/
    │   ├── README.md
    │   └── (client source files...)
    ├── server/
    │   ├── README.md
    │   └── (server source files...)
    └── (các module khác nếu có)
```

---

## 🧩 HƯỚNG PHÁT TRIỂN THÊM

- [ ] Thêm mã hóa AES cho dữ liệu truyền tải
- [ ] Hỗ trợ nhiều client controller đồng thời
- [ ] Tối ưu nén ảnh với H.264 codec
- [ ] Thêm giao diện GUI cho client controller
- [ ] Hỗ trợ truyền âm thanh
- [ ] Triển khai NAT traversal để kết nối qua Internet

---

## 📝 GHI CHÚ

- Repo tuân thủ đúng cấu trúc đã hướng dẫn trong `INSTRUCTION.md`.
- Đảm bảo test kỹ trước khi submit.

---

## 📚 TÀI LIỆU THAM KHẢO

> (Nếu có) Liệt kê các tài liệu, API docs, hoặc nguồn tham khảo đã sử dụng.