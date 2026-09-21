from datetime import datetime, timedelta, timezone
import jwt 
import config
from jwt.exceptions import InvalidTokenError


def create_access_token(user_id):
      expiration_time = datetime.now(timezone.utc) + timedelta(minutes=15)
      payload = {
            "user_id": user_id,
            "exp": expiration_time
           
      }

      
      token =  jwt.encode(
                  payload, 
                  config.JWT_SECRET_KEY, 
                  algorithm="HS256"
            )

      return token


def verify_access_token(token):
      try:
            payload = jwt.decode(
                  token,
                  config.JWT_SECRET_KEY,
                  algorithms=["HS256"]

            )
            return payload

      except InvalidTokenError:
            return None










