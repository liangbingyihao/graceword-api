import os

# 读取环境变量决定使用哪个实现
SERVICE_IMPL = os.environ.get("BOT_IMPL", "hk")  # 默认使用 cn

if SERVICE_IMPL == "cn":
    from .coze_service_cn import CozeService
else:
    from .coze_service import CozeService

# 导出类
__all__ = ['CozeService']