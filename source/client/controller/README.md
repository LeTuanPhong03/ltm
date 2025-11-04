# MODULE CLIENT A - CONTROLLER

**Thành viên:** Phạm Hồng Quang (B22DCCN652)

---

## 🎯 MỤC TIÊU

Client Controller chịu trách nhiệm:
- Kết nối đến server qua **TCP** (port 5555)
- Gửi lệnh điều khiển (mouse click, mouse move, keyboard, pause, continue)
- Nhận và hiển thị màn hình từ Client B (qua server)
- Test độ trễ control (ping test)

---

## ⚙️ CÔNG NGHỆ SỬ DỤNG

| Thành phần | Công nghệ |
|------------|-----------|
| Ngôn ngữ | Python 3.11+ |
| Thư viện | socket, threading, json, Pillow (optional) |
| Giao thức | TCP |

---

## 🚀 HƯỚNG DẪN CHẠY

### Cài đặt
```bash
# Cài đặt thư viện (Pillow optional để hiển thị màn hình)
pip install Pillow

# Hoặc nếu không cần hiển thị màn hình
# Không cần cài gì thêm
```

### Chạy chương trình với GUI (Khuyến nghị ⭐)
```bash
cd source/client/controller
python controller_gui.py
```

**Giao diện GUI giống TeamViewer:**
- 🔗 **Connection Panel**: Nhập Server IP và kết nối
- 🖥️ **Remote Screen**: Hiển thị màn hình máy từ xa real-time
- 🎮 **Control Buttons**: 
  - Test Click: Click chuột tại giữa màn hình
  - Test Key: Nhấn phím Enter
  - Pause/Resume: Điều khiển stream
  - Ping Test: Kiểm tra độ trễ
- 📋 **Activity Log**: Xem log hoạt động

### Chạy CLI mode
```bash
python controller_client.py

# Hoặc chỉ định IP server ngay
python controller_client.py 192.168.1.100
```

### Nhập thông tin
```
Enter server IP address [localhost]: 192.168.1.100
```

---

## 💡 SỬ DỤNG

### Chế độ Interactive

Sau khi kết nối thành công, bạn có thể sử dụng các lệnh sau:

```bash
# Click chuột tại vị trí (x, y)
>>> click 100 200 left

# Di chuyển chuột đến vị trí (x, y)
>>> move 150 250

# Nhấn phím
>>> key enter
>>> key a
>>> key ctrl

# Tạm dừng stream
>>> pause

# Tiếp tục stream
>>> continue

# Test độ trễ
>>> ping

# Thoát
>>> quit
```

### Các lệnh điều khiển

| Lệnh | Cú pháp | Mô tả |
|------|---------|-------|
| `click` | `click <x> <y> [button]` | Click chuột tại (x,y), button: left/right/middle |
| `move` | `move <x> <y>` | Di chuyển chuột đến (x,y) |
| `key` | `key <keyname>` | Nhấn phím (enter, space, a, b, ctrl, etc.) |
| `pause` | `pause` | Tạm dừng stream màn hình |
| `continue` | `continue` | Tiếp tục stream màn hình |
| `ping` | `ping` | Test độ trễ kết nối |
| `quit` | `quit` | Ngắt kết nối và thoát |

---

## 📦 CẤU TRÚC
```
controller/
├── README.md
└── controller_client.py    # Main controller code
```

---

## 🧪 TEST

### Test kết nối TCP
```bash
# Kiểm tra server có sẵn sàng không
python -c "import socket; s=socket.socket(); s.connect(('SERVER_IP',5555)); print('TCP OK')"
```

### Test gửi lệnh đơn giản
```python
# Test script
from controller_client import ControllerClient

client = ControllerClient('localhost')
if client.connect():
    client.mouse_click(100, 200)
    client.key_press('enter')
    client.disconnect()
```

---

## 📝 GHI CHÚ

- Server phải chạy trước khi client kết nối
- Mặc định kết nối đến `server_ip:5555`
- Pillow không bắt buộc nhưng cần thiết để xem màn hình nhận được
- Sử dụng `Ctrl+C` hoặc lệnh `quit` để thoát
- Tọa độ (x,y) phụ thuộc vào độ phân giải màn hình của Client B

---

## 🔧 TROUBLESHOOTING

**Lỗi kết nối:**
```
Connection failed: [Errno 10061] No connection could be made
```
→ Kiểm tra server đã chạy chưa và IP address đúng

**Không nhận được màn hình:**
→ Kiểm tra Client B (Streamer) đã kết nối và gửi dữ liệu chưa

**ImportError: PIL:**
→ Cài đặt Pillow: `pip install Pillow` (không bắt buộc)
