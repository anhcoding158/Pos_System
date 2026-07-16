import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import qrcode
from core.config_manager import ConfigManager

class PrinterService:
    @staticmethod
    def generate_receipt_image(bill_id, cashier_name, cart_items, total_amount, qr_payload=None, payment_method="QR", cash_given=0, change_due=0):
        """
        Vẽ hóa đơn: Tự động thay đổi bố cục tùy theo Hình thức thanh toán (Tiền mặt / QR)
        """
        config = ConfigManager()
        store_name = config.get("store_info", "name") or "POS ENTERPRISE F&B"
        store_addr = config.get("store_info", "address") or "Địa chỉ cửa hàng"

        # Kích thước chuẩn máy in nhiệt K80
        W = 576
        H = 1600 + (len(cart_items) * 60)

        img = Image.new('RGB', (W, H), color='white')
        draw = ImageDraw.Draw(img)

        try:
            font_title = ImageFont.truetype("arialbd.ttf", 34)
            font_bold = ImageFont.truetype("arialbd.ttf", 22)
            font_norm = ImageFont.truetype("arial.ttf", 22)
            font_small = ImageFont.truetype("arial.ttf", 18)
        except IOError:
            font_title = font_bold = font_norm = font_small = ImageFont.load_default()

        def get_text_width(text, font):
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0]

        def draw_text_center(y, text, font, fill="black"):
            tw = get_text_width(text, font)
            draw.text(((W - tw) / 2, y), text, fill=fill, font=font)
            return y + font.size + 5

        def draw_text_lr(y, left_text, right_text, font):
            draw.text((20, y), left_text, fill="black", font=font)
            rw = get_text_width(right_text, font)
            draw.text((W - 20 - rw, y), right_text, fill="black", font=font)

        # --- BẮT ĐẦU VẼ HÓA ĐƠN ---
        y_pos = 20

        # 1. Header
        y_pos = draw_text_center(y_pos, store_name.upper(), font_title)
        y_pos += 15
        y_pos = draw_text_center(y_pos, store_addr, font_norm)
        y_pos += 10
        y_pos = draw_text_center(y_pos, "-" * 55, font_norm)
        y_pos += 10

        # 2. Thông tin Bill
        time_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        draw_text_lr(y_pos, f"Ngày: {time_str[:10]}", f"Giờ: {time_str[11:]}", font_norm)
        y_pos += 35
        draw_text_lr(y_pos, f"Thu ngân: {cashier_name[:15]}", f"Mã HĐ: {bill_id[-8:]}", font_norm)
        y_pos += 35
        y_pos = draw_text_center(y_pos, "=" * 55, font_norm)
        y_pos += 10

        # 3. Tiêu đề Cột
        draw.text((20, y_pos), "TÊN MÓN", font=font_bold, fill="black")
        draw.text((320, y_pos), "SL", font=font_bold, fill="black")
        rw = get_text_width("THÀNH TIỀN", font_bold)
        draw.text((W - 20 - rw, y_pos), "THÀNH TIỀN", font=font_bold, fill="black")
        y_pos += 35
        y_pos = draw_text_center(y_pos, "-" * 55, font_norm)
        y_pos += 10

        # 4. Chi tiết Món ăn
        for code, item in cart_items.items():
            name = item['name']
            if len(name) > 20: name = name[:18] + ".."
            qty = str(item['qty'])
            total = f"{item['qty'] * item['price']:,.0f}"

            draw.text((20, y_pos), name, font=font_norm, fill="black")
            draw.text((320, y_pos), qty, font=font_norm, fill="black")
            tw = get_text_width(total, font_norm)
            draw.text((W - 20 - tw, y_pos), total, font=font_norm, fill="black")
            y_pos += 40

        # 5. TỔNG CỘNG
        y_pos = draw_text_center(y_pos, "=" * 55, font_norm)
        y_pos += 10

        total_str = f"{total_amount:,.0f} VND"
        draw.text((20, y_pos), "TỔNG CỘNG:", font=font_title, fill="black")
        tw = get_text_width(total_str, font_title)
        draw.text((W - 20 - tw, y_pos), total_str, font=font_title, fill="black")
        y_pos += 50

        # --- KHÚC CUA CHÍNH: XỬ LÝ THEO HÌNH THỨC THANH TOÁN ---
        if payment_method == "CASH":
            # In tiền mặt
            cash_str = f"{cash_given:,.0f} VND"
            draw.text((20, y_pos), "Tiền khách đưa:", font=font_norm, fill="black")
            tw = get_text_width(cash_str, font_norm)
            draw.text((W - 20 - tw, y_pos), cash_str, font=font_norm, fill="black")
            y_pos += 35

            change_str = f"{change_due:,.0f} VND"
            draw.text((20, y_pos), "Tiền thừa:", font=font_bold, fill="black")
            tw = get_text_width(change_str, font_bold)
            draw.text((W - 20 - tw, y_pos), change_str, font=font_bold, fill="black")
            y_pos += 50
        else:
            # In chữ chuyển khoản & QR
            draw_text_lr(y_pos, "Hình thức:", "Chuyển khoản / QR", font_norm)
            y_pos += 50

            if qr_payload:
                y_pos = draw_text_center(y_pos, "QUÉT MÃ ĐỂ THANH TOÁN (VIETQR)", font_bold)
                y_pos += 15

                qr = qrcode.QRCode(box_size=10, border=2)
                qr.add_data(qr_payload)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")

                qr_img = qr_img.resize((350, 350))
                qr_x = int((W - 350) / 2)
                img.paste(qr_img, (qr_x, y_pos))
                y_pos += 370

        # 7. Footer
        y_pos = draw_text_center(y_pos, "CẢM ƠN QUÝ KHÁCH & HẸN GẶP LẠI!", font_bold)
        y_pos += 10
        y_pos = draw_text_center(y_pos, "Pass Wifi: 88888888", font_small)
        y_pos += 50

        img = img.crop((0, 0, W, y_pos))

        os.makedirs("receipts", exist_ok=True)
        file_path = f"receipts/Bill_{bill_id}.png"
        img.save(file_path)

        return file_path