# MODULE CLIENT B - STREAMER

**Thành viên:** Nguyễn Đình Tuấn (B22DCCN759)

---

## 🎯 MỤC TIÊU

Client Streamer chịu trách nhiệm:
- Kết nối đến server qua **TCP** (port 5555) để nhận lệnh điều khiển
- Gửi dữ liệu màn hình qua **UDP** (port 5556) đến server
- Capture màn hình liên tục (khoảng 10 FPS)
- Nhận và thực thi lệnh từ Client A (qua server): mouse click, move, keyboard
- Xử lý lệnh pause/continue để điều khiển stream
- **Viết hướng dẫn chạy Client B**

---

## ⚙️ CÔNG NGHỆ SỬ DỤNG

| Thành phần | Công nghệ |
|------------|-----------|
| Ngôn ngữ | Python 3.11+ |
| Thư viện capture màn hình | mss |
| Thư viện xử lý ảnh | Pillow (PIL) |
| Thư viện điều khiển | pyautogui |
| Giao thức | TCP (lệnh), UDP (màn hình) |

---

## 🚀 HƯỚNG DẪN CHẠY

### Cài đặt
```bash
# Cài đặt các thư viện cần thiết
pip install mss Pillow pyautogui

# Hoặc cài theo requirements.txt
pip install -r requirements.txt
```

### Chạy chương trình với GUI (Khuyến nghị ⭐)
```bash
cd source/client/streamer
python streamer_gui.py
```

**Giao diện GUI giống TeamViewer:**
- 📍 **Your Computer ID**: Hiển thị IP local để share cho người khác
- 📋 **Copy ID**: Copy IP vào clipboard
- 🔗 **Server Connection**: Nhập Server IP
- 🟢 **Start Sharing**: Bắt đầu cho phép điều khiển từ xa
- 🔴 **Stop Sharing**: Dừng share màn hình
- 📊 **Statistics**: Theo dõi frames sent và commands received
- 📋 **Activity Log**: Xem log real-time

### Chạy CLI mode
```bash
python streamer_client.py

# Hoặc chỉ định IP server ngay
python streamer_client.py 192.168.1.100
```

### Nhập thông tin
```
Enter server IP address [localhost]: 192.168.1.100
```

---

## 💡 HOẠT ĐỘNG

### Quá trình stream

1. **Kết nối TCP**: Kết nối đến server để nhận lệnh điều khiển
2. **Stream màn hình**: 
   - Capture toàn bộ màn hình
   - Resize về 800x600 để giảm bandwidth
   - Nén JPEG với quality 60%
   - Gửi qua UDP đến server
   - Target FPS: ~10 frames/giây
3. **Nhận lệnh**: Lắng nghe lệnh từ server (từ Controller)
4. **Thực thi**: Thực hiện các thao tác điều khiển

### Các lệnh được hỗ trợ

| Lệnh | Chức năng | Mô tả |
|------|-----------|-------|
| `MOUSE_CLICK` | Click chuột | Nhận tọa độ (x,y) và button, thực hiện click |
| `MOUSE_MOVE` | Di chuyển chuột | Nhận tọa độ (x,y), di chuyển con trỏ |
| `KEY_PRESS` | Nhấn phím | Nhận tên phím, thực hiện nhấn |
| `PAUSE` | Tạm dừng stream | Dừng gửi màn hình (vẫn nhận lệnh) |
| `CONTINUE` | Tiếp tục stream | Tiếp tục gửi màn hình |
| `DISCONNECT` | Ngắt kết nối | Đóng client |

---

## 📦 CẤU TRÚC
```
streamer/
├── README.md
└── streamer_client.py    # Main streamer code
```

---

## 🧪 TEST

### Test capture màn hình
```python
# Test script
import mss
from PIL import Image

with mss.mss() as sct:
    monitor = sct.monitors[1]
    screenshot = sct.grab(monitor)
    img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
    img.save('test_screenshot.png')
    print(f"Screenshot saved: {img.size}")
```

### Test UDP gửi dữ liệu
```bash
python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.sendto(b'test data',('SERVER_IP',5556)); print('UDP OK')"
```

---

## 📊 LOG OUTPUT

Client sẽ hiển thị log như sau:

```
============================================================
REMOTE DESKTOP CONTROL - CLIENT B (STREAMER)
Thành viên 3: Nguyễn Đình Tuấn (B22DCCN759)
============================================================

[2025-11-02 10:30:49] Connected to server at 192.168.1.100
[2025-11-02 10:30:49] TCP port: 5555, UDP port: 5556
[2025-11-02 10:30:49] Streamer client started successfully
[2025-11-02 10:30:49] Press Ctrl+C to stop
[2025-11-02 10:31:19] Streamed 30 frames, last size: 15432 bytes
[2025-11-02 10:31:20] Received command: MOUSE_CLICK
[2025-11-02 10:31:20] Clicked at (1280, 720) with left button
```

---

## 📝 GHI CHÚ

- Server phải chạy **trước** khi client kết nối
- Yêu cầu quyền truy cập màn hình trên một số OS (macOS, Linux)
- Tọa độ chuột được scale từ 800x600 về resolution thực tế
- Stream target: ~10 FPS (có thể điều chỉnh trong code)
- Chất lượng JPEG: 60% (cân bằng giữa chất lượng và bandwidth)
- Sử dụng `Ctrl+C` để dừng client

---

## 🔧 TROUBLESHOOTING

**Lỗi: mss not installed**
```
pip install mss
```

**Lỗi: PIL not installed**
```
pip install Pillow
```

**Lỗi: pyautogui not installed**
```
pip install pyautogui
```

**Không capture được màn hình (macOS/Linux):**
→ Cấp quyền truy cập màn hình trong System Preferences/Settings

**Lệnh điều khiển không hoạt động:**
→ Kiểm tra pyautogui đã cài đặt chưa và có quyền điều khiển hệ thống

**UDP packet loss:**
→ Giảm FPS hoặc tăng compression (giảm quality JPEG)

---

## ⚠️ BẢO MẬT

**Lưu ý quan trọng:**
- Client này cho phép **điều khiển hoàn toàn** máy tính của bạn
- Chỉ chạy khi kết nối đến server **tin cậy**
- Không sử dụng trên mạng công cộng không mã hóa
- Dành cho **mục đích học tập và test trong mạng nội bộ**
