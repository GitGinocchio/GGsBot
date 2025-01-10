import os

def clearpycache(path):
    for root, dirs, _ in os.walk(path):
        print(f"looking in: {root}")
        for dir in dirs:
            if dir == '__pycache__':
                os.system(f'rmdir /s /q {os.path.join(root, dir)}')
    print("done")

clearpycache('.')