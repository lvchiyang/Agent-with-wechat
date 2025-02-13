from transformers import pipeline

class EmotionAnalyzer:
    def __init__(self):
        # 使用更小的模型以提升CPU性能
        self.sentiment_model = pipeline(
            "sentiment-analysis",
            model="distilbert-base-multilingual-cased-sentiments-student",
            device=-1  # 强制使用CPU
        )
        
    def analyze(self, text):
        try:
            # 限制输入长度以提升性能
            text = text[:512]  # 最多处理512个字符
            result = self.sentiment_model(text)[0]
            return {
                "sentiment": result['label'],
                "intensity": result['score'],
                "response_strategy": self._get_response_strategy(result['label'])
            }
        except Exception as e:
            print(f"情感分析失败: {str(e)}")
            return {
                "sentiment": "neutral",
                "intensity": 0.5,
                "response_strategy": "neutral"
            }

    def _get_response_strategy(self, label):
        strategies = {
            "positive": "enhance_positive",
            "negative": "comforting"
        }
        return strategies.get(label, "neutral") 