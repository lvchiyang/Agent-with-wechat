import threading
import time
import logging
from backend.Movements import hobby, relax, work
from backend.LLM.prompt_manager import PromptManager
import asyncio
import json
from backend.plugins.get_time import get_current_time, get_current_day

'''
plan作为一个任务管理线程存在，暂时不需要事件循环，实现响应接口，将其注释掉；
Movements下是可以执行的任务空间，每个任务是一个同步函数，plan等待每一个任务的完成，
每次调用llm，询问要执行的任务，返回要执行的任务名称，在plan中完成对llm返回的信息的解析，调用movements中的任务函数，
'''

logger = logging.getLogger(__name__)



class Plan():
    def __init__(self, state_callback, memory_manager, llm_client):
        self.should_continue = True
        self.plan_thread = threading.Thread(target=self._plan_loop)
        self.state_callback = state_callback
        self.memory = memory_manager
        self.last_summary_time = time.time()
        self.plan_thread.daemon = True
        self.llm_client = llm_client
        self.date_of_summary = None

    def _plan_loop(self): # 就要在线程中，调用异步函数
        loop = asyncio.new_event_loop()  # 创建新的事件循环
        asyncio.set_event_loop(loop)  # 设置为当前线程的事件循环

        async def main_loop():
            while self.should_continue:
                try:
                    plan = await self.get_plan_from_llm()
                    await self.excute_plan(plan)
                except Exception as e:
                    logger.error(f"计划执行出错: {str(e)}")
                await asyncio.sleep(100)


        loop.run_until_complete(main_loop())
        loop.close()

    def start(self):
        """启动计划线程"""
        if not self.plan_thread.is_alive():
            self.plan_thread.start()
            logger.info("Plan thread started")

    def stop(self):
        """停止计划线程"""
        self.should_continue = False
        if self.plan_thread.is_alive():
            self.plan_thread.join(timeout=5)  # 等待线程结束
            if self.plan_thread.is_alive():  # 这里还是有问题
                logger.warning("Plan thread did not stop gracefully")
            else:
                logger.info("Plan thread stopped successfully")

    async def get_plan_from_llm(self):
        """从LLM获取计划任务"""
        current_time = get_current_time()
        if self.date_of_summary != get_current_day():
            summary_task = "今日尚未完成总结"
        else:
            summary_task = "今日已完成总结"

        prompt = f"""
        你是一个智能助手，请从以下可选任务当中，请根据当前时间选择最合适的任务：
        1. work - 工作
        2. hobby - 兴趣爱好
        3. relax - 休息
        4. summary - 每天只进行一次总结（仅在下午15-17点执行）{summary_task}
                
        当前时间：{current_time}

        要求：
        1. 以JSON格式返回，例如：{{"plan": "work"}}
        2. 除了json，不要输出其他内容
        """
        
        try:
            response = await self.llm_client.chat(
                prompt, 
                response_format={"type": "json_object"}
            )
             
            return response
        except Exception as e:
            logger.error(f"获取计划时出错: {str(e)}")
            return '{"plan": "relax"}'  # 出错时默认返回休息
        
    async def excute_plan(self, plan):
        """对llm返回的plan进行解析"""
        plan_data = json.loads(plan)
        plan = plan_data['plan']

        # 根据返回结果，更新Agent状态
        state_map = {
            "work": "working",
            "hobby": "relaxing",
            "relax": "resting",
            "summary": "summarying"
        }
        new_state = state_map.get(plan, "idle")
        self.state_callback(new_state)  # 调用回调更新状态

        """对llm返回的计划进行执行"""
        if plan == "work":
            work.work()
        elif plan == "hobby":
            hobby.hobby()
        elif plan == "relax":
            relax.relax()
        elif plan == "summary":
            self.date_of_summary = get_current_day()
            await self.memory.daily_summary()
        

 
