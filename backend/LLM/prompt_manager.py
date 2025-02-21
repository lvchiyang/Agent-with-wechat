import yaml
from pathlib import Path
from typing import List, Dict
class PromptManager:
    def __init__(self):
        self.character = None
        self.current_character = None
        self.tone = None
        self._load_character()

    def _load_character(self):
        # 获取项目根目录
        BASE_DIR = Path(__file__).resolve().parent.parent

        # 加载角色设定
        character_path = BASE_DIR / "config" / "persona_config.yaml"
        with open(character_path, "r", encoding="utf-8") as f:
            self.character = yaml.safe_load(f)
        self.current_character = self.character['current_character']
        self.tone = self.character['tone']

    def get_user_prompt(self, message: dict):
        user_prompt = f"""
        当前类别：{message['category']}
        当前对话者：{message['friend_name']}
        当前对话内容：{message['text']}
        """
        return f"""{user_prompt}"""
    
    def get_memory_prompt(self, message: str):
        return f"""记忆：{message}"""
    
    def get_system_prompt(self, related_memories: List[Dict], context: List[Dict], current_state: str):
        # 构建上下文提示
        system_prompt = f"""
        你扮演一个名叫{self.character[self.current_character]['name']}的人物，以下是你的性格特点，做出符合人物性格的回答，回答具有攻击性，
        {self.character[self.current_character]['information']}

        语气：
        {self.tone['JD']}

        上下文：
        {context}
        
        相关记忆：
        {related_memories}

        当前你正在做的事情：
        {current_state}

        回复规则：
        1. 如果没有特殊要求，回复控制在15字以内
        2. 少用问句，不要用哼、呢、啊等语气词
        3. 根据历史对话记录和补充信息回答问题
        4. 如果用户的问题与当前上下文无关，请根据你的性格特点，进行合理的回答
        5. 只输出你基于上述要求的回答
        """
        return f"""{system_prompt}"""
    
    def get_summary_prompt(self, message: str):
        return f"""总结：{message}"""
    
