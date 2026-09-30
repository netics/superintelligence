buf = bytearray(b"\x00\x00")  # a 2-byte header
buf[0] = 0x7F  # patch one byte in place
buf += b"data"  # grow it without building a new object
print(bytes(buf))  # b'\x7f\x00data'
