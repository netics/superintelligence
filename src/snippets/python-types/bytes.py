import hashlib

data = "héllo".encode("utf-8")  # str to bytes
print(len(data))  # 6: five letters, but é takes two bytes
print(hashlib.sha256(data).hexdigest()[:12])  # needs bytes
print(data.decode("utf-8"))  # héllo, back to str
