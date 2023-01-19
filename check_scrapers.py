import os
import subprocess
from pathlib import Path
from subprocess import PIPE


def check_scrapers():
    root = Path(__file__).parent
    states = root.glob("*/opinions/*states/*/*.py")

    for state in states:
        if "/state/" in str(state):
            continue
        # try:
        subprocess.run(["python", "sample_caller.py", "-c", state])
        # except:
        #     with open("/Users/Palin/Code/juriscraper/output.txt", "a") as f:
        #         f.writelines(f"\n Error occured in {state} ")


if __name__ == "__main__":
    check_scrapers()
