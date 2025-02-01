"""
This prompt helps agent perspect the world.
"""

from .base_prompt import BasePrompt

class PerspectPrompt(BasePrompt):
    PROMPT = """
        You are {name}. {chat_condition} 
        Your interaction history : {full_interaction_history}
        
        If you are in a group chat, 
        Add the new information into the old summary. Do not change the previous summary too much.
        return in json format:
        
        {EXAMPLE}
        
        If you are in a private chat, 
        return in json format:
        {
            "updated_summary": "null"
        }
    """
    
    EXAMPLE = {
        "involved_participants": [],
        "updated_summary": " Mr Wang re I asked Mr Zhang for help.  "
    }