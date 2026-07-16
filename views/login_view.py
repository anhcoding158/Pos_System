import customtkinter as ctk
from tkinter import messagebox
import base64
from controllers.auth_controller import AuthController
from core.config_manager import ConfigManager

# Cấu hình giao diện chuẩn
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class LoginWindow:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.auth_controller = AuthController()

        self.config = ConfigManager()

        self.root.title("POS Enterprise F&B - Đăng Nhập")
        self.root.geometry("550x700")
        self.root.resizable(False, False)

        self._build_ui()
        self._load_saved_credentials()

    def _build_ui(self):
        # 1. Nền xám nhạt (#F8FAFC) phủ toàn màn hình
        self.bg_frame = ctk.CTkFrame(self.root, fg_color="#F8FAFC", corner_radius=0)
        self.bg_frame.pack(fill="both", expand=True)

        # 2. Thẻ Đăng nhập: Trắng tinh, KHÔNG VIỀN, bo góc 12px (Chuẩn Web App)
        self.main = ctk.CTkFrame(self.bg_frame, corner_radius=12, fg_color="white", width=380, height=480)
        self.main.place(relx=0.5, rely=0.45, anchor="center")

        # --- Header ---
        ctk.CTkLabel(self.main, text="🍽️", font=("Segoe UI Emoji", 42)).place(relx=0.5, rely=0.12, anchor="center")
        ctk.CTkLabel(self.main, text="POS ENTERPRISE", font=("Arial", 20, "bold"), text_color="#0F172A").place(relx=0.5,
                                                                                                               rely=0.22,
                                                                                                               anchor="center")
        ctk.CTkLabel(self.main, text="Hệ Thống Quản Lý F&B", font=("Arial", 13), text_color="#64748B").place(relx=0.5,
                                                                                                             rely=0.28,
                                                                                                             anchor="center")

        # --- Form Đăng Nhập ---
        # Viền mỏng 1px, bo góc 6px để trông sắc nét, chuyên nghiệp
        self.entry_user = ctk.CTkEntry(self.main, width=300, height=42, corner_radius=6, border_width=1,
                                       placeholder_text="Tên đăng nhập", font=("Arial", 14),
                                       fg_color="#F1F5F9", border_color="#CBD5E1", text_color="#0F172A")
        self.entry_user.place(relx=0.5, rely=0.43, anchor="center")

        self.entry_pwd = ctk.CTkEntry(self.main, width=300, height=42, corner_radius=6, border_width=1,
                                      show="•", placeholder_text="Mật khẩu", font=("Arial", 14),
                                      fg_color="#F1F5F9", border_color="#CBD5E1", text_color="#0F172A")
        self.entry_pwd.place(relx=0.5, rely=0.55, anchor="center")

        # --- Remember Me ---
        self.remember_var = ctk.IntVar(value=0)
        self.remember = ctk.CTkCheckBox(self.main, text="Ghi nhớ tài khoản", font=("Arial", 13),
                                        text_color="#475569", variable=self.remember_var,
                                        checkbox_width=20, checkbox_height=20, border_width=2, corner_radius=4,
                                        fg_color="#2563EB", border_color="#94A3B8")
        self.remember.place(relx=0.11, rely=0.66, anchor="w")

        # --- Error Label ---
        self.lbl_error = ctk.CTkLabel(self.main, text="", text_color="#EF4444", font=("Arial", 12))
        self.lbl_error.place(relx=0.5, rely=0.74, anchor="center")

        # --- Nút Đăng Nhập ---
        self.btn = ctk.CTkButton(
            self.main, text="ĐĂNG NHẬP", width=300, height=45,
            corner_radius=6, font=("Arial", 14, "bold"),
            fg_color="#2563EB", hover_color="#1D4ED8",
            command=self.handle_login
        )
        self.btn.place(relx=0.5, rely=0.85, anchor="center")

        # --- Footer ---
        ctk.CTkLabel(self.main, text="Phiên bản 2.0.0 (Enterprise)", font=("Arial", 11), text_color="#94A3B8").place(
            relx=0.5, rely=0.94, anchor="center")

    def _load_saved_credentials(self):
        saved_user = self.config.get("auth", "saved_user")
        saved_pwd_b64 = self.config.get("auth", "saved_pwd")

        if saved_user and saved_pwd_b64:
            try:
                saved_pwd = base64.b64decode(saved_pwd_b64).decode('utf-8')
                self.entry_user.insert(0, saved_user)
                self.entry_pwd.insert(0, saved_pwd)
                self.remember.select()
            except Exception:
                pass

    def handle_login(self):
        self.lbl_error.configure(text="")
        self.btn.configure(text="ĐANG KIỂM TRA...", state="disabled")
        self.root.update()

        username = self.entry_user.get().strip()
        password = self.entry_pwd.get().strip()

        if not username or not password:
            self.lbl_error.configure(text="Vui lòng nhập đầy đủ thông tin!")
            self.btn.configure(text="ĐĂNG NHẬP", state="normal")
            return

        user = self.auth_controller.login(username, password)

        if user:
            if self.remember_var.get() == 1:
                pwd_b64 = base64.b64encode(password.encode('utf-8')).decode('utf-8')
                self.config.update("auth", "saved_user", username)
                self.config.update("auth", "saved_pwd", pwd_b64)
            else:
                self.config.update("auth", "saved_user", "")
                self.config.update("auth", "saved_pwd", "")

            try:
                self.on_login_success(user["username"], user["role"])
            except TypeError:
                self.on_login_success(user)
        else:
            self.btn.configure(text="ĐĂNG NHẬP", state="normal")
            self.lbl_error.configure(text="Sai tài khoản hoặc mật khẩu!")