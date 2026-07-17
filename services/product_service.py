import os
import shutil
from database.db_session import SessionLocal
from database.models import Product, Category

# Tạo thư mục chứa ảnh nếu chưa có
ASSETS_DIR = "assets/products"
os.makedirs(ASSETS_DIR, exist_ok=True)


class ProductService:
    @staticmethod
    def get_all_categories():
        session = SessionLocal()
        try:
            cats = session.query(Category).all()
            return [c.name for c in cats]
        finally:
            session.close()

    @staticmethod
    def _get_or_create_category(session, cat_name):
        if not cat_name:
            return None
        cat = session.query(Category).filter_by(name=cat_name).first()
        if not cat:
            cat = Category(name=cat_name)
            session.add(cat)
            session.commit()
        return cat.id

    @staticmethod
    def get_all_active():
        session = SessionLocal()
        try:
            products = session.query(Product).filter(Product.is_active == True).order_by(Product.code).all()
            # Cập nhật thêm trường category_name và cost_price
            result = []
            for p in products:
                cat_name = p.category.name if p.category else "Khác"
                result.append((p.code, p.name, cat_name, p.cost_price, p.price, p.stock, p.image_path))
            return True, result
        except Exception as e:
            return False, f"Lỗi truy xuất CSDL: {e}"
        finally:
            session.close()

    @staticmethod
    def _save_image(source_path, code):
        """Hàm nội bộ: Copy ảnh vào thư mục hệ thống và đổi tên theo mã SP"""
        if not source_path or not os.path.exists(source_path):
            return ""

        ext = os.path.splitext(source_path)[1]
        dest_filename = f"{code}{ext}"
        dest_path = os.path.join(ASSETS_DIR, dest_filename)

        try:
            shutil.copy2(source_path, dest_path)
            return dest_path
        except Exception as e:
            print(f"Lỗi lưu ảnh: {e}")
            return ""

    @staticmethod
    def add_product(code, name, category_name, cost_price, price, stock, image_source=""):
        session = SessionLocal()
        try:
            product = session.query(Product).filter_by(code=code).first()
            saved_image_path = ProductService._save_image(image_source, code) if image_source else ""
            cat_id = ProductService._get_or_create_category(session, category_name)

            if product:
                if product.is_active:
                    return False, "Mã sản phẩm đã tồn tại!"
                else:
                    product.name = name
                    product.category_id = cat_id
                    product.cost_price = cost_price
                    product.price = price
                    product.stock = stock
                    product.is_active = True
                    if saved_image_path: product.image_path = saved_image_path
                    session.commit()
                    return True, "Khôi phục và cập nhật SP thành công!"

            new_product = Product(
                code=code, name=name, category_id=cat_id,
                cost_price=cost_price, price=price, stock=stock,
                is_active=True, image_path=saved_image_path
            )
            session.add(new_product)
            session.commit()
            return True, "Thêm sản phẩm mới thành công!"
        except Exception as e:
            session.rollback()
            return False, f"Lỗi hệ thống: {e}"
        finally:
            session.close()

    @staticmethod
    def update_product(code, name, category_name, cost_price, price, stock, image_source=""):
        session = SessionLocal()
        try:
            product = session.query(Product).filter(Product.code == code, Product.is_active == True).first()
            if not product: return False, "Không tìm thấy sản phẩm!"

            cat_id = ProductService._get_or_create_category(session, category_name)

            product.name = name
            product.category_id = cat_id
            product.cost_price = cost_price
            product.price = price
            product.stock = stock

            if image_source and os.path.exists(image_source):
                saved_image_path = ProductService._save_image(image_source, code)
                product.image_path = saved_image_path

            session.commit()
            return True, "Cập nhật thành công!"
        except Exception as e:
            session.rollback()
            return False, f"Lỗi: {e}"
        finally:
            session.close()

    @staticmethod
    def soft_delete_product(code):
        session = SessionLocal()
        try:
            product = session.query(Product).filter(Product.code == code, Product.is_active == True).first()
            if not product: return False, "Không tìm thấy sản phẩm!"

            product.is_active = False
            session.commit()
            return True, "Đã xóa sản phẩm!"
        except Exception as e:
            session.rollback()
            return False, f"Lỗi: {e}"
        finally:
            session.close()