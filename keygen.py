import json
import base64
import hmac
import hashlib
from datetime import datetime, timedelta

# CHÌA KHÓA BÍ MẬT CỦA BẠN (Phải giữ bí mật tuyệt đối)
SECRET_KEY = b"ANHLINH_POS_ENTERPRISE_SECRET_KEY_2026_V99"


def base64_encode(data: str) -> str:
    """Mã hóa chuỗi thành Base64 (Bỏ dấu = ở cuối cho đẹp)"""
    return base64.urlsafe_b64encode(data.encode('utf-8')).decode('utf-8').rstrip("=")


def generate_pro_license(machine_id: str, duration_days: int, package: str = "ENTERPRISE"):
    # 1. Tính toán ngày hết hạn
    if duration_days >= 3650:
        exp_date = "PERMANENT"  # Vĩnh viễn
    else:
        exp_date = (datetime.now() + timedelta(days=duration_days)).strftime("%Y-%m-%d")

    # 2. Tạo khối dữ liệu (Payload) chứa Thông tin khách hàng
    payload = {
        "m": machine_id.upper(),  # Mã máy
        "e": exp_date,  # Ngày hết hạn
        "p": package,  # Loại gói
        "g": datetime.now().strftime("%Y%m%d")  # Ngày tạo Key
    }
    payload_json = json.dumps(payload, separators=(',', ':'))

    # 3. Tạo Chữ Ký Điện Tử bằng HMAC-SHA256 (Khách sửa 1 số là chữ ký sai ngay)
    signature = hmac.new(SECRET_KEY, payload_json.encode('utf-8'), hashlib.sha256).hexdigest()

    # 4. Mã hóa Base64 và nối thành Key hoàn chỉnh
    encoded_payload = base64_encode(payload_json)

    # Lấy 16 ký tự đầu của chữ ký cho gọn
    final_key = f"AL-{encoded_payload}-{signature[:16].upper()}"

    return final_key, payload


print("=" * 60)
print(" 🛡️ HỆ THỐNG CẤP PHÁT BẢN QUYỀN (DRM) - ANH LINH STORE")
print("=" * 60)

ma_may = input(" [>] Nhập Mã Máy của khách: ").strip()
so_ngay = int(input(" [>] Số ngày sử dụng (Ví dụ: 30, 365, hoặc 9999 cho Vĩnh viễn): "))

key, details = generate_pro_license(ma_may, so_ngay)

print("\n" + "=" * 60)
print(" ✅ TẠO KEY THÀNH CÔNG!")
print(f" 📌 Chi tiết gói: Mã máy [{details['m']}] - Hết hạn [{details['e']}]")
print(f" 🔑 LICENSE KEY GIAO KHÁCH: \n\n{key}\n")
print("=" * 60)