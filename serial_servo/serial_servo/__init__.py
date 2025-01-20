# 导入 SerialServo 类并将其暴露给包用户
from .serial_servo import SerialServo

# 通过 __all__ 确保只暴露 SerialServo 类
__all__ = ["SerialServo"]
# 定义版本号
__version__ = "1.0.0"

