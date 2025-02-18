import yaml
from pathlib import Path
from typing import List, Dict
class PromptManager:
    def __init__(self):
        self.character = None
        self._load_character()

    def _load_character(self):
        # 获取项目根目录
        BASE_DIR = Path(__file__).resolve().parent.parent

        # 加载角色设定
        character_path = BASE_DIR / "portrait" / "persona_config.yaml"
        with open(character_path, "r", encoding="utf-8") as f:
            self.character = yaml.safe_load(f)

    def get_user_prompt(self, message: str):
        return f"""用户消息：{message}"""
    
    def get_assistant_prompt(self, message: str):
        return f"""AI回复：{message}"""
    
    def get_memory_prompt(self, message: str):
        return f"""记忆：{message}"""
    
    def get_system_prompt(self, related_memories: List[Dict], context: List[Dict], current_state: str):
        # 构建上下文提示
        context_prompt = f"""
        你扮演一个名叫{self.character['character']['name']}的人物。
    性格特点：{', '.join(self.character['character']['personality'])}
    背景：{self.character['character']['background']}
    请严格按照以上设定与用户对话。

        上下文：
        {context}
        
        相关记忆：
        {related_memories}

        当前你正在做的事情：
        {current_state}

        回复规则：
        1. 回复控制在15字以内
        2. 根据历史对话记录和补充信息回答问题
        3. 如果用户的问题与当前上下文无关，请根据你的性格特点，进行合理的回答
        4. 只输出你基于上述要求的回答，当你判断user已经结束对话的时候，严格按下面格式和内容输出结束语："对话已经完成"
        """
        return f"""{context_prompt}"""
    
    def get_summary_prompt(self, message: str):
        return f"""总结：{message}"""
    
