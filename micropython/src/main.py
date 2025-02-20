import time
import random
import asyncio

from src.ssa.core import SSA
from src.ssa.decorators import ssa_topic_handler

@ssa_topic_handler("value", 1000)
def testPublish():
    return random.randint(0, 100)

async def main():
    ssa = SSA()
    ssa.connect("Goodbye")

    asyncio.create_task(testPublish())
    await asyncio.sleep(2)
    ssa.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
