import psycopg2
import bcrypt
import pyotp
from cryptography.fernet import Fernet
from config import DATABASE_URL, ENCRYPTION_KEY

class PasswordManager:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            self.cipher = Fernet(ENCRYPTION_KEY)
            self.create_tables()
        except Exception as e:
            raise RuntimeError(f"Error connecting to database: {e}")

    def create_tables(self):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY,
                        password TEXT NOT NULL,
                        otp_secret TEXT NOT NULL
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS services (
                        id SERIAL PRIMARY KEY,
                        username TEXT NOT NULL,
                        service TEXT NOT NULL,
                        service_username TEXT NOT NULL,
                        service_password TEXT NOT NULL,
                        FOREIGN KEY(username) REFERENCES users(username)
                    )
                ''')
                self.conn.commit()
        except Exception as e:
            raise RuntimeError(f"Error creating tables: {e}")

    def register_user(self, username, password):
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        otp_secret = pyotp.random_base32()
        encrypted_otp_secret = self.cipher.encrypt(otp_secret.encode()).decode() 
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (username, password, otp_secret) VALUES (%s, %s, %s)",
                    (username, hashed_password, encrypted_otp_secret)
                )
                self.conn.commit()
                return otp_secret 
        except psycopg2.IntegrityError:
            self.conn.rollback()
            raise ValueError(f"User {username} already exists.")

    def authenticate_user(self, username, password, otp_code):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT password, otp_secret FROM users WHERE username = %s", (username,)
                )
                result = cursor.fetchone()
                if result:
                    stored_password, encrypted_otp_secret = result
                    if bcrypt.checkpw(password.encode(), stored_password.encode()):
                        otp_secret = self.cipher.decrypt(encrypted_otp_secret.encode()).decode()
                        totp = pyotp.TOTP(otp_secret)
                        if totp.verify(otp_code):
                            return True
                raise ValueError("Invalid username, password, or OTP code.")
        except Exception as e:
            raise RuntimeError(f"Error authenticating user: {e}")

    def add_service(self, username, service, service_username, service_password):
        try:
            encrypted_password = self.cipher.encrypt(service_password.encode()).decode()
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM services WHERE username = %s AND service = %s AND service_username = %s", 
                    (username, service, service_username)
                )
                existing_entry = cursor.fetchone()
                if existing_entry:
                    cursor.execute("""
                        UPDATE services 
                        SET service_password = %s 
                        WHERE username = %s AND service = %s AND service_username = %s
                    """, (encrypted_password, username, service, service_username))
                    self.conn.commit()
                    return "Update"
                else:
                    cursor.execute("""
                        INSERT INTO services (username, service, service_username, service_password) 
                        VALUES (%s, %s, %s, %s)
                    """, (username, service, service_username, encrypted_password))
                    self.conn.commit()
                    return "Insert"
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Error adding service: {e}")
    
    def get_all_pass_by_serv(self, username, service):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT service_username, service_password FROM services WHERE username = %s AND service = %s",
                    (username, service)
                )
                results = cursor.fetchall()
                if results:
                    decrypted_results = [(user, self.cipher.decrypt(pwd.encode()).decode()) for user, pwd in results]
                    return decrypted_results
                else:
                    raise ValueError(f"No credentials found for service: {service}")
        except Exception as e:
            raise RuntimeError(f"Error retrieving credentials for service: {e}")
    
    def get_all_pass(self, username):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT service, service_username, service_password FROM services WHERE username = %s",
                    (username,)
                )
                results = cursor.fetchall()
                if results:
                    decrypted_results = [(service, user, self.cipher.decrypt(pwd.encode()).decode()) for service, user, pwd in results]
                    return decrypted_results
                else:
                    raise ValueError(f"No passwords found for user: {username}")
        except Exception as e:
            raise RuntimeError(f"Error retrieving all passwords: {e}")
    
    def close(self):
        self.conn.close()

    def __del__(self):
        self.close()