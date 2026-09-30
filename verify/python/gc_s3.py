import gc

a = []
b = []
a.append(b)
b.append(a)
del a, b
print(gc.collect())
