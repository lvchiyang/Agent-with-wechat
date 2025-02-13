import time

def hobby(num):
    print(f"Thread {num} started")
    # 模拟耗时任务
    time.sleep(10) # ← 这里也会释放GIL
    print(f"Thread {num} finished")
    
