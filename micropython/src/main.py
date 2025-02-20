import time
import random

from src.ssa import SSA

def main():
    ssa = SSA()
    ssa.connect("Goodbye")

    while(True):
        ssa.publish("value", f"{random.randint(0, 100)}")
        time.sleep(5)

if __name__ == "__main__":
    main()
