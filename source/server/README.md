# MODULE SERVER

**Thành viên:** Lê Tuấn Phong (B22DCCN615)

---

## 🎯 MỤC TIÊU

Server chịu trách nhiệm:
- Nhận lệnh điều khiển từ Client A (Controller) qua **TCP** (port 5555)
- Nhận dữ liệu màn hình từ Client B (Streamer) qua **UDP** (port 5556)
- Chuyển tiếp lệnh từ Controller đến Streamer
- Chuyển tiếp dữ liệu màn hình từ Streamer đến Controller
- **Log thông tin kết nối**: IP, Port, Client ID, thời gian kết nối

---

## ⚙️ CÔNG NGHỆ SỬ DỤNG

| Thành phần | Công nghệ |
|------------|-----------|
| Ngôn ngữ | Python 3.11+ |
| Thư viện | socket (built-in), threading, json |
| Giao thức | TCP (lệnh), UDP (media) |

---

## 🚀 HƯỚNG DẪN CHẠY

### Cài đặt
```bash
# Không cần cài thêm thư viện (sử dụng built-in modules)
python --version  # Kiểm tra Python 3.11+
```

### Khởi động server
```bash
cd source/server
python server.py
```

Server sẽ hiển thị:
```
============================================================
REMOTE DESKTOP CONTROL - SERVER
Thành viên 1: Lê Tuấn Phong (B22DCCN615)
============================================================

[2025-11-02 10:30:45] TCP Server started on port 5555
[2025-11-02 10:30:45] UDP Server started on port 5556
[2025-11-02 10:30:45] Server is ready to accept connections
```

### Cấu hình (nếu cần)
- **TCP Port**: Mặc định `5555` (có thể thay đổi trong code)
- **UDP Port**: Mặc định `5556`
- **Binding**: `0.0.0.0` (lắng nghe tất cả network interfaces)

---

## 🔗 KẾT NỐI

### Kết nối TCP (Controller)
- Client A kết nối đến `server_ip:5555`
- Gửi JSON: `{"type": "controller"}`
- Sau đó gửi các lệnh điều khiển

### Kết nối UDP (Streamer)  
- Client B gửi dữ liệu đến `server_ip:5556`
- Format: Raw bytes (JPEG frames)

---

## 📋 LOG FORMAT

Server tự động log:

```
[2025-11-02 10:30:47] TCP Client A (Controller) connected: 192.168.1.100:54321
[2025-11-02 10:30:49] TCP Client B (Streamer) connected: 192.168.1.101:54322
[2025-11-02 10:30:50] UDP Client B (Streamer) sending from: 192.168.1.101:54323
[2025-11-02 10:30:51] Received command from Controller: MOUSE_CLICK
[2025-11-02 10:30:51] Command forwarded to Streamer
```

---

## 📦 CẤU TRÚC
```
server/
├── README.md
└── server.py        # Main server code
```

---

## 🧪 TEST

### Test TCP connection
```bash
# Từ máy khác hoặc localhost
python -c "import socket; s=socket.socket(); s.connect(('SERVER_IP',5555)); print('TCP OK')"
```

### Test UDP connection
```bash
python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.sendto(b'test',('SERVER_IP',5556)); print('UDP OK')"
```

---

## 📊 STATUS MONITOR

Server tự động in trạng thái mỗi 10 giây:

```
============================================================
SERVER STATUS
============================================================
Controller (Client A): 192.168.1.100
  - Port: 54321
  - Connected at: 2025-11-02 10:30:47

Streamer (Client B): 192.168.1.101
  - Port: 54322
  - Connected at: 2025-11-02 10:30:49
============================================================
```

---

## 📝 GHI CHÚ

- Server phải chạy **trước** khi clients kết nối
- Hỗ trợ kết nối lại tự động nếu client disconnect
- Sử dụng `Ctrl+C` để dừng server
- Port mặc định: TCP 5555, UDP 5556