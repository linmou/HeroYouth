from server.inner_modules.module_agent import CognitiveModuleAgent
from server.prompts.psystage_prompt import PsyStageBullyPrompt, PsyStageVictimPrompt


class PsyStageBullyModuleAgent(CognitiveModuleAgent):
    def __init__(self, function_prompt=PsyStageBullyPrompt, *args, **kwargs):
        super().__init__(
            name='psystage_bully_module',
            system_message="You are a people understand psychology concepts well.",
            functional_prompt=function_prompt,
            *args, **kwargs)
        self.function_chain.add(self.update_psy_stage)
    
    def update_psy_stage(self, message_dict, recipient):
        recipient.psystage.update(message_dict['current_psystage'])
        return dict()
        

class PsyStageVictimModuleAgent(CognitiveModuleAgent):
    def __init__(self, function_prompt=PsyStageVictimPrompt, *args, **kwargs):
        super().__init__(
            name='psystage_victim_module',
            system_message="You are a people understand psychology concepts well.",
            functional_prompt=function_prompt,
            *args, **kwargs)
        self.function_chain.add(self.update_psy_stage)
    
    def update_psy_stage(self, message_dict, recipient):
        recipient.psystage.update(message_dict['direction']=='positive')
        self.logger.info(f'{recipient.name}\'s psystage changes {message_dict["direction"]} ')
        return dict()
        
    
    def update_victim_state(current_state, action):
        states = [
            "Normal State",
            "Disorganization and Confusion",
            "Guilt and Shame",
            "Depression and Isolation",
            "Long-term Psychological Trauma",
            "Trauma Recovery Period"
        ]
        
        if action == "Bullying":
            if current_state == "Trauma Recovery Period":
                return "Long-term Psychological Trauma"
            elif current_state in states[:4]:
                return states[states.index(current_state) + 1]
        
        elif action == "Psychological Intervention":
            if current_state == "Long-term Psychological Trauma":
                return "Trauma Recovery Period"
            elif current_state == "Trauma Recovery Period":
                return "Trauma Recovery Period"
            elif current_state in states[1:4]:
                return states[states.index(current_state) - 1]
        
        return current_state
    
