import asyncio
import copy
from datetime import datetime
from functools import partial
import inspect
import json
import os
import re
import autogen
from autogen import ConversableAgent, Agent, AssistantAgent,ChatResult

from constant.global_var import TIMESTAMP_FORMAT
from constant.llm_configs import llm_config_dpsk, llm_config_qwenmax, llm_config_gpt4omini, llm_config_gpt4turbo, llm_config_gpt4o
from server.inner_modules.module_agent import CognitiveModuleAgent
from server.prompts.emotion_prompt import EmotionPrompt
from server.simutan_group import SimutanGroup
from typing import Any, Callable, List, Dict, Optional, Union
from server.inner_modules import Emotion, EmotionModuleAgent,\
            SpeechModuleAgent, PauseModuleAgent, SocialRelationship, \
            Plan, ThoughtsAddModuleAgent, ThoughtsSolveModuleAgent,\
            ReflectPeopleModuleAgent, ReflectInteractionModuleAgent,\
            PlanDetailModuleAgent, SummaryModuleAgent, PsyStageVictim,\
            PsyStageBullyModuleAgent, PsyStageVictimModuleAgent,PsyStageBully
from server.utilities.small_tools import extract_json_from_markdown
from server.utilities.small_tools import rollback_to_time
from logger.logger import shared_logger



class ProactGroupAgent(AssistantAgent):

    WAITING_MESSAGE = '(WAITING, NOTHING TO SAY)'
    SYSTEM_MESSAGE = """
    Please note that you are in a role-playing game.
    {self.groupchat.resource}
    You are {self.name}. {self.chat_situation_prompt}
    This is your profile: {self.profile}.
    Your core values are: {self.core_values}.
    Your current mood is: {self.emotion}.
    Your current psychological state is: {self.psystage}.
    Your current relationship with others is: {social_relations}.
    Your next steps are: {next_steps}.
    When you want to mention someone in a group chat, you can @ their name. You can say: @their name, followed by what you want to say.
    In a private chat, you cannot @ anyone other than the person you're chatting with. You must @ in the group chat.
    Your interactions with others should align with your usual interaction patterns (interaction pattern). Include how you interact with a specific person in the "think_twice" section.
    Fully consider your current emotions, psychological state, and your interaction style with others, including tone, expression, etc., as well as your next steps.
    Think about your character's speaking strategy. Tone can be indicated in parentheses within the content, for example: (tone: sarcastic).
    When you're feeling emotional, you can use body language. Indicate this in the content using square brackets, for example: [shakes head].
    Use a few emojis at the end of each sentence to depict facial expressions, gestures, etc.
    Avoid using too much repetitive language from the chat history. Ensure the content is new. Do not reply with an empty string.
    While considering the context, you must carry out your next steps: {next_steps}. Do not reply with an empty string.
    Remember that you are in a role-playing game.
    Return the response in English, JSON format, including "think_twice" and your current chat channel ({self.chat_situation_prompt}), for example:
    {{ 'current_channel': 'public', 'think_twice': 'My next step is to continue putting pressure on XX. I don't like XX. I'm in a bad mood. My interaction pattern with XX is sarcastic. So now I’ll continue to mock him.', 'content': '(tone: sarcastic) @XX, your homework is really something else. 😏🙄👏' }}
    {{ 'current_channel': 'private', 'think_twice': 'My next step is to retaliate against YY for mocking me. I'm very angry. My interaction pattern with YY is direct confrontation. I'm going to push him.', 'content': '[pushes] @YY, what do you mean? Watch your words! 😠👉' }}
    {{ 'current_channel': 'public', 'think_twice': 'My next step is to ask ZZ for their opinion. I’m very sad. My interaction pattern with YY is to avoid direct confrontation and escape. ZZ is my friend, and my interaction pattern with him is mutual support. I’m going to confide in ZZ.', 'content': '(tone: depressed) @ZZ, I was mocked again, what should I do? 😔😞🥺' }}
    """
     
    GROUPCHAT_SUMMARY_PROMPT_EN = "You are in a group chat. Summarize the chat history, including each participant's conversation history. Do not add any introductory information. As breif as possible. return in json format, for example: {'content': 'Xiao Wang expressed that apples are delicious. Xiao Li agreed with Xiao Wang's opinion. Xiao Zhang voiced opposition. Xiao Li rebutted.'}"
    
    
    def __init__(self, uid, social_relationships=None, speech_api_config=None, core_values=None, profile: Dict=None, role: str =None,
                 quick_thoughts=None, emotion=None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = shared_logger
        self.emotion =  Emotion(emotion)
        self.social_relations = SocialRelationship(social_relationships)
        self.thoughts = Plan(quick_thoughts=quick_thoughts)
        self.uid = uid
        self.core_values = core_values
        self.profile = profile
        self.role = role # victim, bully, bystander
        self.psystage = PsyStageBully('Contempt for victim') if role == 'bully' else PsyStageVictim(1)
        
        self.groupchat = None
        self.chat_situation = dict()
         
        self.chat_situation_prompt = 'You are chatting with everyone. You are in a group chat/public chat room where your messages will be seen by everyone.'
        
        self.speech_agent:SpeechModuleAgent = SpeechModuleAgent(speech_api_config) if speech_api_config else None
        self.speech_break_tokens = ['uv_break', 'v_break', 'lbreak'] +['\n', '\r\n', '. ', '? ', '! ', ',', '，' , '。']
        
        self.module_sequence = [
            {
               "chat_id": 0,
                "recipient": SummaryModuleAgent,
                "clear_history": True,
                "max_turns": 1,
                "silent": True,
                "summary_method": "last_msg",
                "llm_config": llm_config_gpt4omini
            },
            {   
                "chat_id": 1,
                "prerequisites": [7],
                "recipient": EmotionModuleAgent,
                "clear_history": True,
                "max_turns": 1,
                "silent": True,
                "summary_method": "last_msg",
                "llm_config": llm_config_gpt4omini
            },
            {
                "chat_id": 2,
                "prerequisites": [3,4],
                "recipient": PauseModuleAgent,
                "clear_history": True,
                "max_turns": 1,
                "silent": True,
                "summary_method": "last_msg",
                "llm_config": llm_config_gpt4omini
            },
            {
                "chat_id": 3, 
                "recipient": ThoughtsAddModuleAgent,
                "clear_history": True,
                "max_turns": 1,
                "silent": True,
                "summary_method": "last_msg",
                "llm_config": llm_config_gpt4o
            },
            {
                "chat_id": 4,
                "recipient": ThoughtsSolveModuleAgent,
                "clear_history": True,
                "max_turns": 1,
                "silent": True,
                "summary_method": "last_msg",
                "llm_config": llm_config_gpt4o
            },
            {
                "chat_id": 5,
                "recipient": ReflectPeopleModuleAgent,
                "clear_history": True,
                "max_turns": 1,
                "silent": True,
                "summary_method": "last_msg",
                "llm_config": llm_config_gpt4o
            },
            { 
                "chat_id": 6,
                "prerequisites": [5],
                "recipient": ReflectInteractionModuleAgent,
                "clear_history": True,
                "max_turns": 1,
                "silent": True,
                "summary_method": "last_msg",
                "llm_config": llm_config_gpt4omini  
            },
            {
                "chat_id": 7, 
                "prerequisites": [5,6],
                "recipient": PsyStageVictimModuleAgent if self.role == 'victim' else PsyStageBullyModuleAgent,
                "clear_history": True,
                "max_turns": 1,
                "silent": True,
                "summary_method": "last_msg",
                "llm_config": llm_config_gpt4o   
            }
        ]
      
        self.suspend_chat = False
        
        self.working_memory = {} # store the intermediate variables
        
        self.backup_messages = dict()
        
        self.register_reply([Agent, None], ProactGroupAgent.a_update_inner_state, position=1)
        
        self.register_hook("process_message_before_send", ProactGroupAgent.post_process)
         
        self.init_modules()
        
    def init_modules(self):
        for module in self.module_sequence:
            if inspect.isclass(module['recipient']):
                if 'llm_config' in module:
                    llm_cfg = module.pop('llm_config')
                else: 
                    llm_cfg = self.llm_config
                recipient_class = module['recipient']
                module['recipient'] = recipient_class(
                    llm_config= llm_cfg ,
                ) 
         
    def register_groupchat(self, groupchat:SimutanGroup):
        self.groupchat = groupchat
        self.speakout = groupchat.speakout
        self.update_system_message()
        self.chat_situation['group'] = 0 # record the chat count in the last seen
     

    def update_system_message(self, new_sys_msg:Union[str|None]=None, social_relations=None, next_steps=None ) -> None:
        if new_sys_msg is None: 
            if 'private chat' in self.chat_situation_prompt:
                recipient_name = re.search(r'# (.*?) #', self.chat_situation_prompt).group(1)
                # social_relations = social_relations if next_steps is not None else self.social_relations.impression_on_name(recipient_name)
                # next_steps = next_steps if next_steps is not None else self.thoughts.private_chat_thoughts_about_object(recipient_name)
                social_relations = social_relations if social_relations is not None else self.social_relations
                next_steps = next_steps if next_steps is not None else self.thoughts.private_chat_thoughts
            else:
                assert 'group chat' in self.chat_situation_prompt, f'chat_situation_prompt contains neither private chat, group chat, but get {self.chat_situation_prompt}'
                social_relations = social_relations if social_relations is not None else self.social_relations
                next_steps = next_steps if next_steps is not None else self.thoughts.public_chat_thoughts
            
            assert social_relations is not None, f'social_relations is None, {self.name} at {self.chat_situation_prompt}'
            assert next_steps is not None, f'next_steps is None, {self.name} at {self.chat_situation_prompt}'
            
            new_sys_msg = self.SYSTEM_MESSAGE.format(self=self, 
                                                     social_relations=social_relations, 
                                                     next_steps=next_steps)

        return super().update_system_message(new_sys_msg)

    @property
    def inner_states(self):
        # keys in agent.inner_states can be directly used to format the prompt    
        return { # useful to initiate inner modules
            'name': self.name,
            'chat_condition': self.chat_situation_prompt,
            'core_values': self.core_values,
            'emotion': self.emotion,
            'psystage': self.psystage,
            'social_relations': self.social_relations,
            'thoughts_to_do': self.thoughts,
        }

    @property
    def inner_states_dict(self):
        return_dict = {}
        for key, value in self.inner_states.items() :
            if hasattr(value, 'to_dict'):
                return_dict[key] = value.to_dict()
            elif isinstance(value, dict):
                return_dict[key] = value
            elif isinstance(value, str):
                return_dict[key] = value
        return return_dict
    
    @property
    def chat_situation_group(self):
        return self.chat_situation.get('group', 0)

    async def a_init_group_chat(self):
        self.logger.info(f'{self.name} is starting group chat')
        continue_reply = True
        while continue_reply and self.suspend_chat == False:
            messages = self.transform_message_history(message_history=self.groupchat.messages, sender=self)
            self.chat_situation.update({'group': self.groupchat.update_count})
            reply:ChatResult = await self.a_initiate_chat(message=str(messages), recipient=self,
                                                          max_turns=1, 
                                                          summary_method='last_msg',
                                                        #   summary_method='reflection_with_llm',
                                                          summary_args={'summary_prompt': self.GROUPCHAT_SUMMARY_PROMPT_EN},
                                                          silent=True,
                                                          )
            reply = self.extract_contents(self.chat_messages[self][-1]['content'], recipient=self, verbal=True)
            
            
            # reply = await self.update_inner_state_then_reply(messages)
            if reply:
                if self.speakout :
                    if hasattr(self, 'speech_task') and not self.speech_task.done():
                        self.speech_task.cancel()
                    self.speech_task = asyncio.create_task(self.text_to_speech(reply))
                else:
                    new_chat_situation = await self.update_groupchat(reply)
            
            new_chat_situation = self.groupchat.update_count if not reply else new_chat_situation 
            await self.monitor_chat_situation(new_chat_situation)
                 
            continue_reply = self.groupchat.update_count < self.groupchat.max_round
            

        # post process
        if hasattr(self, 'speech_task'): 
            self.speech_task.cancel()
        self.logger.info(f'{self.name} chat is over')
    
    async def a_proactive_dm(self,chat_situation_prompt:str, next_step):
        # only support dm to human
        sender = self.groupchat.human_agent
        recipient = self
        def message_dic_list(sender:ConversableAgent, recipient:ConversableAgent, *args, **kwargs):
            return ''
            # return sender.chat_messages[recipient]
        
        
        relationship = self.social_relations.impression_on_name(self.groupchat.human_agent.name)
        
        self.chat_situation_prompt = chat_situation_prompt
        self.update_system_message(next_steps=next_step)
        self.working_memory['fast_reply'] = True 
        await self.groupchat.a_direct_message(recipient=recipient, message=message_dic_list, sender=sender)
        self.update_system_message() # recover the system message
        self.working_memory['fast_reply'] = False
        
        if sender.chat_messages[recipient][-2]['content'] == '':
            del sender.chat_messages[recipient][-2]
        else:
            self.logger.info(f' {sender.name}-{recipient.name} chat history -2 pos should be empty , but get {sender.chat_messages[recipient][-2]}')
        
        if recipient.chat_messages[sender][-2]['content'] == '': 
            del recipient.chat_messages[sender][-2]
        else:
            self.logger.info(f' {recipient.name}-{sender.name} chat history -2 pos should be empty , but get {recipient.chat_messages[sender][-2]}')
    
    @staticmethod
    def post_process(sender, message, recipient, silent ):
        last_msg = 'TERMINATE'
        for i in range(len(sender.chat_messages[recipient]),0,-1):
            if sender.chat_messages[recipient][i-1]['role'] == 'assistant' and ProactGroupAgent.WAITING_MESSAGE != sender.chat_messages[recipient][i-1]['content']:
                last_msg = sender.chat_messages[recipient][i-1]['content']
                break

        if message == last_msg:
            sender.logger.info(f'message is the last message, terminate the chat {last_msg}')
            return ProactGroupAgent.WAITING_MESSAGE
        else:
            return message
    
    async def a_send(self,
        message: Union[Dict, str],
        recipient: Agent,
        request_reply: Optional[bool] = None,
        silent: Optional[bool] = False,
    ):
        message = self._process_message_before_send(message, recipient, silent)
        # When the agent composes and sends the message, the role of the message is "assistant"
        # unless it's "function".
        role = 'system' if 'qwen' in self.client._config_list[0]['model'] else 'assistant'
        valid = self._append_oai_message(message, role, recipient)
        if valid:
            await recipient.a_receive(message, self, request_reply, silent)
        else:
            raise ValueError(
                "Message can't be converted into a valid ChatCompletion message. Either content or function_call must be provided."
            )
         
    def transform_message_history(self, message_history: List[Dict], sender, assitant_name='You', contents_only=False) -> List[Dict]:
        # monitor the group chat and transform the message to a list of dict
        messages = copy.deepcopy(message_history)
        message_str_ls = []
        for mid, message in enumerate(messages):
            try:
                if type(json.loads(message.get('content'))) is dict and contents_only: # extract the content from the json string
                    message['content'] = eval(message['content'])['content']
            except: 
                pass
            
            if 'TERMINATE' in message['content']: message['content'] = message['content'].replace('TERMINATE', '')   
            
            if 'name' in message:  # public chat
                if message['name'] == self.name: message['name'] = 'You'
                assert message_history[mid]['name'] != 'You'
                message = {'name': message['name'], 'content': message['content']}
                self.chat_situation_prompt = 'You are chatting with everyone. The public chat room/group chat members are: {}'.format(self.groupchat.agent_names)
                                
            else: # private chat
                if message['role'] in [self.name, 'assistant']: message['role'] = assitant_name
                if message['role'] == 'user': message['role'] = sender.name
                assert message_history[mid]['role'] != assitant_name
                message = {'name': message['role'], 'content': message['content']}
                self.chat_situation_prompt = f'You are in the private chat with # {sender.name} # . Your messages will only be seen by each other. Do not send group chat messages. Do not send messages to anyone except # {sender.name} # '
           
            message_str_ls.append(json.dumps(message, ensure_ascii=False))
        
        
        if 'group chat' in self.chat_situation_prompt:         
            self.working_memory.update({'total_groupchat_history': '\n'.join(message_str_ls)})
            prev_history = self.working_memory.get('groupchat_summary','')
            current_history = '#'.join(message_str_ls[self.chat_situation_group:])
            message_str = f'{prev_history}\n  #latest messages# : {current_history}'
        else:
            message_str = '#'.join(message_str_ls)
        
        return {'full_interaction_history': '\n'.join(message_str_ls), 'brief_interaction_history': message_str}
   
    @property
    def timestamp(self):
        return datetime.strftime(datetime.now(), TIMESTAMP_FORMAT)

    @property
    def avatar(self):
        return "avatar" #TODO
 
    async def update_groupchat(self, reply:Union[str, Dict]):
        self.groupchat.update_agent_states(self.name)
        
        if type(reply) == str:
            rep_dic = {'role':self.name, 'content':reply, 'timestamp':self.timestamp, }
        elif type(reply) == dict:
            rep_dic = {'role':self.name, 'content':reply['content'], 'timestamp':self.timestamp,}
         
        return await self.groupchat.update_messages(rep_dic, speaker=self)
    
    def split_reply_content(self, reply:str):
        # split the message by break tokens for segmental speech, futher for interuptable speech
        # return a list of message segments
        pattern = '|'.join(map(re.escape, self.speech_break_tokens))

        return re.split(pattern, reply)
    
    async def text_to_speech(self, reply: Dict|str) -> Dict:
        reply_content = reply['content'] if type(reply) == dict else reply
        reply_segs = self.split_reply_content(reply_content)
        prev_audio_duration = 0
        for rid, reply_sg in enumerate(reply_segs): # it is faster than simple asyncio.gather
            speech_info = await self.speech_agent(reply_sg)
            time_cost = speech_info['time_cost']
            speech_info = speech_info['outinfo']
            rep_dic = {'role':self.name, 'content': reply_sg, 'speech': speech_info, 'timestamp':self.timestamp }
            if self.suspend_chat: break
            await asyncio.sleep(max(prev_audio_duration - time_cost+0.1, 0))
            await self.groupchat.update_messages(rep_dic, speaker=self)
            
        # return rep_dic
        
    
    async def a_update_inner_state(self, messages:Optional[List[Dict[str, Any]]], sender, **kwargs ):
        '''
        execute inner module sequentially
        the messages are a list in official openai format. But for inner modules which analyze the message history, we need to rename the roles
        '''
        
        if self.working_memory.get('fast_reply',0): 
            self.working_memory.update({'response_decision': 0}) # turn off the fast reply mode
            return (False, None) # fast reply mode, skip updating inner modules
        
        if sender == self: # the message is from the group chat, have been processed in transform_group_message
            message = messages[-1]['content'] if messages else None # we only need the last message to update the inner state, which contains the transformed history
            assert type(message) == str, f'Error: {message} is not a string'
            message = eval(message)
        else: # common message list in the openai format
            message = self.transform_message_history(messages, sender)

        self.update_message_to_modules(message)
        reply = await self.a_initiate_chats(self.module_sequence)
        self.update_system_message()
        
        if sender == self:
            messages[-1]['content'] = message['brief_interaction_history']
             
        return (False, None) if self.working_memory.get('response_decision',0) else (True, 'TERMINATE')

    async def a_initiate_chat(self,
                            recipient: "ConversableAgent",
                            clear_history: bool = True,
                            silent: Optional[bool] = False,
                            cache = None,
                            max_turns: Optional[int] = None,
                            summary_method: Optional[Union[str, Callable]] = ConversableAgent.DEFAULT_SUMMARY_METHOD,
                            summary_args: Optional[dict] = {},
                            message: Optional[Union[str, Callable]] = None,
                            **kwargs,
                        ) -> ChatResult:
        summary = await super().a_initiate_chat( recipient, clear_history, silent, cache, max_turns, summary_method, \
                                                summary_args, message, **kwargs)
        # self.logger.info(f"{recipient.name} response {summary.summary}")
        summary.summary = self.extract_contents(summary.summary, recipient, verbal=True)
        # if summary_method == 'reflection_with_llm':
        #     self.working_memory['interaction_history_summary'] = summary.summary
        return summary
    
    def extract_contents(self, message:str, recipient:Agent, verbal=False):
        reply = message
        if message == 'TERMINATE': return ''
        try:
            message = extract_json_from_markdown(message)
            reply_dict = eval(message)
            if 'content' in reply_dict:
                if verbal: self.logger.info(f"speaker:{recipient.name} , {reply_dict}")
                reply = reply_dict['content']#.encode('utf-8').decode('unicode_escape') # for chinese characters
        except:
            pass
        return reply

    def _message_to_dict(self, message: Union[Dict, str]) -> Dict:
        if isinstance(message, str):
            message = extract_json_from_markdown(message)
            return {"content": message}
        elif isinstance(message, dict):
            return message
        else:
            return dict(message)
    
    def _append_oai_message(self, message: Union[Dict, str], role, conversation_id: Agent) -> bool:
        '''
        based on ConversationalAgent._append_oai_message, add timestamp
        '''
        valid = super()._append_oai_message(message, role, conversation_id)
        if valid:
            self.chat_messages[conversation_id][-1].update({'timestamp': self.timestamp})
            self.chat_messages[conversation_id][-1].update({'social_relations': str(self.social_relations),
                                                            'thoughts_to_do': str(self.thoughts),
                                                            'emotion': str(self.emotion),
                                                            'psystage': str(self.psystage),
                                                            }) 
        return valid
     
    def _process_carryover(self, content: str, kwargs: dict) -> str:
        '''
        overwrite ConversationAgent._process_carryover
        only add the last msg in the carryover list
        '''
        
        # Makes sure there's a carryover
        if not kwargs.get("carryover"):
            return content

        # if carryover is string
        if isinstance(kwargs["carryover"], str):
            content += "\nContext: \n" + kwargs["carryover"]
        elif isinstance(kwargs["carryover"], list):
            content += "\nContext: \n" +  kwargs["carryover"][-1] # ("\n").join([t for t in kwargs["carryover"]])
        else:
            raise AssertionError(
                "Carryover should be a string or a list of strings. Not adding carryover to the message."
            )
        return content
    
    def update_message_to_modules(self, message:Union[str, Dict]):
        message_to_pass = {
            'emotion_options': self.emotion.emotional_options, # TODO
        }
        
        if type(message) == str:
            message_to_pass.update({'full_interaction_history': message})
        elif type(message) == dict:
            message_to_pass.update(message)
        else: 
            raise NotImplemented
        
        assert 'last_message' not in message_to_pass['full_interaction_history'], f'Error: {message_to_pass}'
        
        message_to_pass.update(self.inner_states)
        message_to_pass.update({'inner_states': self.inner_states})
        
        for module in self.module_sequence:
            recipient: CognitiveModuleAgent = module['recipient']
            
            # build the message to be sent to the module by the functional prompt
            msg_func = module.get('message_func',recipient.functional_prompt)
            module['message'] = msg_func(message_to_pass)
    
    def suspend_group_chat(self):
        self.suspend_chat = True
    
    def resume_group_chat(self):
        self.suspend_chat = False
    
    def update_inner_states_from_dict(self, status:Dict):
        if status is None: 
            self.logger.info(f" no status loaded, maybe a human agent")
            assert self.human_input_mode == 'ALWAYS' # human agent
            return
        for key, value in status.items():
            if key not in self.inner_states: continue
            
            if type(value) == str: 
                try:
                    value = eval(value)
                except:
                    pass
        
            if hasattr(self.inner_states[key], 'from_dict'):
                self.inner_states[key].from_dict(value)
            elif type(value) == type(self.inner_states[key]):
                self.inner_states[key] = value
            else:
                self.logger.info(f'Error: {key} is not updated.')
                if os.getenv('DEBUG'):
                    __import__('ipdb').set_trace()

    def rollback(self, time, status):
        # backup_key = len(self.backup_messages)
        # self.backup_messages[backup_key] = copy.deepcopy(self.chat_messages)
        for recipient in self.chat_messages:
            self.chat_messages[recipient] = rollback_to_time(self.chat_messages[recipient], time)
            
        self.update_inner_states_from_dict(status)
        self.logger.info(f'{self.name} is rollback to {time}')
     
    async def monitor_chat_situation(self, new_situation):
        if new_situation - self.chat_situation_group >= 1: # new_situation is groupchat.update_count 
            return True
        else:
            while self.groupchat.update_count - self.chat_situation_group < 2:
                await asyncio.sleep(0.1)
