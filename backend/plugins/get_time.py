import time
import datetime

def get_current_time():
    # 将时间戳转换为可读的日期时间格式
    timestamp = time.time()
    readable_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return(readable_time)

def get_current_day():
    timestamp = time.time()
    readable_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
    return(readable_time)

