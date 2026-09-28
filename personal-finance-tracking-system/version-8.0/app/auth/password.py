from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError


password_hasher = PasswordHasher()

def hash_password(hashed):
      return password_hasher.hash(hashed)




def verify_password(password, hashed):
      try:
            return password_hasher.verify(hashed, password)
      except VerifyMismatchError:
            return False 
      except InvalidHashError:
            return False