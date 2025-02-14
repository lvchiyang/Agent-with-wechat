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

    def _plan_loop(self):
        """主任务循环"""
        while self.should_continue:
            try:
                # 正常任务流程
                plan = self.get_plan_from_llm()
                self.excute_plan(plan)
                
            except Exception as e:
                logger.error(f"计划执行出错: {str(e)}")
            time.sleep(60)

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

    def get_plan_from_llm(self):
        """从LLM获取计划任务"""
        current_time = get_current_time()
        if self.date_of_summary != get_current_day():
            summary_task = "今日尚未完成总结"
        else:
            summary_task = "今日已完成总结"

        prompt = f"""
        你是一个智能助手，需要根据当前时间选择适当的任务。以下是可选任务：
        1. work - 工作
        2. hobby - 兴趣爱好
        3. relax - 休息
        4. summary - 每天只进行一次总结（仅在凌晨2-4点执行）{summary_task}
        
        请根据当前时间选择最合适的任务，并以JSON格式返回，例如：{{"plan": "work"}}
        
        当前时间：{current_time}
        """
        
        try:
            response = self.llm_client.chat(prompt)
            return response
        except Exception as e:
            logger.error(f"获取计划时出错: {str(e)}")
            return '{"plan": "relax"}'  # 出错时默认返回休息
        
    def excute_plan(self, plan):
        """对llm返回的plan进行解析"""
        plan_data = json.loads(plan)
        task = plan_data['plan']

        """对llm返回的计划进行执行"""
        if plan == "work":
            work.work()
        elif plan == "hobby":
            hobby.hobby()
        elif plan == "relax":
            relax.relax()
        elif plan == "summary":
            self.date_of_summary = get_current_day()
            self.memory.daily_summary()
        
        # 根据返回结果，更新Agent状态
        state_map = {
            "work": "working",
            "hobby": "relaxing",
            "relax": "resting",
            "summary": "summarying"
        }
        new_state = state_map.get(task, "idle")
        self.state_callback(new_state)  # 调用回调更新状态
        
        return task