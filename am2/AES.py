from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
import base64

# Derive a key from a password
def derive_key(password, salt):
    key = PBKDF2(password, salt, dkLen=32, count=1000000)
    return key

# Encrypt a string
def encryptData(password, data=None):
    salt = get_random_bytes(16)
    key = derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_CFB)
    iv = cipher.iv
    if data is None:
        ciphertext = cipher.encrypt(password.encode())
    else:
        ciphertext = cipher.encrypt(data.encode())
    encrypted_data = base64.b64encode(salt + iv + ciphertext).decode('utf-8')
    return encrypted_data

# Decrypt a string
def decryptPW(encrypted_data, password):
    encrypted_data = base64.b64decode(encrypted_data)
    salt = encrypted_data[:16]
    iv = encrypted_data[16:32]
    ciphertext = encrypted_data[32:]
    key = derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_CFB, iv=iv)
    decrypted_data = cipher.decrypt(ciphertext).decode('utf-8')
    return decrypted_data

def verifyPW(encrypted_data, password):
    try:
        decrypted_data = decryptPW(encrypted_data, password)
        return decrypted_data == password
    except:
        return False
