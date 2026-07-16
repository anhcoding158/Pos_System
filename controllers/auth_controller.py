import bcrypt
from database.db_session import SessionLocal
from database.models import User


class AuthController:
    def login(self, username, password):
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.username == username, User.is_active == True).first()
            if user:
                password_bytes = password.encode('utf-8')
                hashed_bytes = user.password_hash.encode('utf-8')

                if bcrypt.checkpw(password_bytes, hashed_bytes):
                    return {
                        "id": user.id,
                        "username": user.username,
                        "full_name": user.full_name,
                        "role": user.role.value
                    }
            return None
        except Exception as e:
            print(f"Lỗi đăng nhập: {e}")
            return None
        finally:
            session.close()
