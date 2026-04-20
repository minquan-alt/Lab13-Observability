import os
import langfuse
from dotenv import load_dotenv
load_dotenv()

# Explicitly set
os.environ["LANGFUSE_DEBUG"] = "True"

from langfuse import observe, get_client

@observe(name="ROOT_FINAL_TEST")
def main():
    print("Inner main")
    child()

@observe(name="CHILD_FINAL_TEST")
def child():
    print("Inner child")

if __name__ == "__main__":
    main()
    get_client().flush()
    get_client().shutdown()
