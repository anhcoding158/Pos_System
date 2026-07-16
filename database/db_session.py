import os
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from database.models import Base, User, RoleEnum

# Tương lai khi cài PostgreSQL, bạn chỉ cần thay dòng này:
# DATABASE_URL = "postgresql://postgres:matkhau@localhost:5432/pos_enterprise"

# Hiện tại, cứ để SQLite chạy test schema trước
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "pos_enterprise_v2.db")
DATABASE_URL = f"sqlite:///{db_path}"

# Khởi tạo Engine
engine = create_engine(DATABASE_URL, echo=False)

# Khởi tạo Session Factory (Chuẩn đa luồng)
SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
SessionLocal = scoped_session(SessionFactory)


def init_db():
    """Hàm này tự động dò tìm các models, tạo bảng và GIEO DỮ LIỆU MẶC ĐỊNH"""
    import database.models  # Import để engine nhận diện
    Base.metadata.create_all(bind=engine)
    print("✅ Đã khởi tạo cấu trúc CSDL Enterprise thành công!")

    # --- SIÊU THUẬT TOÁN SEEDING: TỰ TẠO ADMIN NẾU CHƯA CÓ ---
    session = SessionLocal()
    try:
        # Kiểm tra xem trong DB đã có nhân viên nào chưa
        admin_exists = session.query(User).first()

        if not admin_exists:
            print("⚙️ Đang khởi tạo tài khoản Quản trị viên mặc định...")

            # Tạo mật khẩu mã hóa bảo mật
            salt = bcrypt.gensalt()
            hashed_pwd = bcrypt.hashpw("admin123".encode('utf-8'), salt).decode('utf-8')

            # Tạo user admin
            default_admin = User(
                username="admin",
                password_hash=hashed_pwd,
                full_name="Giám Đốc (CEO)",
                role=RoleEnum.ADMIN,
                is_active=True
            )
            session.add(default_admin)
            session.commit()
            print("🎉 TẠO THÀNH CÔNG TÀI KHOẢN MẶC ĐỊNH!")
            print("👉 Tên đăng nhập: admin")
            print("👉 Mật khẩu: admin123")
    except Exception as e:
        print(f"❌ Lỗi khi gieo dữ liệu: {e}")
        session.rollback()
    finally:
        session.close()


def get_db_session():
    """Hàm cung cấp session cho các Controller (Dependency Injection)"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()