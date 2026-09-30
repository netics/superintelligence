tasks = ["review", "email"]
tasks.append("deploy")
tasks.sort()  # sorts in place
first = tasks.pop(0)
print(first, tasks)  # deploy ['email', 'review']
