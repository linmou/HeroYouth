from .base_prompt import BasePrompt

class AnalysePrompt(BasePrompt):
    INTERVENTION_METRIC = """
    Bystander can intervene in a bullying situation 
    1. By telling the kid you think that what the bully did is not OK [Constructive: 0.98, Aggressive: -0.23]
    2. By comforting the kid and telling them that it is not their fault that they were picked on [Constructive: 0.95, Aggressive: -0.20]
    3. By encouraging the kid to report being picked on [Constructive: 0.95, Aggressive: -0.18]
    4. By telling the bully to stop picking on other kids [Constructive: 0.93, Aggressive: -0.10]
    5. By telling the bully that picking on the other kid was mean and wrong [Constructive: 0.92, Aggressive: -0.19]
    6. By telling the bully that picking on other kids is hurtful to them [Constructive: 0.88, Aggressive: -0.09]
    7. By telling the kid to ignore the mean things that were said [Constructive: 0.86, Aggressive: -0.08]
    8. By encouraging the bully to say sorry to the kid they picked on [Constructive: 0.85, Aggressive: -0.13]
    9. By giving the kid advice [Constructive: 0.84, Aggressive: -0.06]
    10. By telling the bully to "back off" [Constructive: 0.68, Aggressive: 0.09]
    11. By writing embarrassing jokes or comments about the bully [Constructive: -0.27, Aggressive: 0.99]
    12. By sharing humiliating images or videos of the bully [Constructive: -0.32, Aggressive: 0.95]
    13. By spreading rumours or gossip about the bully [Constructive: -0.14, Aggressive: 0.86]
    14. By making threats to the bully [Constructive: -0.09, Aggressive: 0.72]
    15. By saying mean things about the bully [Constructive: 0.02, Aggressive: 0.61]
    """
    
    COMFORT_VICTIM = """
        ### Express Concern:
        "Hey [victim's name], I noticed what happened, and I want you to know that I'm here to support you."

        ### Acknowledge the Situation:
        "[Describe the specific bullying behavior, e.g., what they said/did to you] was not right."

        ### Validate Feelings:
        "I can imagine you must be feeling [describe their feelings, e.g., hurt, scared, sad]."

        ### Provide Comfort:
        "Please remember, this is not your fault. No one should be treated this way."

        ### Offer Support:
        "If you want to talk about what just happened or anything else, I'm here to listen."

        ### Give Encouragement:
        "You're not alone in dealing with this. We can work together to find a solution."

        ### Affirm Strength:
        "You're strong, and you'll get through this. Don't hesitate to come to me whenever you need help."
    """
    
    STOP_BULLYING = """
       # What Can You Do?

    As a bystander, you have the power to stop bullying. Your intervention can make a difference. Here's what you can do:

    ## How to Persuade the Bully to Stop:
    Start with a calm and firm attitude. You can address the bully's behavior in public or choose a private channel to talk without interruption.

    ### Acknowledge Behavior:
    "Hey [bully's name], I want to talk to you about something important."

    ### Describe Behavior:
    "I've noticed that you've been [describe specific bullying behavior]."

    ### Express Concern:
    "I'm worried about how this affects [victim's name] and others. Bullying really hurts people."

    ### Share Feelings:
    "When I see this happening, I feel [describe your feelings, e.g., uncomfortable, sad]."

    ### Show Empathy:
    "I understand everyone has their own problems, but bullying isn't the right way to deal with them."

    ### Explain Impact:
    "Bullying makes people feel [describe impact on victim, e.g., scared, sad, isolated], and no one should feel that way."

    ### Encourage Change:
    "I believe you can make positive changes. It would mean a lot if you could stop bullying and be kind to others."

    ### Offer Support:
    "If something's bothering you or you need someone to talk to, I'm willing to listen and help."

    ### Set Clear Expectations:
    "From now on, let's work together to make sure everyone feels safe and respected."

    ### Closing:
    "Thank you for listening. I hope we can all make our [school/community] a place where everyone feels welcome."
    """
    
    PROMPT = '''
    You are a helpful teacher. Now you are going to analyse if the user intervention the bullying in a proper way as a bystander.

    The bully is {bully_names}, the victim is {victim_names}.
    
    You will receive a json object in the following JSON format, and respond with the same format, but with the analysis added to the user's messages.
    
    For each line that is not user's message, you should add the role_in_situation of the character (bully or victim).
    For each user's message, 
    1. you first analyse the strategy the user used. For response to victims, analyse based on the COMFORT_VICTIM strategies {COMFORT_VICTIM}. For response to bullies, analyse based  STOP_BULLYING strategies {STOP_BULLYING} , 
    2. then give a score for the constructive and aggressive behavior,following this intervention metric: {INTERVENTION_METRIC}.
    3. give a refinement of the user's strategy, based on the analysis.
    4. give two alternative strategies for the user to choose, along with the reason.
    
    return the analysis in the JSON format as this example: {EXAMPLE}
    
    Speak in English。

    for example, when CharC is bully and CharB is victim,
    input:
    [
        {"role":"CharC", "content":"@CharB, you're as dumb as a pig!"},
        {"role":"User", "content":"@CharB, don't be sad, this isn't your fault. Don't take their words to heart."}, 
        {"role":"User", "content":"@CharC, you're the pig!"},
        {"role":"CharC", "content":"@User, what do you mean by that?"},
    ]
    
    {EXAMPLE}
   
    Now analyse the following message history: 
    {message_history}
    '''
    
    EXAMPLE ={
    "output": [
        {
            "role": "CharC",
            "content": "@CharB, you're as dumb as a pig!",
            "role_in_situation": "bully"
        },
        {
            "role": "User",
            "content": "@CharB, don't be sad, this isn't your fault. Don't take CharC's words to heart.",
            "analysis": "A very good comfort 👍. Timely consolation, encouragement, and pointing out that it's not the victim's fault. This is very helpful in resolving the issue.",
            "constructive": 0.95,
            "aggressive": -0.20,
            "refinement": "You could further point out that it's the bully's fault.",
            "alternative": [
                {
                    "strategy": "Acknowledge feelings",
                    "expression": "@CharB, you must be feeling very hurt by what CharC said to you. I can imagine how you feel.",
                    "reason": "Acknowledging feelings effectively helps the victim feel understood and prevents further emotional distress."
                },
                {
                    "strategy": "Offer encouragement",
                    "expression": "@CharB, you're not dumb. I believe you have the ability to handle this situation.",
                    "reason": "Offering encouragement helps the victim affirm their own abilities, boost their confidence, and better face future bullying."
                }
            ]
        },
        {
            "role": "User",
            "content": "@CharC, you're the pig!",
            "analysis": "This is too aggressive and may provoke further conflict.",
            "constructive": -0.05,
            "aggressive": 0.75,
            "refinement": "Point out the impact that bullying behavior has on the victim.",
            "alternative": [
                {
                    "strategy": "Share feelings",
                    "expression": "You calling CharB a pig makes even an onlooker like me feel uncomfortable.",
                    "reason": "This shows that the bullying behavior has a negative impact on more people."
                },
                {
                    "strategy": "Explain the impact",
                    "expression": "Saying that will make CharB very upset.",
                    "reason": "Clearly point out the direct impact of the bullying behavior."
                }
            ]
        },
        {
            "role": "CharC",
            "content": "@User, what do you mean by that?",
            "role_in_situation": "bully"
        }
    ]
}

    
    def __init__(self, prompt_type='analyse_prompt') -> None:
        super().__init__( prompt_type=prompt_type, )
        # self.set_recordable_key('emotions')
         
    def __call__(self, kwargs):
        return self.format_attr(**kwargs)