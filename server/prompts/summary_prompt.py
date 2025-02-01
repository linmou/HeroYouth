from server.prompts.base_prompt import BasePrompt

class SummaryPrompt(BasePrompt):
    
    GROUPCHAT_SUMMARY_PROMPT_EN = "You are in a group chat. Summarize the chat history, including each participant's conversation history. Do not add any introductory information. As breif as possible."
    
    PROMPT = '''
    You are {name}.
    {chat_condition} 
    {GROUPCHAT_SUMMARY_PROMPT_EN}
    chat history is: {full_interaction_history}
    
    
    return in json format, for example: {EXAMPLE}
    the 'chat_type' should be 'groupchat' or 'privatechat'
    '''
    
    EXAMPLE = { 'chat_type': 'groupchat',
                'participants': ['Xiao Wang', 'Xiao Zhang', 'Xiao Li'],
                'summary': {'Xiao Wang': "Apples are delicious.", 
                          "Xiao Zhang": "Repeatedly insists apples are not delicious and argues with Xiao Wang", 
                          "Xiao Li": "Agrees with Xiao Wang's viewpoint."}
                }
    
    def __init__(self, prompt_type='summary_prompt',check_exempt_layers=[1,2,3,4,5,6,7,8,9] ) -> None:
        super().__init__( prompt_type=prompt_type, check_exempt_layers=check_exempt_layers)
        self.set_recordable_key(['chat_type','summary', 'participants'])
         
    def __call__(self, kwargs):
        return self.format_attr(**kwargs)
    
    def response_structure_check(self, response_dict, exempt_layers=...):
        super().response_structure_check(response_dict, exempt_layers)
        assert response_dict['chat_type'] in ['groupchat', 'privatechat'], f'chat_type should be groupchat or privatechat, current chat_type is {response_dict["chat_type"]}'
        if response_dict['chat_type'] == 'privatechat':
            assert len(response_dict['participants']) == 1, f'privatechat should have only one participant, current participants are {response_dict["participants"]}'
            
            