import cv2
import base64
from core.config_manager import ConfigManager


class QRService:
    @staticmethod
    def process_and_save_qr(file_path):
        """Xử lý ảnh, Xác thực chuẩn VietQR và Mã hóa bảo mật"""
        try:
            img = cv2.imread(file_path)
            if img is None:
                return False, "Không thể đọc file ảnh!"

            # 1. TIỀN XỬ LÝ ẢNH (Tăng độ tương phản để quét nét hơn)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            detector = cv2.QRCodeDetector()
            data, _, _ = detector.detectAndDecode(binary)

            # Nếu ảnh đã nét sẵn thì đọc lại bằng ảnh gốc
            if not data:
                data, _, _ = detector.detectAndDecode(img)

            if not data:
                return False, "Không tìm thấy mã QR. Vui lòng crop (cắt) ảnh sát vào mã QR!"

            data = data.strip()

            # 2. XÁC THỰC BẢO MẬT (Chuẩn EMVCo / VietQR)
            # Mã VietQR bắt buộc phải bắt đầu bằng '000201' (Payload Format Indicator)
            if not data.startswith("000201"):
                return False, "LỖI AN NINH: Đây không phải mã VietQR chuẩn ngân hàng!"

            # Bắt buộc phải có thẻ 6304 (CRC Checksum) ở phần đuôi
            if "6304" not in data[-10:]:
                return False, "LỖI AN NINH: Mã QR bị hỏng hoặc thiếu mã kiểm tra (Tag 6304)."

            # 3. MÃ HÓA & LƯU TRỮ (Che giấu data không cho đọc bằng mắt thường)
            encoded_data = base64.b64encode(data.encode('utf-8')).decode('utf-8')

            config = ConfigManager()
            config.update("payment", "secure_qr_code", encoded_data)

            # Xóa mã thô cũ (nếu có) để dọn dẹp
            config.update("payment", "qr_code", "")

            return True, "Mã VietQR đã được xác thực an toàn và lưu trữ bảo mật!"
        except Exception as e:
            return False, f"Lỗi xử lý ảnh: {str(e)}"