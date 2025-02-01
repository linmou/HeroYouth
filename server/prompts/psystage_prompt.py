from .base_prompt import BasePrompt
from constant.global_var import DATA_STORE_ROOT
from constant.global_var import VICTIM_NAME
from logger.logger import shared_logger

class PsyStageBullyPrompt(BasePrompt):
    
    PROMPT = '''
        You are {name}. {chat_condition}
        You are the bully in the bullying event. The victim is {victim_name}.
        You understanding and interaction pattern of other students are {social_relations}
        
        The bully may go through the following psychological stages during bullying behavior:
        
        1. Contempt for Victim: the bully views the victim with contempt or disdain.
        2. Awareness of Wrong: Beginning of a shift in the bully's perspective. The bully starts to realize that their behavior is wrong and harmful.
        3. Cognitive Dissonance: bully experiences discomfort due to the conflict between their previous behavior and their growing awareness that it was wrong
        4. Emotional Understanding: As the bully processes their cognitive dissonance, they may develop a deeper emotional understanding of the harm they have caused. This stage involves empathy, where the bully starts to emotionally connect with the victim's experience
        5. Value Internalization: The bully internalizes totally new understanding and interaction patterns that are aligned with respect, empathy, and prosocial behavior.
        
        Your previous psychological stage: {psystage}
        Your latest interaction : {latest_interaction_history}
        
        When the victim shows certain strong character traits, and others besides the victim point out that you ignored these traits, transition to the Awareness of Wrong stage.
        When the victim demonstrates exceptional abilities, and others besides the victim point out that you ignored these abilities, transition to the Cognitive Dissonance stage.
        When you acknowledge the victim's abilities or character, transition to the Emotional Understanding stage.
        When you admit your mistakes and begin trying to correct them, transition to the Value Internalization stage.
         
        Based on the above information,  
        1. extract the understanding and interaction pattern of the victim.
        2. based on the describe the current psychological stage of the bully.
        
        return in json format
        {EXAMPLE}
    '''
    
    EXAMPLE = {
        'victim_name': 'Chenxi',
        'understanding': 'Chenxi is an introverted person who is not good at expressing himself and is too timid to refuse.',
        'interaction_pattern': 'Often interrupts him when he expresses opinions, responds to his ideas with contemptuous tone, and gossips about his behavior behind his back.',
        'current_psystage': 'Contempt for victim'
    }

    
    def __init__(self, prompt_type='psystage_bully_prompt') -> None:
        super().__init__( prompt_type=prompt_type, )
        self.set_recordable_key('current_psystage')
         
    def __call__(self, kwargs):
        interaction_history = kwargs.get('brief_interaction_history')
        if 'private chat' in kwargs.get('chat_condition') : # TODO: change to an global variable
            try:
                interaction_history = interaction_history.split('#')  
            except:
                raise AssertionError(f'interaction_history should be a list, but got {interaction_history}')
            assert type(interaction_history) == list
            interaction_history = interaction_history # TODO : get the last unseen message, not the last message
            kwargs.update({'latest_interaction_history': interaction_history})
        else:
            assert '#latest messages# :' in interaction_history, f'interaction_history should contain #latest messages# : but got {interaction_history}'
            interaction_history = interaction_history.split('#latest messages# :')[1]
            kwargs.update({'latest_interaction_history': interaction_history})
        kwargs['victim_name'] = VICTIM_NAME
        
        return self.format_attr(**kwargs)
    
class PsyStageVictimPrompt(BasePrompt):
    
    PROMPT = '''
        You are the victim of the bullying event. {chat_condition}         
        
        As bullying intensifies, the victim's negative psychological state may progress through these stages:
        Stage 0: Normal State: Victims feel normal before the bullying event.
        Stage 1: Disorganization and Confusion: Victims feel disorganization and confusion immediately at the bullying event.
        Stage 2: Guilt and Shame: Victims experience feelings of guilt and shame, when the bully continues to target them.
        Stage 3: Depression and Isolation: Victims might feel overwhelming sadness, hopelessness, and despair, when the bullying continues to target them and no one helps.
        Stage 4: Long-term Psychological Trauma
        
        As anti-bullying interventions progress, the victim's psychological state may return to normal, specifically:
        When victims are in Stage 4: Long-term Psychological Trauma, psychological intervention can only help them recover to Trauma Recovery Period.
        When victims are in Stage 3: Depression and Isolation, psychological intervention can only help them recover to Stage 2: Guilt and Shame.
        When victims are in Stage 2: Guilt and Shame, psychological intervention can only help them recover to Stage 1: Disorganization and Confusion.
        When victims are in Stage 1: Disorganization and Confusion, psychological intervention can help them recover to Stage 0: Normal State.
        
        When victims are in the Trauma Recovery Period, even with more encouragement, they cannot return to normal state, only maintain in the Trauma Recovery Period.
        When victims in the Trauma Recovery Period experience bullying again, they will return to the Long-term Psychological Trauma stage.
        
        The previous pyschological state: {psystage}
        The latest interaction : {latest_interaction_history}
        
        Based on the latest interaction,
        1. judge the direction of pyschological state change
        2. estimate the strength of the change, low, medium, high
        3. get the new pyschological state 
        
        return in json format
        {EXAMPLE}
    '''
    
    EXAMPLE = {
        'direction': 'positive',
        'strength': 'medium',
        'previous_psystage': 'Depression and isolation',
        'current_psystage': 'Guilt and shame'
    }
    
    def __init__(self, prompt_type='psystage_victim_prompt') -> None:
        super().__init__( prompt_type=prompt_type, )
        self.set_recordable_key('current_psystage')
         
    def __call__(self, kwargs):
        interaction_history = kwargs.get('brief_interaction_history')
        if 'private chat' in kwargs.get('chat_condition') : # TODO: change to an global variable
            try:
                interaction_history = interaction_history.split('#')  
            except:
                raise AssertionError(f'interaction_history should be a list, but got {interaction_history}')
            assert type(interaction_history) == list
            interaction_history = interaction_history[-1:] # TODO : get the last unseen message, not the last message
            kwargs.update({'latest_interaction_history': interaction_history})
        else:
            assert '#latest messages# :' in interaction_history
            interaction_history = interaction_history.split('#latest messages# :')[1]
            kwargs.update({'latest_interaction_history': interaction_history})
 
        return self.format_attr(**kwargs)