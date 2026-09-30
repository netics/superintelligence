visitors = ["ana", "bo", "ana", "cy"]
today = set(visitors)  # duplicates removed
yesterday = {"bo", "dan"}
print(sorted(today - yesterday))  # ['ana', 'cy'], new today
print(sorted(today & yesterday))  # ['bo'], came back
print("cy" in today)  # True, a fast hash lookup
