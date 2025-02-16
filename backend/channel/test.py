from backend.plugins.get_time import get_current_time, get_current_day
import json
import numpy as np

if __name__ == "__main__":
    current_time = get_current_time()
    print(current_time)


plan = '{"plan": "relax"}'
plan_data = json.loads(plan)
plan = plan_data['plan']
print(plan)

new_vector = np.random.rand(1024).tolist()
print(new_vector)


test = {
    "id": "1739704423283",
    "category": "私聊",
    "friend_name": "A",
    "group_name": "测试群组",
    "text": "你好",
    "image": ""
}