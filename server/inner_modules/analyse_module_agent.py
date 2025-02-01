'''
This module analyse a specific agents' behaviors, especially user proxy agent. 
'''

from server.inner_modules.module_agent import CognitiveModuleAgent
from server.prompts.analyse_prompt import AnalysePrompt

class AnalyseModuleAgent(CognitiveModuleAgent):
    def __init__(self, function_prompt=AnalysePrompt, *args, **kwargs):
        super().__init__(
            name='analyse_module',
            system_message="You are an expert in analysing teenagers' social behaviors.",
            functional_prompt=function_prompt,
            *args, **kwargs)