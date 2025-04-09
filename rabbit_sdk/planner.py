# Rabbit/rabbit_sdk/planner.py
"""
Simple task planner: determines whether to reuse, redo, or skip a task.
Decides whether to reuse a task result from memory or execute again.

Uses memory key pattern: task:{task}:{url}
**Upgrade this with an LLM to make it more robust 
"""

# Rabbit/rabbit_sdk/planner.py 

def plan_next_action(memory_manager, task, session_id):
    """Plan the next action based on the current task and memory."""
    # Placeholder planning logic
    return f"Planned action for task: {task} in session {session_id}"
