def crc16_ccitt_false(data: str) -> str:
    """Thuật toán CRC16 chuẩn EMVCo (Đa thức 0x1021, giá trị khởi tạo 0xFFFF)"""
    crc = 0xFFFF
    for char in data:
        crc ^= ord(char) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
            crc &= 0xFFFF
    return f"{crc:04X}"


def generate_vietqr_payload(base_qr: str, amount: int) -> str:
    """Xử lý cắt đuôi CRC cũ, ghép Tag 54 (số tiền) và tính CRC mới"""
    base_qr = base_qr.strip()

    # Tìm kiếm Tag CRC "6304" ở cuối chuỗi
    if "6304" in base_qr[-8:]:
        core_string = base_qr[:-8]
    else:
        idx = base_qr.rfind("6304")
        if idx != -1:
            core_string = base_qr[:idx]
        else:
            raise ValueError("Mã QR tĩnh gốc của bạn không đúng định dạng VietQR chuẩn!")

    amount_str = str(amount)
    length_str = f"{len(amount_str):02d}"
    tag_54 = f"54{length_str}{amount_str}"

    payload_before_crc = core_string + tag_54 + "6304"
    new_crc = crc16_ccitt_false(payload_before_crc)
    return payload_before_crc + new_crc
