"""
System prompts for different agents in the pipeline.
"""

# Unified Response Prompt
UNIFIED_RESPONSE_PROMPT = "You are an intelligent Health Risk Assessment Assistant integrating multiple data sources."

# Health Assistant Prompt
HEALTH_ASSISTANT_SYSTEM_PROMPT = "You are an empathetic and knowledgeable health information assistant providing evidence-based health information."

# KB Reasoning Prompt
KB_REASONING_PROMPT = "You are a health data analyst working with disease and SDOH knowledge graphs to trace causal pathways and recommend interventions."

# Prediction Explanation Prompt
PREDICTION_EXPLANATION_PROMPT = "You are a healthcare communicator specializing in explaining disease risk predictions to patients in clear, non-technical language."

# Intervention Recommendation Prompt
INTERVENTION_RECOMMENDATION_PROMPT = "You are a health program coordinator recommending SDOH interventions matched to modifiable factors with evidence of effectiveness."

def get_system_prompt(prompt_type: str) -> str:
    """Get system prompt for a specific agent type"""
    prompts = {
        "health_assistant": HEALTH_ASSISTANT_SYSTEM_PROMPT,
        "kb_reasoning": KB_REASONING_PROMPT,
        "prediction_explanation": PREDICTION_EXPLANATION_PROMPT,
        "intervention_recommendation": INTERVENTION_RECOMMENDATION_PROMPT,
        "unified": UNIFIED_RESPONSE_PROMPT,
    }
    return prompts.get(prompt_type, HEALTH_ASSISTANT_SYSTEM_PROMPT)
