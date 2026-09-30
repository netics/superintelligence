import math

temps = [21.5, 23.0, 19.8]
avg = sum(temps) / len(temps)  # / always returns a float
print(round(avg, 1))  # 21.4
print(math.isclose(0.1 + 0.2, 0.3))  # True, unlike ==
