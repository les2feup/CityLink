import asyncio
from src.ssa.core import SSA

def ssa_topic_handler(topic: str, period_ms: int):
    def decorator(func):
        def wrapper(*args, **kwargs):
            ssa_instance = SSA()
            while True:
                result = func(*args, **kwargs)
                ssa_instance.publish(f"{topic}", f"{result}")
                await asyncio.sleep_ms(period_ms)
            return result
        return wrapper
    return decorator

