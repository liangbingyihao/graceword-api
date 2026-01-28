
import time

def get_utc_timestamp_millis() -> int:
    """
    获取当前 UTC 毫秒时间戳
    这是最推荐的方法
    """
    if hasattr(time, 'time_ns'):
        # Python 3.7+ 使用纳秒接口
        return time.time_ns() // 1_000_000
    else:
        # Python 3.6 及以下
        return int(time.time() * 1000)