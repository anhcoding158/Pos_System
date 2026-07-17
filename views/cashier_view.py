import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import qrcode
import os
import base64
import math
from datetime import datetime
from PIL import Image, ImageTk

from services.printer_service import PrinterService
from controllers.sales_controller import SalesController
from services.product_service import ProductService
from core.vietqr_logic import generate_vietqr_payload
from core.config_manager import ConfigManager


class CashierWindow:
    def __init__(self, root, username, on_logout_callback=None):
        self.root = root
        self.username = username
        self.on_logout_callback = on_logout_callback
        self.config = ConfigManager()

        self.root.title(f"Hệ Thống Bán Hàng POS Enterprise - [Thu ngân: {username}]")
        self.root.geometry("1300x800")
        self.root.minsize(1100, 700)
        ctk.set_appearance_mode("light")

        self.sales_ctrl = SalesController()
        self.cart = {}
        self.cart_ui_items = {}
        self.total_amount = 0
        self.current_bill_id = None
        self.products_db = []

        self.last_payment_method = "QR"
        self.last_cash_given = 0
        self.last_change_due = 0
        self.reset_timer = None

        self._build_ui()
        self.load_products()
        self.update_cart_ui()

    # ================= MODAL SẠCH SẼ =================
    def center_modal(self, window, width, height):
        self.root.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_rooty() + (self.root.winfo_height() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def create_modern_modal(self, title_text, width, height):
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
            modal.destroy()

        btn_close = ctk.CTkButton(header, text="✖", width=30, height=30, fg_color="transparent",
                                  hover_color="#FEE2E2", text_color="#EF4444", font=("Arial", 16),
                                  command=close_modal)
        btn_close.pack(side="right", padx=5)
        return modal

    # ================= HIỆU ỨNG BAY VÀO GIỎ HÀNG =================
    def play_add_animation(self, source_widget, code):
        try:
            start_x = source_widget.winfo_rootx() - self.root.winfo_rootx() + 40
            start_y = source_widget.winfo_rooty() - self.root.winfo_rooty() + 40
            target_x = self.right_panel.winfo_rootx() - self.root.winfo_rootx() + 50
            target_y = self.right_panel.winfo_rooty() - self.root.winfo_rooty() + 150

            if not hasattr(self, 'anim_images'): self.anim_images = {}
            anim_lbl = tk.Label(self.root, bd=0, bg="#F1F5F9")

            p = next((item for item in self.products_db if item[0] == code), None)

            # Ảnh nằm ở vị trí index 6
            if p and len(p) > 6 and p[6] and os.path.exists(p[6]):
                if code not in self.anim_images:
                    pil_img = Image.open(p[6]).resize((50, 50))
                    self.anim_images[code] = ImageTk.PhotoImage(pil_img)
                anim_lbl.configure(image=self.anim_images[code])
            else:
                anim_lbl.configure(text="🍔", font=("Arial", 24), bg="white")

            anim_lbl.place(x=start_x, y=start_y)
            anim_lbl.lift()

            steps = 20
            dx = (target_x - start_x) / steps
            dy = (target_y - start_y) / steps

            def move(step=0):
                if step <= steps:
                    curve = math.sin(math.pi * (step / steps)) * 100
                    anim_lbl.place(x=start_x + dx * step, y=start_y + dy * step - curve)
                    self.root.after(15, move, step + 1)
                else:
                    anim_lbl.destroy()

            move()
        except Exception:
            pass

    # ================= GIAO DIỆN CHÍNH =================
    def _build_ui(self):
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#F1F5F9")
        self.main_frame.pack(fill="both", expand=True)

        self.left_panel = ctk.CTkFrame(self.main_frame, fg_color="transparent", corner_radius=0)
        self.left_panel.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        self.right_panel = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=15, width=450, border_width=1,
                                        border_color="#E2E8F0")
        self.right_panel.pack(side="right", fill="y", padx=(0, 20), pady=20)
        self.right_panel.pack_propagate(False)

        self._build_left_panel()
        self._build_right_panel()

    def _build_left_panel(self):
        header_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="🏪", font=("Arial", 36)).pack(side="left", padx=(0, 10))

        text_box = ctk.CTkFrame(title_box, fg_color="transparent")
        text_box.pack(side="left")
        ctk.CTkLabel(text_box, text="SẢNH DỊCH VỤ", font=("Arial", 22, "bold"), text_color="#0F172A", anchor="w").pack(
            fill="x")
        ctk.CTkLabel(text_box, text="Đồng bộ danh mục tự động từ Admin", font=("Arial", 12), text_color="#64748B",
                     anchor="w").pack(fill="x")

        ctk.CTkButton(header_frame, text="🚪 Đăng xuất", fg_color="#EF4444", hover_color="#DC2626",
                      width=100, height=40, font=("Arial", 13, "bold"), command=self.logout).pack(side="right")

        search_frame = ctk.CTkFrame(self.left_panel, fg_color="white", corner_radius=10, border_width=1,
                                    border_color="#E2E8F0")
        search_frame.pack(fill="x", pady=(0, 15))

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 Gõ tên hoặc mã món để tìm kiếm nhanh...",
                                         font=("Arial", 15), height=50, fg_color="transparent", border_width=0)
        self.search_entry.pack(fill="x", padx=15, pady=5)
        self.search_entry.bind("<KeyRelease>", self.on_search)

        # NÂNG CẤP: Chuyển thanh danh mục thành Scrollable nằm ngang đề phòng Admin tạo quá nhiều danh mục
        self.category_frame = ctk.CTkScrollableFrame(self.left_panel, fg_color="transparent", height=50,
                                                     orientation="horizontal")
        self.category_frame.pack(fill="x", pady=(0, 15))
        self.category_buttons = []
        self.current_category = "Tất cả"

        self.product_grid = ctk.CTkScrollableFrame(self.left_panel, fg_color="transparent")
        self.product_grid.pack(fill="both", expand=True)

    def _build_right_panel(self):
        ctk.CTkLabel(self.right_panel, text="🛒 GIỎ HÀNG", font=("Arial", 18, "bold"), text_color="#1E293B").pack(
            pady=(20, 10))

        self.cart_scroll = ctk.CTkScrollableFrame(self.right_panel, fg_color="#F8FAFC", corner_radius=10)
        self.cart_scroll.pack(fill="both", expand=True, padx=15, pady=5)

        bottom_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=15, pady=15)

        total_frame = ctk.CTkFrame(bottom_frame, fg_color="#FFF7ED", corner_radius=10, border_width=1,
                                   border_color="#FED7AA")
        total_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(total_frame, text="TỔNG TIỀN:", font=("Arial", 14, "bold"), text_color="#EA580C").pack(side="left",
                                                                                                            padx=15,
                                                                                                            pady=15)
        self.lbl_total = ctk.CTkLabel(total_frame, text="0 đ", font=("Arial", 28, "bold"), text_color="#C2410C")
        self.lbl_total.pack(side="right", padx=15, pady=15)

        self.btn_checkout = ctk.CTkButton(bottom_frame, text="💰 THANH TOÁN ĐƠN", fg_color="#10B981",
                                          hover_color="#059669", height=60, font=("Arial", 16, "bold"),
                                          command=self.show_payment_modal)
        self.btn_checkout.pack(fill="x", pady=(0, 10))

        self.btn_print = ctk.CTkButton(bottom_frame, text="🖨️ IN HÓA ĐƠN ĐIỆN TỬ", fg_color="#0EA5E9",
                                       hover_color="#0284C7", height=50, font=("Arial", 14, "bold"), state="disabled",
                                       command=self.print_receipt)
        self.btn_print.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(bottom_frame, text="🔄 TẠO ĐƠN MỚI", fg_color="#F97316", hover_color="#EA580C", height=45,
                      font=("Arial", 14, "bold"), command=self.clear_for_new_order).pack(fill="x", pady=(0, 15))

        self.status_border = ctk.CTkFrame(bottom_frame, fg_color="#F8FAFC", border_width=2, border_color="#E2E8F0",
                                          corner_radius=10, height=120)
        self.status_border.pack(fill="x")
        self.status_border.pack_propagate(False)
        self.lbl_status = ctk.CTkLabel(self.status_border, text="⏳\nChưa chốt đơn", text_color="#94A3B8",
                                       font=("Arial", 14, "bold"))
        self.lbl_status.pack(expand=True)

    # NÂNG CẤP: Dựa vào tên Danh Mục xịn để gắn icon và màu sắc cho đẹp mắt
    def get_category_theme(self, cat_name):
        cat_lower = cat_name.lower()
        if any(k in cat_lower for k in ['uống', 'trà', 'cafe', 'cà phê', 'bia', 'nước']):
            return "🍹", "#E0F2FE", "#BAE6FD", "#0369A1"
        elif any(k in cat_lower for k in ['ăn', 'mỳ', 'cơm', 'phở', 'bún', 'lẩu', 'nướng']):
            return "🍔", "#FEE2E2", "#FECACA", "#B91C1C"
        elif any(k in cat_lower for k in ['kem', 'bánh', 'chè', 'tráng miệng', 'ngọt']):
            return "🍰", "#FEF3C7", "#FDE68A", "#B45309"
        else:
            return "📦", "#F1F5F9", "#E2E8F0", "#334155"

    def load_products(self):
        success, products = ProductService.get_all_active()
        if success:
            self.products_db = products
            self.build_dynamic_categories()  # NÂNG CẤP: Gọi hàm tự động tạo Nút Danh Mục
        else:
            messagebox.showerror("Lỗi", "Không thể tải danh sách sản phẩm!")

    def build_dynamic_categories(self):
        # 1. Xóa sạch các nút cũ (nếu có)
        for widget in self.category_frame.winfo_children():
            widget.destroy()
        self.category_buttons = []

        # 2. THUẬT TOÁN MỚI: Lọc Danh mục trực tiếp từ các sản phẩm đang TỒN TẠI
        # self.products_db chứa (code, name, cat_name, price, stock, img_path) -> cat_name ở vị trí số 2
        active_cats = set()  # Dùng set để tự động loại bỏ các danh mục bị trùng tên
        for p in self.products_db:
            if len(p) > 2 and p[2]:
                active_cats.add(p[2])

        # Chuyển set thành list và sắp xếp theo bảng chữ cái ABC cho đẹp
        sorted_cats = sorted(list(active_cats))

        # Thêm nút "Tất cả" lên đầu tiên
        categories = ["Tất cả"] + sorted_cats

        # 3. Tạo nút động
        for cat in categories:
            icon, _, _, _ = self.get_category_theme(cat)
            display_text = "Tất cả" if cat == "Tất cả" else f"{icon} {cat}"

            btn = ctk.CTkButton(self.category_frame, text=display_text, font=("Arial", 14, "bold"),
                                fg_color="#E2E8F0", text_color="#475569", hover_color="#CBD5E1",
                                height=40, corner_radius=20,
                                command=lambda c=cat: self.filter_by_category(c))
            btn.pack(side="left", padx=(0, 10))
            self.category_buttons.append(btn)

        # Ép chọn lại danh mục hiện tại (hoặc về "Tất cả" nếu danh mục cũ vừa bị bốc hơi)
        self.filter_by_category(self.current_category if self.current_category in categories else "Tất cả")

    def filter_by_category(self, category):
        self.current_category = category
        for btn in self.category_buttons:
            # So sánh chuỗi text của nút (cần bỏ bớt icon nếu có)
            btn_cat_name = btn.cget("text").split(" ", 1)[-1] if " " in btn.cget("text") and btn.cget(
                "text") != "Tất cả" else btn.cget("text")

            if btn_cat_name == category:
                btn.configure(fg_color="#10B981", text_color="white", hover_color="#059669")
            else:
                btn.configure(fg_color="#E2E8F0", text_color="#475569", hover_color="#CBD5E1")
        self.on_search(None)

    def on_search(self, event=None):
        keyword = self.search_entry.get().strip().lower()
        filtered = []
        for p in self.products_db:
            # p = (code, name, category, cost_price, price, stock, img_path)
            code, name, cat_name, price, stock = p[0], p[1], p[2], p[4], p[5]

            match_text = keyword in code.lower() or keyword in name.lower() if keyword else True
            # NÂNG CẤP: Lọc CHUẨN XÁC theo Danh Mục từ Database, không đoán mò nữa
            match_cat = True if self.current_category == "Tất cả" else cat_name == self.current_category

            if match_text and match_cat:
                filtered.append(p)

        self.last_filtered_data = filtered
        self.populate_grid(filtered)

    # ================= GRID SẢN PHẨM KHÔNG BAO GIỜ GIẬT LAG =================
    def populate_grid(self, data_list):
        for widget in self.product_grid.winfo_children(): widget.destroy()
        row, col = 0, 0
        max_cols = 4

        if not hasattr(self, 'img_cache'): self.img_cache = {}

        self.stock_labels = {}
        self.card_frames = {}

        for p in data_list:
            code, name, cat_name, price, stock = p[0], p[1], p[2], p[4], p[5]
            img_path = p[6] if len(p) > 6 else ""
            icon, bg_color, hover_color, text_color = self.get_category_theme(cat_name)

            in_cart_qty = self.cart.get(code, {}).get('qty', 0)
            real_stock = stock - in_cart_qty
            is_out_of_stock = real_stock <= 0

            card = ctk.CTkFrame(self.product_grid, fg_color="white", corner_radius=12, border_width=2,
                                border_color="#E2E8F0", width=180, height=225)
            card.pack_propagate(False)
            card.grid(row=row, column=col, padx=10, pady=12)

            img_frame = ctk.CTkFrame(card, fg_color="transparent", height=100)
            img_frame.pack(pady=(15, 0))

            if img_path and os.path.exists(img_path):
                if code not in self.img_cache:
                    pil_img = Image.open(img_path)
                    self.img_cache[code] = ctk.CTkImage(light_image=pil_img, size=(100, 100))
                tk_img = self.img_cache[code]
            else:
                tk_img = ctk.CTkImage(light_image=Image.new('RGB', (100, 100), color='#F1F5F9'), size=(100, 100))

            img_lbl = ctk.CTkLabel(img_frame, image=tk_img, text="")
            img_lbl.pack()

            name_lbl = ctk.CTkLabel(card, text=name[:18], font=("Arial", 14, "bold"), text_color="#0F172A")
            name_lbl.pack(pady=(5, 0))

            if is_out_of_stock:
                price_lbl = ctk.CTkLabel(card, text="[HẾT HÀNG]", font=("Arial", 13, "bold"), text_color="#EF4444")
                card.configure(fg_color="#F8FAFC")
            else:
                price_lbl = ctk.CTkLabel(card, text=f"{price:,.0f} ₫\n(Còn: {real_stock})", font=("Arial", 14, "bold"),
                                         text_color="#059669")

                cmd = lambda e, c=code, w=card: self.add_to_cart(c, w)
                card.bind("<Button-1>", cmd)
                img_frame.bind("<Button-1>", cmd)
                img_lbl.bind("<Button-1>", cmd)
                name_lbl.bind("<Button-1>", cmd)
                price_lbl.bind("<Button-1>", cmd)

                card.bind("<Enter>", lambda e, c=card: c.configure(border_color="#3B82F6"))
                card.bind("<Leave>", lambda e, c=card: c.configure(border_color="#E2E8F0"))

            price_lbl.pack()

            self.stock_labels[code] = price_lbl
            self.card_frames[code] = card

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def update_grid_stocks_in_place(self):
        if not hasattr(self, 'stock_labels'): return

        for p in getattr(self, 'last_filtered_data', self.products_db):
            code, price, stock = p[0], p[4], p[5]
            in_cart_qty = self.cart.get(code, {}).get('qty', 0)
            real_stock = stock - in_cart_qty

            if code in self.stock_labels:
                lbl = self.stock_labels[code]
                card = self.card_frames[code]

                if real_stock <= 0:
                    lbl.configure(text="[HẾT HÀNG]", text_color="#EF4444")
                    card.configure(fg_color="#F8FAFC", border_color="#E2E8F0")
                else:
                    lbl.configure(text=f"{price:,.0f} ₫\n(Còn: {real_stock})", text_color="#059669")
                    card.configure(fg_color="white")

    # ================= LOGIC GIỎ HÀNG =================
    def add_to_cart(self, code, source_widget=None):
        if getattr(self, 'reset_timer', None):
            self.root.after_cancel(self.reset_timer)
            self.reset_timer = None

        p = next((item for item in self.products_db if item[0] == code), None)
        if not p: return

        stock = p[5]
        current_qty = self.cart.get(code, {}).get('qty', 0)
        if current_qty + 1 > stock:
            messagebox.showwarning("Hết hàng", f"Món '{p[1]}' chỉ còn tối đa {stock} phần!")
            return

        if source_widget:
            self.play_add_animation(source_widget, code)

        if code in self.cart:
            self.cart[code]['qty'] += 1
        else:
            self.cart[code] = {'name': p[1], 'price': p[4], 'qty': 1}
        self.update_cart_ui()

    def change_qty(self, code, amount):
        if code not in self.cart: return
        new_qty = self.cart[code]['qty'] + amount

        if new_qty <= 0:
            del self.cart[code]
        else:
            p = next((item for item in self.products_db if item[0] == code), None)
            if p and new_qty > p[5]:
                messagebox.showwarning("Hết hàng", f"Món '{p[1]}' chỉ còn tối đa {p[5]} phần!")
                return
            self.cart[code]['qty'] = new_qty

        self.update_cart_ui()

    def update_cart_ui(self):
        if not hasattr(self, 'cart_scroll') or not self.cart_scroll.winfo_exists():
            return

        codes_in_cart = set(self.cart.keys())
        for code in list(self.cart_ui_items.keys()):
            if code not in codes_in_cart:
                self.cart_ui_items[code]['frame'].destroy()
                del self.cart_ui_items[code]

        self.total_amount = 0

        if not self.cart:
            if not hasattr(self, 'empty_cart_frame') or not self.empty_cart_frame.winfo_exists():
                self.empty_cart_frame = ctk.CTkFrame(self.cart_scroll, fg_color="transparent")
                self.empty_cart_frame.pack(expand=True, fill="both", pady=50)
                ctk.CTkLabel(self.empty_cart_frame, text="🛒", font=("Arial", 50), text_color="#CBD5E1").pack()
                ctk.CTkLabel(self.empty_cart_frame, text="Giỏ hàng trống", font=("Arial", 18, "bold"),
                             text_color="#94A3B8").pack(pady=(10, 5))
                ctk.CTkLabel(self.empty_cart_frame, text="Vui lòng chọn món ở danh sách bên trái", font=("Arial", 13),
                             text_color="#94A3B8").pack()

            if hasattr(self, 'lbl_total') and self.lbl_total.winfo_exists():
                self.lbl_total.configure(text="0 đ")

            self.update_grid_stocks_in_place()
            return
        else:
            if hasattr(self, 'empty_cart_frame') and self.empty_cart_frame.winfo_exists():
                self.empty_cart_frame.destroy()

        for code, item in self.cart.items():
            total = item['price'] * item['qty']
            self.total_amount += total

            if code in self.cart_ui_items:
                self.cart_ui_items[code]['lbl_qty'].configure(text=str(item['qty']))
                self.cart_ui_items[code]['lbl_price'].configure(text=f"{total:,.0f} đ")
            else:
                item_card = ctk.CTkFrame(self.cart_scroll, fg_color="white", corner_radius=8, border_width=1,
                                         border_color="#E2E8F0")
                item_card.pack(fill="x", pady=4, padx=2)

                btn_del = ctk.CTkButton(item_card, text="✖", width=30, height=30, corner_radius=6,
                                        fg_color="#FEE2E2", text_color="#EF4444", hover_color="#FECACA",
                                        font=("Arial", 14, "bold"), command=lambda c=code: self.remove_item(c))
                btn_del.pack(side="left", padx=(10, 0))

                info_frame = ctk.CTkFrame(item_card, fg_color="transparent")
                info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=8)
                ctk.CTkLabel(info_frame, text=item['name'], font=("Arial", 14, "bold"), text_color="#1E293B",
                             anchor="w").pack(fill="x")

                lbl_price = ctk.CTkLabel(info_frame, text=f"{total:,.0f} đ", font=("Arial", 12), text_color="#64748B",
                                         anchor="w")
                lbl_price.pack(fill="x")

                qty_frame = ctk.CTkFrame(item_card, fg_color="transparent")
                qty_frame.pack(side="right", padx=10)

                ctk.CTkButton(qty_frame, text="-", width=28, height=28, fg_color="#F1F5F9", text_color="#0F172A",
                              hover_color="#E2E8F0", font=("Arial", 14, "bold"),
                              command=lambda c=code: self.change_qty(c, -1)).pack(side="left")
                lbl_qty = ctk.CTkLabel(qty_frame, text=str(item['qty']), font=("Arial", 14, "bold"), width=30)
                lbl_qty.pack(side="left", padx=5)
                ctk.CTkButton(qty_frame, text="+", width=28, height=28, fg_color="#F1F5F9", text_color="#0F172A",
                              hover_color="#E2E8F0", font=("Arial", 14, "bold"),
                              command=lambda c=code: self.change_qty(c, 1)).pack(side="left")

                self.cart_ui_items[code] = {
                    'frame': item_card,
                    'lbl_qty': lbl_qty,
                    'lbl_price': lbl_price
                }

        if hasattr(self, 'lbl_total') and self.lbl_total.winfo_exists():
            self.lbl_total.configure(text=f"{self.total_amount:,.0f} đ")

        self.update_grid_stocks_in_place()

    def remove_item(self, code):
        if code in self.cart:
            del self.cart[code]
            self.update_cart_ui()

    # ================= MÀN HÌNH THANH TOÁN =================
    def show_payment_modal(self):
        if not self.cart:
            messagebox.showwarning("Trống", "Giỏ hàng đang trống!")
            return

        self.pay_win = self.create_modern_modal("Xác Nhận Thanh Toán", 550, 650)

        ctk.CTkLabel(self.pay_win, text="💰 TỔNG CẦN THANH TOÁN", font=("Arial", 16, "bold"), text_color="#64748B").pack(
            pady=(25, 5))
        ctk.CTkLabel(self.pay_win, text=f"{self.total_amount:,.0f} VNĐ", font=("Arial", 38, "bold"),
                     text_color="#EA580C").pack(pady=(0, 20))

        self.pay_tabs = ctk.CTkTabview(self.pay_win, width=450, height=350, fg_color="white",
                                       segmented_button_selected_color="#10B981",
                                       segmented_button_selected_hover_color="#059669")
        self.pay_tabs.pack(padx=20, pady=10, fill="both", expand=True)

        tab_cash = self.pay_tabs.add("💵 Khách Trả Tiền Mặt")
        tab_qr = self.pay_tabs.add("📱 Khách Quét VietQR")

        # --- GIAO DIỆN TAB: TIỀN MẶT ---
        ctk.CTkLabel(tab_cash, text="Số tiền khách đưa:", font=("Arial", 15)).pack(anchor="w", padx=20, pady=(20, 5))

        self.entry_cash = ctk.CTkEntry(tab_cash, font=("Arial", 24, "bold"), height=50, justify="right")
        self.entry_cash.pack(fill="x", padx=20)
        self.entry_cash.insert(0, f"{self.total_amount:,.0f}")
        self.entry_cash.bind("<KeyRelease>", self.format_cash_input)

        self.quick_frame = ctk.CTkFrame(tab_cash, fg_color="transparent")
        self.quick_frame.pack(fill="x", padx=20, pady=15)

        self.update_cash_suggestions(self.total_amount)

        change_frame = ctk.CTkFrame(tab_cash, fg_color="#ECFDF5", corner_radius=8, border_color="#A7F3D0",
                                    border_width=1)
        change_frame.pack(fill="x", padx=20, pady=(15, 0))
        ctk.CTkLabel(change_frame, text="Tiền thừa trả khách:", font=("Arial", 15, "bold"), text_color="#047857").pack(
            side="left", padx=15, pady=20)
        self.lbl_change = ctk.CTkLabel(change_frame, text="0 đ", font=("Arial", 24, "bold"), text_color="#059669")
        self.lbl_change.pack(side="right", padx=15, pady=20)

        # --- GIAO DIỆN TAB: QUÉT QR ---
        secure_qr = self.config.get("payment", "secure_qr_code")
        base_qr = None
        if secure_qr:
            try:
                base_qr = base64.b64decode(secure_qr).decode('utf-8')
            except:
                pass
        if not base_qr: base_qr = "00020101021238580010A000000727012700069704220113VNPAY123456780208QRIBFTTA5303704540450005802VN6304"

        payload = generate_vietqr_payload(base_qr, int(self.total_amount))
        img = qrcode.make(payload).convert("RGB").resize((230, 230))
        tk_qr_img = ctk.CTkImage(light_image=img, dark_image=img, size=(230, 230))

        ctk.CTkLabel(tab_qr, image=tk_qr_img, text="").pack(pady=(15, 10))
        ctk.CTkLabel(tab_qr, text="Đưa mã này cho khách hàng quét để thanh toán", font=("Arial", 13, "italic"),
                     text_color="#64748B").pack()

        self.btn_confirm_pay = ctk.CTkButton(self.pay_win, text="✅ HOÀN TẤT & CHỐT ĐƠN", height=55,
                                             font=("Arial", 16, "bold"), fg_color="#10B981", hover_color="#059669",
                                             command=self.process_payment)
        self.btn_confirm_pay.pack(fill="x", padx=20, pady=20)

    def format_cash_input(self, event):
        if event.keysym in ('Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Tab'):
            return

        raw_val = self.entry_cash.get().replace(",", "").strip()
        if not raw_val:
            self.update_cash_suggestions(0)
            self.calculate_change()
            return

        if not raw_val.isdigit():
            self.entry_cash.delete(0, 'end')
            self.entry_cash.insert(0, raw_val[:-1])
            self.entry_cash.icursor(ctk.END)
            return

        val = int(raw_val)
        self.entry_cash.delete(0, 'end')
        self.entry_cash.insert(0, f"{val:,.0f}")
        self.entry_cash.icursor(ctk.END)

        self.update_cash_suggestions(val)
        self.calculate_change()

    def update_cash_suggestions(self, current_val):
        for widget in self.quick_frame.winfo_children(): widget.destroy()

        if current_val == 0:
            suggestions = [self.total_amount, 50000, 100000, 500000]
        else:
            suggestions = [current_val * 10, current_val * 100, current_val * 1000]
            suggestions.append(self.total_amount)

        def set_cash(amount):
            self.entry_cash.delete(0, 'end')
            self.entry_cash.insert(0, f"{amount:,.0f}")
            self.entry_cash.icursor(ctk.END)
            self.update_cash_suggestions(amount)
            self.calculate_change()

        for sug in suggestions[:4]:
            text_disp = "Vừa đủ" if sug == self.total_amount and current_val != self.total_amount else f"{sug:,.0f}"
            btn = ctk.CTkButton(self.quick_frame, text=text_disp, width=80,
                                fg_color="#DBEAFE" if text_disp != "Vừa đủ" else "#F1F5F9",
                                text_color="#1D4ED8" if text_disp != "Vừa đủ" else "#0F172A",
                                hover_color="#BFDBFE", command=lambda s=sug: set_cash(s))
            btn.pack(side="left", expand=True, padx=2)

    def calculate_change(self, event=None):
        try:
            raw_val = self.entry_cash.get().replace(",", "").strip()
            given = float(raw_val) if raw_val else 0
            change = given - self.total_amount
            if change < 0:
                self.lbl_change.configure(text="Thiếu tiền!", text_color="#EF4444")
                self.btn_confirm_pay.configure(state="disabled")
            else:
                self.lbl_change.configure(text=f"{change:,.0f} đ", text_color="#059669")
                self.btn_confirm_pay.configure(state="normal")
        except ValueError:
            self.lbl_change.configure(text="Lỗi nhập số", text_color="#EF4444")
            self.btn_confirm_pay.configure(state="disabled")

    def process_payment(self):
        if self.pay_tabs.get() == "💵 Khách Trả Tiền Mặt":
            try:
                given = float(self.entry_cash.get().replace(",", ""))
                if given < self.total_amount:
                    messagebox.showerror("Lỗi", "Khách đưa chưa đủ tiền!", parent=self.pay_win)
                    return
                self.last_payment_method = "CASH"
                self.last_cash_given = given
                self.last_change_due = given - self.total_amount
            except ValueError:
                messagebox.showerror("Lỗi", "Số tiền không hợp lệ!", parent=self.pay_win)
                return
        else:
            self.last_payment_method = "QR"
            self.last_cash_given = 0
            self.last_change_due = 0

        success, msg_or_id = self.sales_ctrl.checkout(self.username, self.cart, self.total_amount)
        if success:
            self.current_bill_id = msg_or_id
            self.btn_print.configure(state="normal")
            self.lbl_total.configure(text_color="#10B981")

            self.lbl_status.destroy()
            self.lbl_status = ctk.CTkLabel(self.status_border, text=f"✅ ĐÃ THANH TOÁN\nMã HĐ: {self.current_bill_id}",
                                           font=("Arial", 16, "bold"), text_color="#10B981")
            self.lbl_status.pack(expand=True)

            self.load_products()
            self.pay_win.destroy()

            if getattr(self, 'reset_timer', None):
                self.root.after_cancel(self.reset_timer)
            self.reset_timer = self.root.after(10000, self.clear_for_new_order)

            messagebox.showinfo("Thành công", f"Đã chốt đơn thành công!\nBạn có thể in hóa đơn ngay.", parent=self.root)
        else:
            messagebox.showerror("Lỗi thanh toán", msg_or_id, parent=self.pay_win)

    # ================= IN HÓA ĐƠN & TẠO ĐƠN MỚI =================
    def print_receipt(self):
        if not self.current_bill_id or not self.cart: return

        secure_qr = self.config.get("payment", "secure_qr_code")
        base_qr = None
        if secure_qr:
            try:
                base_qr = base64.b64decode(secure_qr).decode('utf-8')
            except:
                pass

        payload = None
        if base_qr:
            from core.vietqr_logic import generate_vietqr_payload
            payload = generate_vietqr_payload(base_qr, int(self.total_amount))

        try:
            image_path = PrinterService.generate_receipt_image(
                bill_id=self.current_bill_id,
                cashier_name=self.username,
                cart_items=self.cart,
                total_amount=self.total_amount,
                qr_payload=payload,
                payment_method=getattr(self, 'last_payment_method', 'QR'),
                cash_given=getattr(self, 'last_cash_given', 0),
                change_due=getattr(self, 'last_change_due', 0)
            )
        except Exception as e:
            messagebox.showerror("Lỗi in", f"Không thể tạo ảnh hóa đơn: {e}")
            return

        preview_win = self.create_modern_modal(f"Hóa Đơn Điện Tử - {self.current_bill_id}", 500, 750)

        pil_image = Image.open(image_path)
        preview_width = 450
        ratio = preview_width / float(pil_image.width)
        preview_height = int(float(pil_image.height) * ratio)
        pil_image_resized = pil_image.resize((preview_width, preview_height))

        ctk_img = ctk.CTkImage(light_image=pil_image_resized, dark_image=pil_image_resized,
                               size=(preview_width, preview_height))

        scroll_frame = ctk.CTkScrollableFrame(preview_win, fg_color="#F1F5F9")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        lbl_img = ctk.CTkLabel(scroll_frame, image=ctk_img, text="")
        lbl_img.pack(pady=10, anchor="center")

        def mock_print():
            messagebox.showinfo("Hoàn tất", f"Đã đẩy lệnh in thành công tới máy in K80!\nFile lưu tại: {image_path}",
                                parent=preview_win)
            preview_win.destroy()

        ctk.CTkButton(preview_win, text="🖨️ XUẤT RA MÁY IN NHIỆT", font=("Arial", 16, "bold"),
                      height=55, fg_color="#10B981", hover_color="#059669", command=mock_print).pack(fill="x", padx=10,
                                                                                                     pady=(0, 10))

        if getattr(self, 'reset_timer', None):
            self.root.after_cancel(self.reset_timer)
        self.reset_timer = self.root.after(10000, self.clear_for_new_order)

    def clear_for_new_order(self):
        if getattr(self, 'reset_timer', None):
            self.root.after_cancel(self.reset_timer)
            self.reset_timer = None

        self.cart = {}
        if hasattr(self, 'cart_ui_items'):
            for item in self.cart_ui_items.values():
                item['frame'].destroy()
            self.cart_ui_items.clear()

        if hasattr(self, 'cart_scroll') and self.cart_scroll.winfo_exists():
            self.update_cart_ui()
            self.last_payment_method = "QR"
            self.last_cash_given = 0
            self.last_change_due = 0

            if hasattr(self, 'lbl_status') and self.lbl_status.winfo_exists():
                self.lbl_status.destroy()
            self.lbl_status = ctk.CTkLabel(self.status_border, text="⏳\nĐang chờ chốt đơn", text_color="#94A3B8",
                                           font=("Arial", 14, "bold"))
            self.lbl_status.pack(expand=True)

            self.btn_print.configure(state="disabled")
            self.search_entry.delete(0, 'end')
            self.load_products()
            self.lbl_total.configure(text_color="#C2410C")

    def logout(self):
        if getattr(self, 'reset_timer', None):
            self.root.after_cancel(self.reset_timer)
            self.reset_timer = None
        if self.on_logout_callback:
            self.on_logout_callback()