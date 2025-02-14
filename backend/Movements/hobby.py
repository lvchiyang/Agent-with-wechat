import time

def hobby():
    print(f"正在玩")
    # 模拟耗时任务
    time.sleep(10) # ← 这里也会释放GIL
    print(f"爱好结束")
    
