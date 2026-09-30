scores = [72, 45, 90, 58]
passed = [s >= 60 for s in scores]
print(passed)  # [True, False, True, False]
print(sum(passed))  # 2, because True counts as 1
print(any(passed), all(passed))  # True False
