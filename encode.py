import base64

token = ""

encoded = token.encode()
encoded = base64.encodebytes(encoded)
encoded = encoded.hex()
print(base64.urlsafe_b64decode(bytes.fromhex(encoded)).decode())