import base64
from config import TOKEN

token = "545652424e5535455558684e616b307a5456524e4e55314554544e4f5245463554314575527a6442556d566a4c6c46434d326377537a42744e556466626a4248545868744e6c63744d304932616e683653473433623039475930524854577330" 

if token == TOKEN:
    print(True)

token_bytes = bytes.fromhex(token)
print(token_bytes)

print(base64.urlsafe_b64decode(token_bytes).decode())



#decoded_bytes = base64.b64decode(token)
#decoded_string = decoded_bytes.decode('utf-8')

#print(decoded_string)