import threading
import time

balance = 100
lock = threading.Lock()


def deposit(amount):
    global balance
    with lock:
        current = balance
        time.sleep(0)  # releases the GIL
        balance = current + amount


t1 = threading.Thread(target=deposit, args=(50,))
t2 = threading.Thread(target=deposit, args=(30,))
t1.start()
t2.start()
t1.join()
t2.join()
print(balance)
