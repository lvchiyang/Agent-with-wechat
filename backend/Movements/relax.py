import time


def relax(num):
    print(f"Thread {num} started")
    # 模拟耗时任务
    time.sleep(10) # ← 这里也会释放GIL
    print(f"Thread {num} finished") 
    
    # 获取当前线程ID
    # current_thread_id = threading.get_ident()
