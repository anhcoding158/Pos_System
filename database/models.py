from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


# --- CƠ SỞ CHO CÁC MODEL ---
class Base(DeclarativeBase):
    pass


# --- CÁC ĐỊNH NGHĨA TRẠNG THÁI (ENUMS) ---
class RoleEnum(enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    CASHIER = "cashier"
    WAITER = "waiter"


class TableStatusEnum(enum.Enum):
    EMPTY = "empty"  # Bàn trống
    OCCUPIED = "occupied"  # Đang có khách
    RESERVED = "reserved"  # Đã đặt trước


class OrderStatusEnum(enum.Enum):
    OPEN = "open"  # Khách đang ăn (Tạm tính)
    PAID = "paid"  # Đã thanh toán
    CANCELLED = "cancelled"  # Đã hủy


class ItemStatusEnum(enum.Enum):
    PENDING = "pending"  # Chờ báo bếp
    COOKING = "cooking"  # Bếp đang làm
    SERVED = "served"  # Đã mang ra bàn
    CANCELLED = "cancelled"  # Hủy món


# --- 1. NHÂN SỰ & PHÂN QUYỀN ---
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # Không lưu pass thô
    full_name: Mapped[str] = mapped_column(String(100), nullable=True)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.CASHIER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# --- 2. QUẢN LÝ BÀN & KHU VỰC ---
class Area(Base):
    __tablename__ = "areas"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)  # VD: Tầng 1, Sân vườn

    tables: Mapped[list["RestaurantTable"]] = relationship(back_populates="area")


class RestaurantTable(Base):  # Tránh dùng chữ 'Table' vì là từ khóa SQL
    __tablename__ = "restaurant_tables"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)  # VD: Bàn 01, VIP 1
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id"))
    status: Mapped[TableStatusEnum] = mapped_column(Enum(TableStatusEnum), default=TableStatusEnum.EMPTY)

    area: Mapped["Area"] = relationship(back_populates="tables")
    orders: Mapped[list["Order"]] = relationship(back_populates="table")


# --- 3. MENU, SẢN PHẨM & TOPPING ---
class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)  # VD: Đồ nướng, Lẩu, Nước giải khát

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=True)

    # THÊM CỘT MỚI: Đường dẫn lưu ảnh sản phẩm
    image_path: Mapped[str] = mapped_column(String(255), nullable=True, default="")

    category: Mapped["Category"] = relationship(back_populates="products")


class ModifierGroup(Base):
    """Nhóm Topping/Ghi chú (VD: Kích cỡ, Lượng đá, Lượng đường, Topping thêm)"""
    __tablename__ = "modifier_groups"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))  # VD: Size, Topping
    is_multiple: Mapped[bool] = mapped_column(Boolean, default=False)  # Chọn nhiều topping được không?

    modifiers: Mapped[list["Modifier"]] = relationship(back_populates="group")


class Modifier(Base):
    """Chi tiết Topping (VD: Size L +10k, Trân châu +5k, Không hành +0đ)"""
    __tablename__ = "modifiers"
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("modifier_groups.id"))
    name: Mapped[str] = mapped_column(String(50))
    price_impact: Mapped[float] = mapped_column(Float, default=0.0)  # Số tiền cộng/trừ thêm

    group: Mapped["ModifierGroup"] = relationship(back_populates="modifiers")


# --- 4. HÓA ĐƠN & BÁN HÀNG ---
class Discount(Base):
    """Quản lý các loại mã giảm giá/Khuyến mãi"""
    __tablename__ = "discounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))  # VD: Khai trương giảm 10%
    type: Mapped[str] = mapped_column(String(20))  # 'PERCENT' hoặc 'AMOUNT'
    value: Mapped[float] = mapped_column(Float)  # 10 (10%) hoặc 50000 (50k)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Order(Base):
    """Bảng Hóa đơn tổng"""
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # Order ID tự sinh (VD: HD-A1B2)
    table_id: Mapped[int] = mapped_column(ForeignKey("restaurant_tables.id"),
                                          nullable=True)  # Có thể null nếu mua mang về
    cashier_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[OrderStatusEnum] = mapped_column(Enum(OrderStatusEnum), default=OrderStatusEnum.OPEN)

    # Tiền nong
    sub_total: Mapped[float] = mapped_column(Float, default=0.0)  # Tổng tiền món
    discount_amount: Mapped[float] = mapped_column(Float, default=0.0)  # Tiền giảm giá
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)  # Tiền khách phải trả

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    table: Mapped["RestaurantTable"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")


class OrderItem(Base):
    """Chi tiết từng món trong hóa đơn"""
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))

    quantity: Mapped[int] = mapped_column(Integer, default=1)
    base_price: Mapped[float] = mapped_column(Float)  # Đóng băng giá tại thời điểm mua
    note: Mapped[str] = mapped_column(String(255), nullable=True)  # Ghi chú tay (VD: Xin thêm bát phụ)
    status: Mapped[ItemStatusEnum] = mapped_column(Enum(ItemStatusEnum), default=ItemStatusEnum.PENDING)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()
    item_modifiers: Mapped[list["OrderItemModifier"]] = relationship(back_populates="order_item")


class OrderItemModifier(Base):
    """Lưu lại Topping của món đó (VD: Khách gọi Trà sữa, thì đây là Trân châu của ly trà sữa đó)"""
    __tablename__ = "order_item_modifiers"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"))
    modifier_id: Mapped[int] = mapped_column(ForeignKey("modifiers.id"))
    recorded_price: Mapped[float] = mapped_column(Float)  # Đóng băng giá topping

    order_item: Mapped["OrderItem"] = relationship(back_populates="item_modifiers")
    modifier: Mapped["Modifier"] = relationship()
