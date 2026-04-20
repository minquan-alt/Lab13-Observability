import os
from dotenv import load_dotenv
load_dotenv()
from langfuse import get_client
import time

client = get_client()
print("--- Starting Manual Span ---")
with client.start_as_current_span(name="MANUAL_ROOT_DEBUG") as span:
    tid = client.get_current_trace_id()
    print(f"TRACE_ID_FOUND: {tid}")
    time.sleep(0.5)

client.flush()
client.shutdown()
print("--- Done ---")
