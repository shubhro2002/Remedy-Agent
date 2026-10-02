import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.graph import app

def test_checkpoint_retrieval():
    load_dotenv(override=True)
    mongo_uri = os.environ.get("MONGODB_URI")
    
    if not mongo_uri:
        print("MONGODB_URI not found in environment variables.")
        return

    print("Connecting to MongoDB Atlas...")
    client = MongoClient(mongo_uri)
    db = client["secops_agent_memory"]
    checkpoints_col = db["checkpoints"]

    thread_id = "incident-002"
    config = {"configurable": {"thread_id": thread_id}}

    # ---------------------------------------------------------
    # PART 1: Raw PyMongo Query
    # ---------------------------------------------------------
    print(f"\n--- 1. Raw MongoDB Query (BSON Binary Payloads) ---")
    cursor = checkpoints_col.find(
        {"thread_id": thread_id},
        sort=[("checkpoint_id", -1)],
        limit=3
    )
    
    count = 0
    for doc in cursor:
        count += 1
        print(f"State ID:     {doc['checkpoint_id']}")
        print(f"Parent State: {doc.get('parent_checkpoint_id', 'None (START)')}")
        print(f"Payload Size: {len(doc['checkpoint'])} bytes")
        print("-" * 50)
        
    if count == 0:
        print(f"No checkpoints found for thread: {thread_id}. Run main.py first to generate data!")
        return

    # ---------------------------------------------------------
    # PART 2: LangGraph API
    # ---------------------------------------------------------
    print(f"\n--- 2. LangGraph API (Deserialized State) ---")
    current_state = app.get_state(config) # type: ignore
    
    # .next shows which nodes are queued up to run next (empty tuple means the graph reached END)
    print(f"Next Node in Queue: {current_state.next if current_state.next else 'END'}")
    print(f"Is Remediated:      {current_state.values.get('is_remediated')}")
    
    messages = current_state.values.get("messages", [])
    print(f"Total Messages:     {len(messages)}")
    if messages:
        # Print a snippet of the final message in the thread
        print(f"Last Msg Preview:   {str(messages[-1].content)[:100]}...")

    # ---------------------------------------------------------
    # PART 3: Time-Travel (Inspecting State History)
    # ---------------------------------------------------------
    print(f"\n--- 3. State History Traversal ---")
    history = app.get_state_history(config) # type: ignore
    
    step = 0
    for past_state in history:
        # Metadata tracks exactly which node generated this specific state checkpoint
        assert past_state.metadata is not None
        source_node = past_state.metadata.get('step', 'START')
        short_id = past_state.config['configurable']['checkpoint_id'][:8] # type: ignore
        print(f"Step -{step}: Node '{source_node}' -> (State ID: {short_id}...)")
        step += 1

if __name__ == "__main__":
    test_checkpoint_retrieval()