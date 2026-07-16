import customtkinter as ctk
from tkinter import messagebox
import uuid
import hashlib
import hmac
import json
import base64
from datetime import datetime

from views.login_view import LoginWindow
from views.cashier_view import CashierWindow
from views.admin_view import AdminWindow
from core.config_manager import ConfigManager
from database.db_session import init_db

# PHẢI TRÙNG KHỚP VỚI SECRET_KEY BÊN FILE KEYGEN.PY
SECRET_KEY = b"ANHLINH_POS_ENTERPRISE_SECRET_KEY_2026_V99"


def get_machine_id():
    """Lấy mã MAC của máy tính làm ID phần cứng"""
    mac = uuid.getnode()
    return hashlib.md5(str(mac).encode('utf-8')).hexdigest()[:12].upper()


def base64_decode(b64_string: str) -> str:
    """Thuật toán giải mã Base64 bù trừ padding"""
    padding = '=' * (8 - (len(b64_string) % 8)) % 8
    return base64.urlsafe_b64decode(b64_string + padding).decode('utf-8')


def verify_pro_license(machine_id, license_key):
    """SIÊU THUẬT TOÁN GIẢI MÃ VÀ KIỂM TRA BẢN QUYỀN"""
    try:
        if not license_key or not str(license_key).startswith("AL-"):
            return False, "Chưa kích hoạt hoặc Mã không hợp lệ!"

        # Cắt lấy phần Dữ liệu (Payload) và Chữ ký (Signature)
        parts = str(license_key)[3:].split('-')
        if len(parts) != 2:
            return False, "Cấu trúc mã bảo mật đã bị phá hoại!"

        encoded_payload, provided_signature = parts

        # Giải mã Payload để đọc thông tin
        payload_json = base64_decode(encoded_payload)
        payload = json.loads(payload_json)

        # 1. KIỂM TRA CHỮ KÝ (Chống hack đổi ngày hết hạn)
        expected_sig = hmac.new(SECRET_KEY, payload_json.encode('utf-8'), hashlib.sha256).hexdigest()[:16].upper()
        if provided_signature != expected_sig:
            return False, "⛔ LỖI AN NINH: Mã kích hoạt đã bị can thiệp trái phép!"

        # 2. KIỂM TRA MÃ MÁY (Chống mang Key sang máy khác)
        if payload.get("m") != machine_id:
            return False, "⛔ LỖI BẢN QUYỀN: Key này được cấp cho máy khác, không phải máy này!"

        # 3. KIỂM TRA THỜI HẠN (Chống xài chùa)
        exp_date = payload.get("e")
        if exp_date != "PERMANENT":
            exp_dt = datetime.strptime(exp_date, "%Y-%m-%d")
            if datetime.now() > exp_dt:
                return False, f"⏳ BẢN QUYỀN ĐÃ HẾT HẠN vào ngày {exp_date}!\nVui lòng liên hệ Admin để gia hạn."

        return True, f"Bản quyền {payload.get('p')} hợp lệ!"
    except Exception:
        return False, "⛔ Lỗi giải mã: Khóa không đúng định dạng!"


class AppController:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Hệ Thống POS Enterprise")
        self.root.geometry("1150x700")
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        self.config = ConfigManager()
        self.check_license_first()

    def check_license_first(self):
        """Bảo vệ ứng dụng trước khi vào màn Đăng nhập"""
        machine_id = get_machine_id()
        is_activated = self.config.get("security", "is_activated")
        saved_key = self.config.get("security", "license_key")

        is_valid, msg = verify_pro_license(machine_id, saved_key)

        if is_activated and is_valid:
            self.show_login_window()
        else:
            # Nếu có lỗi (hết hạn, sai máy, can thiệp), hiện lỗi cho khách xem
            self.show_activation_window(machine_id, error_msg=msg if saved_key else None)

    def show_activation_window(self, machine_id, error_msg=None):
        self.clear_screen()
        self.root.geometry("650x450")

        frame = ctk.CTkFrame(self.root, fg_color="white", corner_radius=15)
        frame.pack(expand=True, padx=40, pady=40, fill="both")

        ctk.CTkLabel(frame, text="🔒 PHẦN MỀM CHƯA ĐƯỢC KÍCH HOẠT", font=("Arial", 20, "bold"),
                     text_color="#EF4444").pack(pady=(30, 5))

        if error_msg:
            ctk.CTkLabel(frame, text=error_msg, font=("Arial", 13, "bold"), text_color="#Eab308").pack(pady=(0, 15))
        else:
            ctk.CTkLabel(frame, text="Vui lòng gửi Mã Máy bên dưới cho Nhà phát triển để mua Bản Quyền.",
                         font=("Arial", 13)).pack(pady=(0, 15))

        # MÃ MÁY
        txt_machine = ctk.CTkEntry(frame, width=300, font=("Courier New", 20, "bold"), justify="center",
                                   fg_color="#F1F5F9")
        txt_machine.pack(pady=10)
        txt_machine.insert(0, machine_id)
        txt_machine.configure(state="readonly")

        ctk.CTkLabel(frame, text="Nhập Mã Kích Hoạt (License Key) do Admin cấp:", font=("Arial", 12, "bold")).pack(
            pady=(20, 5))
        txt_key = ctk.CTkEntry(frame, width=450, font=("Courier New", 14), justify="center")
        txt_key.pack(pady=5)

        def activate():
            key = txt_key.get().strip()
            is_valid, msg = verify_pro_license(machine_id, key)

            if is_valid:
                self.config.update("security", "is_activated", True)
                self.config.update("security", "license_key", key)
                messagebox.showinfo("Thành công", "🎉 Kích hoạt bản quyền thành công!\nCảm ơn bạn đã tin dùng sản phẩm.")
                self.root.geometry("1150x700")
                self.show_login_window()
            else:
                messagebox.showerror("Lỗi Kích Hoạt", msg)

        ctk.CTkButton(frame, text="✅ XÁC NHẬN KÍCH HOẠT", font=("Arial", 14, "bold"), fg_color="#10B981",
                      hover_color="#059669", height=45, command=activate).pack(pady=20)

    def clear_screen(self):
        for widget in self.root.winfo_children(): widget.destroy()

    def show_login_window(self):
        self.clear_screen()
        LoginWindow(self.root, on_login_success=self.show_home_window)

    def show_home_window(self, username, role):
        self.clear_screen()
        if role == 'admin':
            AdminWindow(self.root, username, on_logout_callback=self.show_login_window)
        else:
            CashierWindow(self.root, username, on_logout_callback=self.show_login_window)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    init_db()
    app = AppController()
    app.run()