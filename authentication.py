import pyotp
import qrcode
import subprocess
import os

def generate_qr_code(username, otp_secret):
    totp_uri = pyotp.TOTP(otp_secret).provisioning_uri(name=username, issuer_name="SimplePassManager")
    qr = qrcode.make(totp_uri)
    qr_file_path = f"qrcodes/{username}_qr.png"
    os.makedirs(os.path.dirname(qr_file_path), exist_ok=True)
    qr.save(qr_file_path)
    subprocess.call(["wslview", qr_file_path])
    return qr_file_path