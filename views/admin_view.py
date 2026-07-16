import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import bcrypt
import base64

from core.config_manager import ConfigManager
from database.db_session import SessionLocal
from database.models import Order, OrderItem, OrderStatusEnum, User, RoleEnum
from services.product_service import ProductService
from services.qr_service import QRService


class AdminWindow:
    def __init__(self, root, username, on_logout_callback=None):
        self.root = root
        self.current_username = username
        self.on_logout_callback = on_logout_callback

        self.root.title(f"Quản Trị Hệ Thống - Admin: {username}")
        self.root.geometry("1300x850")
        self.root.minsize(1100, 750)
        ctk.set_appearance_mode("light")

        self.config = ConfigManager()

        # BỘ NHỚ ĐỆM CỬA SỔ PHỤ (Tránh giật lag khi mở lại)
        self.cached_windows = {}

        self.bg_frame = ctk.CTkFrame(self.root, fg_color="#F1F5F9", corner_radius=0)
        self.bg_frame.pack(fill="both", expand=True)

        self.sidebar = ctk.CTkFrame(self.bg_frame, width=260, fg_color="#1E293B", corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main_content = ctk.CTkFrame(self.bg_frame, fg_color="transparent", corner_radius=0)
        self.main_content.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        self._build_sidebar_menu()
        self._build_header()
        self._build_qr_config()
        self._build_product_form()
        self._build_action_buttons()
        self._build_data_table()

        self.load_inventory()

    # ================= THUẬT TOÁN QUẢN LÝ CỬA SỔ PHỤ (CHỐNG GIẬT LAG) =================
    def center_modal(self, window, width, height):
        self.root.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_rooty() + (self.root.winfo_height() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def get_or_create_modal(self, window_key, title_text, width, height):
        """Siêu thuật toán: Nếu cửa sổ đã có, gọi nó dậy. Nếu chưa, tạo mới."""

        # NẾU CỬA SỔ ĐÃ TỒN TẠI TRONG BỘ NHỚ -> ĐÁNH THỨC NÓ DẬY NGAY LẬP TỨC
        if window_key in self.cached_windows and self.cached_windows[window_key].winfo_exists():
            modal = self.cached_windows[window_key]
            modal.deiconify()  # Đưa nó ra ánh sáng
            modal.lift()
            modal.grab_set()  # Khóa nền
            return modal, False  # False nghĩa là "Không phải tạo mới"

        # NẾU CHƯA CÓ -> TIẾN HÀNH XÂY DỰNG MỚI
        self.root.update_idletasks()
        modal = ctk.CTkToplevel(self.root)
        modal.geometry(f"{width}x{height}")
        self.center_modal(modal, width, height)
        modal.overrideredirect(True)
        modal.attributes("-topmost", True)
        modal.grab_set()
        modal.configure(fg_color="#F8FAFC", border_width=2, border_color="#94A3B8")

        header = ctk.CTkFrame(modal, fg_color="white", height=45, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=title_text, font=("Arial", 15, "bold"), text_color="#0F172A").pack(side="left",
                                                                                                     padx=15)

        def close_modal():
            modal.grab_release()
            modal.withdraw()  # THUẬT TOÁN ẨN MÌNH, KHÔNG HỦY DIỆT ĐỂ LẦN SAU MỞ LÊN 1MS

        btn_close = ctk.CTkButton(header, text="✖", width=30, height=30, fg_color="transparent",
                                  hover_color="#FEE2E2", text_color="#EF4444", font=("Arial", 16),
                                  command=close_modal)
        btn_close.pack(side="right", padx=5)

        # Lưu vào kho chứa
        self.cached_windows[window_key] = modal

        return modal, True  # True nghĩa là "Vừa tạo mới xong, cần xây dựng ruột bên trong"

    # ================= GIAO DIỆN CHÍNH =================
    def _build_sidebar_menu(self):
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", pady=(40, 30))

        ctk.CTkLabel(brand_frame, text="📦", font=("Arial", 36)).pack(side="left", padx=(20, 10))
        text_frame = ctk.CTkFrame(brand_frame, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(text_frame, text="POS", font=("Arial", 20, "bold"), text_color="#38BDF8", anchor="w").pack(
            fill="x")
        ctk.CTkLabel(text_frame, text="ENTERPRISE", font=("Arial", 12, "bold"), text_color="white", anchor="w").pack(
            fill="x")

        ctk.CTkLabel(self.sidebar, text="QUẢN LÝ HỆ THỐNG", font=("Arial", 11, "bold"), text_color="#64748B",
                     anchor="w").pack(fill="x", padx=25, pady=(10, 5))

        menu_configs = [
            ("🏠", "Tổng quan", None, False),
            ("📁", "Sản phẩm", None, True),
            ("👥", "Nhân sự", self.show_user_management_window, False),
            ("📊", "Báo cáo", self.show_report_window, False),
            ("⚙️", "Cài đặt", None, False),
        ]

        for icon, text, cmd, is_active in menu_configs:
            bg_color = "#3B82F6" if is_active else "transparent"
            text_color = "white" if is_active else "#94A3B8"
            hover_color = "#2563EB" if is_active else "#334155"

            btn = ctk.CTkButton(self.sidebar, text=f"{icon}   {text}", font=("Arial", 14, "bold"),
                                fg_color=bg_color, text_color=text_color, hover_color=hover_color,
                                anchor="w", height=45, corner_radius=8, command=cmd)
            btn.pack(fill="x", padx=15, pady=4)

        status_card = ctk.CTkFrame(self.sidebar, fg_color="#0F172A", corner_radius=12)
        status_card.pack(fill="x", padx=20, pady=(100, 20), side="bottom")
        ctk.CTkLabel(status_card, text="🛡️ Hệ thống ổn định", font=("Arial", 12, "bold"), text_color="white").pack(
            pady=(15, 5))
        ctk.CTkLabel(status_card, text="Mọi dữ liệu được bảo mật", font=("Arial", 11), text_color="#64748B").pack(
            pady=(0, 15))

    def _build_header(self):
        header_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(title_frame, text="⚙️ QUẢN TRỊ HỆ THỐNG", font=("Arial", 28, "bold"), text_color="#0F172A",
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(title_frame, text="Chào mừng bạn quay trở lại! 👋", font=("Arial", 14), text_color="#64748B",
                     anchor="w").pack(fill="x")

        ctk.CTkButton(header_frame, text="🚪 Đăng xuất", fg_color="#EF4444", hover_color="#DC2626",
                      font=("Arial", 13, "bold"), width=120, height=40, corner_radius=8, command=self.logout).pack(
            side="right", pady=10)

    def _build_qr_config(self):
        qr_card = ctk.CTkFrame(self.main_content, fg_color="white", corner_radius=15, border_width=1,
                               border_color="#E2E8F0")
        qr_card.pack(fill="x", pady=(0, 15))

        inner_frame = ctk.CTkFrame(qr_card, fg_color="transparent")
        inner_frame.pack(fill="x", padx=25, pady=15)

        ctk.CTkLabel(inner_frame, text="🖩", font=("Arial", 40), text_color="#8B5CF6").pack(side="left", padx=(0, 20))

        info_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(info_frame, text="MÃ QR THANH TOÁN", font=("Arial", 12, "bold"), text_color="#64748B",
                     anchor="w").pack(fill="x")

        self.lbl_qr_status = ctk.CTkLabel(info_frame, text="Đang tải dữ liệu...", font=("Courier New", 13, "italic"),
                                          anchor="w", fg_color="#F8FAFC", corner_radius=6, height=35)
        self.lbl_qr_status.pack(fill="x", pady=(5, 0))

        self.btn_upload_qr = ctk.CTkButton(inner_frame, text="✏️ Cập nhật QR", fg_color="#6366F1",
                                           hover_color="#4F46E5", font=("Arial", 13, "bold"), width=150, height=40,
                                           corner_radius=8, command=self.upload_qr_image)
        self.btn_upload_qr.pack(side="right", padx=(20, 0))

        self._check_qr_status()

    def _check_qr_status(self):
        secure_qr = self.config.get("payment", "secure_qr_code")
        if secure_qr:
            self.lbl_qr_status.configure(text=f"  ✅ Đã mã hóa bảo mật (Base64: {secure_qr[:15]}...)",
                                         text_color="#10B981")
        else:
            self.lbl_qr_status.configure(text="  ❌ Chưa có dữ liệu mã QR!", text_color="#EF4444")

    def upload_qr_image(self):
        file_path = filedialog.askopenfilename(title="Chọn ảnh mã VietQR",
                                               filetypes=[("Image files", "*.jpg *.png *.jpeg")])
        if not file_path: return

        self.lbl_qr_status.configure(text="  ⏳ Đang phân tích mã...", text_color="#F59E0B")
        self.root.update()

        success, msg = QRService.process_and_save_qr(file_path)
        if success:
            messagebox.showinfo("Bảo mật", msg)
        else:
            messagebox.showerror("Cảnh báo An ninh", msg)
        self._check_qr_status()

    def _build_product_form(self):
        form_card = ctk.CTkFrame(self.main_content, fg_color="white", corner_radius=15, border_width=1,
                                 border_color="#E2E8F0")
        form_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form_card, text="🏷️ THÔNG TIN SẢN PHẨM", font=("Arial", 15, "bold"), text_color="#1E293B").pack(
            anchor="w", padx=25, pady=(15, 5))

        grid_frame = ctk.CTkFrame(form_card, fg_color="transparent")
        grid_frame.pack(fill="x", padx=25, pady=(0, 20))

        self.entries = {}
        self.current_img_path = ""

        columns_config = [
            ("Mã Sản Phẩm *", "code", 120, "SP001"),
            ("Tên Sản Phẩm *", "name", 300, "Trà Đào"),
            ("Giá Bán (VNĐ) *", "price", 150, "35000"),
            ("Tồn Kho *", "stock", 100, "100")
        ]

        for i, (label_text, key, width, placeholder) in enumerate(columns_config):
            ctk.CTkLabel(grid_frame, text=label_text, font=("Arial", 12, "bold"), text_color="#64748B").grid(row=0,
                                                                                                             column=i,
                                                                                                             sticky="w",
                                                                                                             padx=(
                                                                                                             0, 15))
            entry = ctk.CTkEntry(grid_frame, width=width, height=42, font=("Arial", 14), fg_color="#F8FAFC",
                                 border_color="#E2E8F0", placeholder_text=placeholder)
            entry.grid(row=1, column=i, sticky="w", padx=(0, 15), pady=(5, 0))
            self.entries[key] = entry

        ctk.CTkLabel(grid_frame, text="Ảnh minh họa", font=("Arial", 12, "bold"), text_color="#64748B").grid(row=0,
                                                                                                             column=4,
                                                                                                             sticky="w",
                                                                                                             padx=(
                                                                                                             0, 15))
        self.btn_select_img = ctk.CTkButton(grid_frame, text="🖼️ Tải Ảnh Lên", fg_color="#8B5CF6",
                                            hover_color="#7C3AED", height=42, command=self.select_product_image)
        self.btn_select_img.grid(row=1, column=4, sticky="w", padx=(0, 15), pady=(5, 0))

    def select_product_image(self):
        file_path = filedialog.askopenfilename(title="Chọn ảnh sản phẩm",
                                               filetypes=[("Image files", "*.jpg *.png *.jpeg")])
        if file_path:
            self.current_img_path = file_path
            self.btn_select_img.configure(text="✅ Đã Chọn", fg_color="#10B981")

    def _build_action_buttons(self):
        btn_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 15))

        button_configs = [
            ("➕ Thêm Mới", "#10B981", "#059669", self.add_product),
            ("🔄 Cập Nhật", "#3B82F6", "#2563EB", self.update_product),
            ("🗑️ Xóa SP", "#EF4444", "#DC2626", self.delete_product),
            ("🧹 Làm mới Form", "#F97316", "#EA580C", self.clear_fields)
        ]

        for text, fg, hover, cmd in button_configs:
            ctk.CTkButton(btn_frame, text=text, fg_color=fg, hover_color=hover, font=("Arial", 14, "bold"), width=150,
                          height=45, corner_radius=8, command=cmd).pack(side="left", padx=(0, 15))

    def _build_data_table(self):
        table_card = ctk.CTkFrame(self.main_content, fg_color="white", corner_radius=15, border_width=1,
                                  border_color="#E2E8F0")
        table_card.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview", background="white", foreground="#0F172A", rowheight=45, font=("Arial", 13),
                        borderwidth=1, relief="solid")
        style.configure("Treeview.Heading", background="#6366F1", foreground="white", font=("Arial", 13, "bold"),
                        borderwidth=1, relief="flat")
        style.map("Treeview", background=[("selected", "#EFF6FF")], foreground=[("selected", "#4F46E5")])

        tree_frame = tk.Frame(table_card, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=20)

        scroll_y = ttk.Scrollbar(tree_frame)
        scroll_y.pack(side="right", fill="y")

        self.tree = ttk.Treeview(tree_frame, columns=("stt", "code", "name", "price", "stock"), show="headings",
                                 yscrollcommand=scroll_y.set)
        scroll_y.config(command=self.tree.yview)

        self.tree.tag_configure('evenrow', background='#F8FAFC')
        self.tree.tag_configure('oddrow', background='white')

        self.tree.heading("stt", text="STT", anchor="center")
        self.tree.column("stt", width=60, anchor="center")
        self.tree.heading("code", text="MÃ SẢN PHẨM", anchor="center")
        self.tree.column("code", width=140, anchor="center")
        self.tree.heading("name", text="TÊN SẢN PHẨM", anchor="w")
        self.tree.column("name", width=420, anchor="w")
        self.tree.heading("price", text="ĐƠN GIÁ (VNĐ)", anchor="e")
        self.tree.column("price", width=180, anchor="e")
        self.tree.heading("stock", text="TỒN KHO", anchor="center")
        self.tree.column("stock", width=120, anchor="center")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)

    def on_item_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        vals = self.tree.item(selected[0])['values']

        for entry in self.entries.values():
            entry.delete(0, 'end')

        self.entries['code'].insert(0, vals[1])
        self.entries['name'].insert(0, vals[2])
        self.entries['price'].insert(0, str(vals[3]).replace(",", ""))
        self.entries['stock'].insert(0, vals[4])

    def load_inventory(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        success, data_or_error = ProductService.get_all_active()
        if success:
            for index, p in enumerate(data_or_error):
                tag = 'evenrow' if index % 2 == 0 else 'oddrow'
                self.tree.insert("", tk.END, values=(index + 1, p[0], p[1], f"{p[2]:,.0f}", p[3]), tags=(tag,))
        else:
            messagebox.showerror("Lỗi CSDL", data_or_error)

    def add_product(self):
        try:
            code = self.entries['code'].get().strip()
            name = self.entries['name'].get().strip()
            price = float(self.entries['price'].get())
            stock = int(self.entries['stock'].get())

            if not code or not name:
                messagebox.showerror("Lỗi", "Mã và Tên sản phẩm không được để trống!")
                return

            success, msg = ProductService.add_product(code, name, price, stock, getattr(self, 'current_img_path', ""))
            if success:
                self.load_inventory()
                self.clear_fields()
                messagebox.showinfo("Thành công", msg)
            else:
                messagebox.showerror("Lỗi", msg)
        except ValueError:
            messagebox.showerror("Lỗi", "Giá và Tồn kho phải là số hợp lệ!")

    def update_product(self):
        try:
            code = self.entries['code'].get().strip()
            name = self.entries['name'].get().strip()
            price = float(self.entries['price'].get())
            stock = int(self.entries['stock'].get())

            success, msg = ProductService.update_product(code, name, price, stock,
                                                         getattr(self, 'current_img_path', ""))
            if success:
                self.load_inventory()
                self.clear_fields()
                messagebox.showinfo("Thành công", msg)
            else:
                messagebox.showerror("Lỗi", msg)
        except ValueError:
            messagebox.showerror("Lỗi", "Giá và Tồn kho phải là số hợp lệ!")

    def delete_product(self):
        code = self.entries['code'].get().strip()
        if not code: return

        if messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa (ẩn) SP: {code}?"):
            success, msg = ProductService.soft_delete_product(code)
            if success:
                self.load_inventory()
                self.clear_fields()
                messagebox.showinfo("Thành công", msg)
            else:
                messagebox.showerror("Lỗi", msg)

    def clear_fields(self):
        for entry in self.entries.values():
            entry.delete(0, 'end')
        self.current_img_path = ""
        self.btn_select_img.configure(text="🖼️ Tải Ảnh Lên", fg_color="#8B5CF6")
        if hasattr(self, 'tree') and self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def logout(self):
        if self.on_logout_callback: self.on_logout_callback()

    # ================= QUẢN LÝ NHÂN SỰ =================
    def show_user_management_window(self):
        # DÙNG THUẬT TOÁN KIỂM TRA BỘ NHỚ ĐỆM TRƯỚC KHI TẠO CỬA SỔ
        user_win, is_new = self.get_or_create_modal("user_modal", "👥 Quản lý Nhân sự", 850, 550)

        if not is_new:
            # Nếu chỉ gọi cửa sổ cũ dậy, cần tải lại dữ liệu nhân sự mới nhất từ CSDL
            if hasattr(self, 'load_users_func'): self.load_users_func()
            return

        # NẾU LÀ LẦN ĐẦU MỞ, TIẾN HÀNH VẼ GIAO DIỆN BÊN TRONG CỬA SỔ NÀY
        form_frame = ctk.CTkFrame(user_win, fg_color="white", corner_radius=10, border_width=1, border_color="#E2E8F0")
        form_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(form_frame, text="Tài khoản:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=15, pady=15,
                                                                                     sticky="e")
        txt_username = ctk.CTkEntry(form_frame, width=200, fg_color="#F1F5F9", border_width=1)
        txt_username.grid(row=0, column=1, padx=5, pady=15)

        ctk.CTkLabel(form_frame, text="Mật khẩu (Bỏ trống nếu ko đổi):", font=("Arial", 12, "bold")).grid(row=0,
                                                                                                          column=2,
                                                                                                          padx=15,
                                                                                                          pady=15,
                                                                                                          sticky="e")
        txt_password = ctk.CTkEntry(form_frame, width=200, show="*", fg_color="#F1F5F9", border_width=1)
        txt_password.grid(row=0, column=3, padx=5, pady=15)

        ctk.CTkLabel(form_frame, text="Họ và tên:", font=("Arial", 12, "bold")).grid(row=1, column=0, padx=15, pady=15,
                                                                                     sticky="e")
        txt_fullname = ctk.CTkEntry(form_frame, width=200, fg_color="#F1F5F9", border_width=1)
        txt_fullname.grid(row=1, column=1, padx=5, pady=15)

        ctk.CTkLabel(form_frame, text="Phân quyền:", font=("Arial", 12, "bold")).grid(row=1, column=2, padx=15, pady=15,
                                                                                      sticky="e")
        cb_role = ctk.CTkComboBox(form_frame, values=["admin", "cashier"], width=200, fg_color="#F1F5F9",
                                  border_width=1)
        cb_role.grid(row=1, column=3, padx=5, pady=15)
        cb_role.set("cashier")

        btn_frame = ctk.CTkFrame(user_win, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=5)

        tree_frame = ctk.CTkFrame(user_win, fg_color="white", corner_radius=10)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=20)

        tree_users = ttk.Treeview(tree_frame, columns=("id", "username", "fullname", "role"), show="headings", height=8)
        tree_users.heading("id", text="ID")
        tree_users.column("id", width=50, anchor="center")
        tree_users.heading("username", text="TÀI KHOẢN")
        tree_users.column("username", width=150)
        tree_users.heading("fullname", text="HỌ VÀ TÊN")
        tree_users.column("fullname", width=250)
        tree_users.heading("role", text="CHỨC VỤ")
        tree_users.column("role", width=150, anchor="center")
        tree_users.pack(fill="both", expand=True, padx=2, pady=2)

        def clear_form():
            txt_username.delete(0, 'end')
            txt_password.delete(0, 'end')
            txt_fullname.delete(0, 'end')
            cb_role.set("cashier")
            if tree_users.selection():
                tree_users.selection_remove(tree_users.selection())

        def load_users():
            for item in tree_users.get_children(): tree_users.delete(item)
            session = SessionLocal()
            try:
                for u in session.query(User).filter_by(is_active=True).all():
                    tree_users.insert("", tk.END, values=(u.id, u.username, u.full_name, u.role.value))
            finally:
                session.close()

        # Lưu lại hàm tải dữ liệu để gọi mỗi khi đánh thức cửa sổ này
        self.load_users_func = load_users

        def on_user_select(event):
            selected = tree_users.selection()
            if not selected: return
            vals = tree_users.item(selected[0])['values']

            txt_username.delete(0, 'end')
            txt_password.delete(0, 'end')
            txt_fullname.delete(0, 'end')

            txt_username.insert(0, vals[1])
            txt_fullname.insert(0, vals[2] if vals[2] else "")
            cb_role.set(vals[3])

        tree_users.bind("<<TreeviewSelect>>", on_user_select)

        def add_user():
            session = SessionLocal()
            try:
                uname, pwd, fname = txt_username.get().strip(), txt_password.get().strip(), txt_fullname.get().strip()
                if not uname or not pwd:
                    messagebox.showerror("Lỗi", "Thiếu TK/MK!", parent=user_win)
                    return
                if session.query(User).filter_by(username=uname).first():
                    messagebox.showerror("Lỗi", "TK đã tồn tại!", parent=user_win)
                    return

                salt = bcrypt.gensalt()
                hashed_pwd = bcrypt.hashpw(pwd.encode('utf-8'), salt).decode('utf-8')
                new_user = User(username=uname, password_hash=hashed_pwd, full_name=fname,
                                role=RoleEnum.ADMIN if cb_role.get() == "admin" else RoleEnum.CASHIER)
                session.add(new_user)
                session.commit()
                load_users()
                clear_form()
            finally:
                session.close()

        def update_user():
            selected = tree_users.selection()
            if not selected:
                messagebox.showwarning("Nhắc nhở", "Vui lòng CLICK CHUỘT vào một nhân viên trước khi Cập nhật!",
                                       parent=user_win)
                return

            session = SessionLocal()
            try:
                user_id = tree_users.item(selected[0])['values'][0]
                user = session.query(User).filter_by(id=user_id).first()
                uname, pwd, fname = txt_username.get().strip(), txt_password.get().strip(), txt_fullname.get().strip()

                if not uname:
                    messagebox.showerror("Lỗi", "Tài khoản không được rỗng!", parent=user_win)
                    return
                if uname != user.username and session.query(User).filter_by(username=uname).first():
                    messagebox.showerror("Lỗi", "Tài khoản bị trùng!", parent=user_win)
                    return

                user.username = uname
                user.full_name = fname
                user.role = RoleEnum.ADMIN if cb_role.get() == "admin" else RoleEnum.CASHIER
                if pwd:
                    salt = bcrypt.gensalt()
                    user.password_hash = bcrypt.hashpw(pwd.encode('utf-8'), salt).decode('utf-8')

                session.commit()
                load_users()
                messagebox.showinfo("Thành công", "Đã cập nhật!", parent=user_win)
            finally:
                session.close()

        def delete_user():
            selected = tree_users.selection()
            if not selected:
                messagebox.showwarning("Nhắc nhở",
                                       "Vui lòng CLICK CHUỘT vào một nhân viên trong bảng bên dưới trước khi Xóa!",
                                       parent=user_win)
                return
            uname = tree_users.item(selected[0])['values'][1]
            if uname == self.current_username:
                messagebox.showerror("Lỗi", "Không thể tự xóa chính mình!", parent=user_win)
                return
            if messagebox.askyesno("Xác nhận", f"Xóa tài khoản {uname}?", parent=user_win):
                session = SessionLocal()
                try:
                    user_id = tree_users.item(selected[0])['values'][0]
                    user = session.query(User).filter_by(id=user_id).first()

                    user.is_active = False
                    session.commit()

                    load_users()
                    clear_form()
                    messagebox.showinfo("Thành công", "Đã vô hiệu hóa tài khoản!", parent=user_win)
                except Exception as e:
                    messagebox.showerror("Lỗi CSDL", f"Lỗi: {e}", parent=user_win)
                finally:
                    session.close()

        ctk.CTkButton(btn_frame, text="Thêm", fg_color="#10B981", hover_color="#059669", width=100,
                      command=add_user).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cập nhật", fg_color="#3B82F6", hover_color="#2563EB", width=100,
                      command=update_user).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Xóa", fg_color="#EF4444", hover_color="#DC2626", width=100,
                      command=delete_user).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Làm mới", fg_color="#94A3B8", hover_color="#64748B", width=100,
                      command=clear_form).pack(side="left", padx=5)

        load_users()

    # ================= BÁO CÁO DOANH THU =================
    def show_report_window(self):
        # DÙNG THUẬT TOÁN KIỂM TRA BỘ NHỚ ĐỆM
        report_win, is_new = self.get_or_create_modal("report_modal", "📊 Báo cáo kinh doanh", 900, 650)

        if not is_new:
            # Chỉ nạp lại báo cáo (để lỡ có đơn mới vừa bán thì hiển thị luôn)
            if hasattr(self, 'load_report_func'): self.load_report_func()
            return

        filter_frame = ctk.CTkFrame(report_win, fg_color="white", corner_radius=10)
        filter_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(filter_frame, text="Từ:", font=("Arial", 12, "bold")).pack(side="left", padx=10, pady=15)
        entry_start = ctk.CTkEntry(filter_frame, width=120)
        entry_start.insert(0, datetime.now().strftime("%Y-%m-%d"))
        entry_start.pack(side="left")

        ctk.CTkLabel(filter_frame, text="Đến:", font=("Arial", 12, "bold")).pack(side="left", padx=10, pady=15)
        entry_end = ctk.CTkEntry(filter_frame, width=120)
        entry_end.insert(0, datetime.now().strftime("%Y-%m-%d"))
        entry_end.pack(side="left")

        dash = ctk.CTkFrame(report_win, fg_color="transparent")
        dash.pack(fill="x", padx=20)

        def make_card(parent, title, color):
            card = ctk.CTkFrame(parent, fg_color="white", corner_radius=10, border_width=1, border_color="#E2E8F0",
                                height=80)
            card.pack(side="left", expand=True, fill="x", padx=5)
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=title, font=("Arial", 12, "bold"), text_color="#64748B").pack(pady=(10, 0))
            lbl = ctk.CTkLabel(card, text="0", font=("Arial", 20, "bold"), text_color=color)
            lbl.pack()
            return lbl

        lb_revenue = make_card(dash, "💰 DOANH THU", "#10B981")
        lb_orders = make_card(dash, "🧾 HÓA ĐƠN", "#3B82F6")
        lb_products = make_card(dash, "📦 ĐÃ BÁN", "#F59E0B")

        tables_container = ctk.CTkFrame(report_win, fg_color="transparent")
        tables_container.pack(fill="both", expand=True, padx=15, pady=20)

        left_frame = ctk.CTkFrame(tables_container, fg_color="white", corner_radius=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(left_frame, text="DOANH THU THEO NGÀY", font=("Arial", 12, "bold"), text_color="#0F172A").pack(
            pady=(10, 5))

        tree = ttk.Treeview(left_frame, columns=("date", "money"), show="headings")
        tree.heading("date", text="NGÀY")
        tree.column("date", width=120, anchor="center")
        tree.heading("money", text="DOANH THU")
        tree.column("money", width=180, anchor="e")
        tree.pack(fill="both", expand=True, padx=2, pady=2)

        right_frame = ctk.CTkFrame(tables_container, fg_color="white", corner_radius=10)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)
        ctk.CTkLabel(right_frame, text="🏆 TOP 5 SP BÁN CHẠY", font=("Arial", 12, "bold"), text_color="#0F172A").pack(
            pady=(10, 5))

        top_tree = ttk.Treeview(right_frame, columns=("name", "qty"), show="headings")
        top_tree.heading("name", text="TÊN SẢN PHẨM")
        top_tree.column("name", width=220, anchor="w")
        top_tree.heading("qty", text="ĐÃ BÁN")
        top_tree.column("qty", width=80, anchor="center")
        top_tree.pack(fill="both", expand=True, padx=2, pady=2)

        def load():
            for i in tree.get_children(): tree.delete(i)
            for i in top_tree.get_children(): top_tree.delete(i)

            start, end = entry_start.get(), entry_end.get()
            session = SessionLocal()
            try:
                start_dt = datetime.strptime(start, "%Y-%m-%d")
                end_dt = datetime.strptime(end + " 23:59:59", "%Y-%m-%d %H:%M:%S")

                orders = session.query(Order).filter(Order.created_at >= start_dt, Order.created_at <= end_dt,
                                                     Order.status == OrderStatusEnum.PAID).all()
                total_rev = sum(o.total_amount for o in orders)

                order_ids = [o.id for o in orders]
                items = session.query(OrderItem).filter(OrderItem.order_id.in_(order_ids)).all()
                total_products = sum(i.quantity for i in items)

                lb_revenue.configure(text=f"{total_rev:,.0f} đ")
                lb_orders.configure(text=str(len(orders)))
                lb_products.configure(text=str(total_products))

                rev_by_date = {}
                for o in orders:
                    d = o.created_at.strftime("%Y-%m-%d")
                    rev_by_date[d] = rev_by_date.get(d, 0) + o.total_amount
                for d_str, rev in sorted(rev_by_date.items()):
                    tree.insert("", tk.END, values=(d_str, f"{rev:,.0f} đ"))

                prod_qty = {}
                for item in items:
                    p_name = item.product.name if item.product else "SP Đã Xóa"
                    prod_qty[p_name] = prod_qty.get(p_name, 0) + item.quantity
                top_5 = sorted(prod_qty.items(), key=lambda x: x[1], reverse=True)[:5]
                for name, qty in top_5:
                    top_tree.insert("", tk.END, values=(name, qty))

            except Exception as e:
                messagebox.showerror("Lỗi", f"Dữ liệu ngày không hợp lệ: {e}", parent=report_win)
            finally:
                session.close()

        self.load_report_func = load
        ctk.CTkButton(filter_frame, text="TẢI DỮ LIỆU", fg_color="#2563EB", command=load).pack(side="right", padx=10)
        load()