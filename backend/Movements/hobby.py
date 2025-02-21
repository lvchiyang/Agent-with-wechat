import asyncio

async def hobby():
    print(f"正在玩")
    # 模拟耗时任务
    await asyncio.sleep(3600) # ← 这里也会释放GIL
    print(f"爱好结束")
    
