"""
Shared state keys and model configuration.
Import these in every sub-agent to stay consistent.
"""

# Model
MODEL = "gemini-2.5-flash"

# State keys
STATE_RAW_CONTENT = "raw_content"
STATE_VALIDATED_CONTENT = "validated_content"
STATE_CONTENT_TYPE = "content_type"
STATE_REFLECTIVE_QUESTIONS = "reflective_questions"
STATE_REFINED_TICKET = "refined_ticket"
STATE_HITL_FEEDBACK = "hitl_feedback"
STATE_ITERATION_COUNT = "iteration_count"
STATE_USER_SATISFIED = "user_satisfied"
STATE_FINAL_TICKET = "final_ticket"