from get_time import get_current_time, get_current_day
import json

if __name__ == "__main__":
    current_time = get_current_time()
    print(current_time)


plan = '{"plan": "relax"}'
plan_data = json.loads(plan)
plan = plan_data['plan']
print(plan)