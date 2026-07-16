from database.db_session import SessionLocal
from database.models import Product, Order, OrderItem, User, OrderStatusEnum, ItemStatusEnum
import uuid


class SalesController:
    def __init__(self):
        pass

    def get_available_products(self):
        session = SessionLocal()
        try:
            products = session.query(Product).filter(Product.is_active == True).all()
            return [(p.code, p.name, p.price, p.stock) for p in products]
        finally:
            session.close()

    def checkout(self, cashier_username, cart_items, total_amount):
        if not cart_items:
            return False, "Giỏ hàng rỗng!"

        session = SessionLocal()
        try:
            # 1. Tìm thông tin thu ngân
            cashier = session.query(User).filter_by(username=cashier_username).first()
            cashier_id = cashier.id if cashier else 1

            # 2. Kiểm tra tồn kho trước khi thanh toán
            for code, item in cart_items.items():
                product = session.query(Product).filter_by(code=code).first()
                if not product or product.stock < item['qty']:
                    return False, f"Sản phẩm '{product.name if product else code}' không đủ tồn kho!"

            # 3. Tạo ID hóa đơn duy nhất
            order_id = "HD-" + str(uuid.uuid4())[:8].upper()

            # 4. Lưu bảng hóa đơn chính (Order)
            new_order = Order(
                id=order_id,
                cashier_id=cashier_id,
                status=OrderStatusEnum.PAID,
                total_amount=total_amount,
                sub_total=total_amount
            )
            session.add(new_order)

            # 5. Trừ kho và lưu bảng chi tiết (OrderItem)
            for code, item in cart_items.items():
                product = session.query(Product).filter_by(code=code).first()
                product.stock -= item['qty']  # Trừ kho

                order_item = OrderItem(
                    order_id=order_id,
                    product_id=product.id,
                    quantity=item['qty'],
                    base_price=item['price'],
                    status=ItemStatusEnum.SERVED
                )
                session.add(order_item)

            session.commit()
            return True, order_id

        except Exception as e:
            session.rollback()
            return False, f"Lỗi hệ thống: {str(e)}"
        finally:
            session.close()
