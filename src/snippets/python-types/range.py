for i in range(3):
    print(i)  # 0, then 1, then 2

evens = range(0, 1_000_000, 2)  # only start, stop, step
print(len(evens), 999_998 in evens)  # 500000 True, instantly
