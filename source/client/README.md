# CLIENT MODULES

Thư mục này chứa 2 client modules:

## 📁 Cấu trúc

```
client/
├── README.md                    # File này
├── controller/                  # Client A - Controller
│   ├── README.md
│   └── controller_client.py
└── streamer/                    # Client B - Streamer  
    ├── README.md
    └── streamer_client.py
```

---

## 🎯 MÔ TẢ CÁC MODULE

### Client A - Controller (Thành viên 2: Phạm Hồng Quang)
- **Chức năng**: Gửi lệnh điều khiển đến server qua TCP
- **Công nghệ**: Python + Socket
- **Xem chi tiết**: [controller/README.md](controller/README.md)

### Client B - Streamer (Thành viên 3: Nguyễn Đình Tuấn)
- **Chức năng**: Capture và gửi màn hình qua UDP, nhận và thực thi lệnh
- **Công nghệ**: Python + mss + Pillow + pyautogui
- **Xem chi tiết**: [streamer/README.md](streamer/README.md)

---

## 🚀 HƯỚNG DẪN NHANH

### Cài đặt dependencies
```bash
# Từ thư mục gốc của project
pip install -r requirements.txt
```

### Chạy Controller (Client A)
```bash
cd controller
python controller_client.py <server_ip>
```

### Chạy Streamer (Client B)
```bash
cd streamer
python streamer_client.py <server_ip>
```

---

## � LƯU Ý

- Server phải chạy **trước** khi chạy các client
- Client B (Streamer) nên chạy trước Client A (Controller) để có màn hình hiển thị
- Cả 2 clients phải kết nối đến cùng một server