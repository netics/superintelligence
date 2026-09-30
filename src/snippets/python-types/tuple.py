def min_max(values):
    return min(values), max(values)  # returns a tuple


low, high = min_max([4, 9, 1])  # unpacking: 1 and 9
cells = {(0, 0): "start", (2, 3): "exit"}  # tuple keys
print(low, high, cells[(2, 3)])  # 1 9 exit
