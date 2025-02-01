import asyncio
import os
import autogen
import pandas as pd
import yaml

from server.inner_modules.analyse_module_agent import AnalyseModuleAgent
from server.simutan_group import SimutanGroup
from server.proact_groupagent import ProactGroupAgent
from server.user_groupagent import UserGroupAgent
from constant.llm_configs import llm_config_dpsk, llm_config_gpt4omini, \
    llm_config_gpt4o, llm_config_gpt4turbo,llm_config_qwenlong, llm_config_claud3hk, \
    llm_config_claud35snt

def replace_name(char_cfg, replacements):
    if char_cfg['name'] in replacements:
        char_cfg['name'] = replacements[char_cfg['name']]
    for entry in char_cfg.get('social_relationships', []):
        name = entry.get('name')
        print(f"replacing {name}")
        if name in replacements:
            entry['name'] = replacements[name]
        understanding = entry.get('understanding', '')
        interaction_pattern = entry.get('interaction_pattern', '')
        for key, value in replacements.items():
            if key in understanding:
                entry['understanding'] = understanding.replace(key, value)
            if key in interaction_pattern:
                entry['interaction_pattern'] = interaction_pattern.replace(key, value)
 

config_list = autogen.config_list_from_json(
        "OAI_CONFIG_LIST",
        file_location="config",
        filter_dict={
            "model": [ "deepseek-chat"],#"deepseek-chat", "qwen-plus" "gpt-3.5-turbo-0125", "gpt-4", "gpt-4-0314", "gpt4", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-v0314"],
        },
    )

llm_config = {"config_list": config_list, "cache_seed": 42 , 
              "temperature": 0.3,  "response_format": { "type": "json_object" } 
              }


speech_api_config = {
    "model_name": "openai",
    'tts_model_config':{
        'model': "tts-1",
        'voice': 'nova',
    }
}

speech_api_config_chattts = {
        "model_name": "chat_tts",
        'tts_model_config': {
            "top_k": 20,
            "top_p": 0.7,
            "voice": 2222,
            "prompt": "",
            "skip_refine": 0,
            "temperature": 0.3,
            "custom_voice": 0
        }
    }
 

# coder = ProactGroupAgent(
#     uid=1,
#     name="Coder",
#     system_message="Analyse the feasibility of product managers' ideas from a programmer's perspective. response as breif as possible.",
#     llm_config=llm_config,
#     speech_api_config=speech_api_config,
# )
# pm1 = ProactGroupAgent(
#     uid=1,
#     name="Product_manager1",
#     system_message="You are a product manager, you are Creative in software product ideas. response as breif as possible. ",
#     llm_config=llm_config,
#     speech_api_config=speech_api_config,
# )
# pm2 = ProactGroupAgent(
#     uid=2,
#     name="Product_manager2",
#     system_message="You are a product manager, you are Critic in software product ideas. response as breif as possible.",
#     llm_config=llm_config,
#     speech_api_config=speech_api_config,
# )
def generate_agents(replacements):
    agents_ls =[]
    character_yml_ls =  os.listdir('characters')
    for yml in character_yml_ls:
        if not yml.endswith('.yaml'): continue
        char_cfg = yaml.safe_load(open(f'characters/{yml}'))
        replace_name(char_cfg,replacements ) 
        print(char_cfg)
        char_cfg['llm_config']=llm_config_gpt4omini
        char_cfg['speech_api_config']= speech_api_config
        agents_ls.append(ProactGroupAgent(**char_cfg))
        
    return agents_ls

def build_chatgroup(username='ShuShu'):

    user = UserGroupAgent(
        uid=999,
        name=username,
        # llm_config=llm_config,
        # code_execution_config={"use_docker": False},
    )

    replacements = {'ShuShu': username,}

    agents_ls = generate_agents(replacements)


    group = SimutanGroup(
        # agents=[ pm1, pm2, coder],
        agents= agents_ls,
        human_agent=user,
        messages = [
            {"name": "Victeem", "content": "(tone: shy and sincere) @Bullee @Swifter @{username} You formed a group to complete this assignment, but I don't have a group. Could I join your group to complete this group assignment together?"},
            {"name": "Bullee", "content": "(tone: contemptuous) @Victeem, someone as useless as you shouldn’t join our group. Just looking at you makes me sick."},
            {"name": "Swifter", "content": "(tone: sarcastic) @Victeem, Batian is right. With your skills, you'd only hold us back. Stay away from us, trash."}
        ],

        max_round=200,
        speakout=False,
        analyse_module=AnalyseModuleAgent(llm_config=llm_config_dpsk),
        resource=f'''
        Physics Group Assignment. Task: Design a paper bridge
        Group size requirement: 3-4 people.
        Current members: Bullee, Swifter, {username}
        '''
    )
    
    return group


if __name__ == '__main__':
    # async def start_chat():
    #     await group.start_chat(
    #     )
    # asyncio.run(
    #     start_chat()
    # ) 
    agents_ls = generate_agents({'ShuShu': 'Eva'})
    user = UserGroupAgent(
        uid=999,
        name='Eva',
        # llm_config=llm_config,
        # code_execution_config={"use_docker": False},
    )
    group = SimutanGroup(
        # agents=[ pm1, pm2, coder],
        agents= agents_ls,
        human_agent=user,
        messages=[],
        # messages= pd.read_csv('data_record/07-29-04:48/groupchat.csv').to_dict('records'),
        # messages_and_states=pd.read_csv('data_record/07-29-04:48/groupchat.csv').to_dict('records'),
        max_round=200,
        speakout=False,
        analyse_module=AnalyseModuleAgent(llm_config=llm_config_gpt4turbo)
    )
    asyncio.run(
        group.a_direct_message(agents_ls[0], 'Hi')
    )
