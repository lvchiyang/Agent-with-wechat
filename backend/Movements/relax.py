import time


def relax():
    print(f"正在休息")
    # 模拟耗时任务
    time.sleep(100) # ← 这里也会释放GIL
    print(f"休息结束") 
    

