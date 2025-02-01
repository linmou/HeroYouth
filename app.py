import os
from pathlib import Path
import pandas as pd
from quart import Quart, jsonify, render_template, request, send_file, send_from_directory, websocket
from quart_cors import cors
import asyncio
import threading
import json
import asyncio

import requests

from constant.global_var import message_queue, conversation_started, DATA_STORE_ROOT
from server.simut_group_test import build_chatgroup

app = Quart(__name__, static_folder='static')
app = cors(app)  # Enable CORS for all routes

messages = []
clients = set()
with open('config/AZURE_CONFIG', 'r') as f:
    azure_config = json.load(f)
SPEECH_KEY = os.environ.get('AZURE_SPEECH_KEY') if azure_config.get('AZURE_SPEECH_KEY') is None else azure_config.get('AZURE_SPEECH_KEY')
SPEECH_REGION = os.environ.get('AZURE_SPEECH_REGION') if azure_config.get('AZURE_SPEECH_REGION') is None else azure_config.get('AZURE_SPEECH_REGION')
SPEECH_LANGUAGE = os.environ.get('AZURE_SPEECH_LANGUAGE') if azure_config.get('AZURE_SPEECH_LANGUAGE') is None else azure_config.get('AZURE_SPEECH_LANGUAGE')

chat_group=None

# class MessageWorker:
#     SPEECH_FILE = 'audio_record/output.mp3'
#     def __init__(self):
#         pass
        
#     async def put_message(self):
#         while True:
#             reply = {'content': 'dummy message', 'role': 'dummy role', 'speechFile': self.SPEECH_FILE}
#             await message_queue.put(json.dumps(reply))  # Push message to the queue
#             print(f'queue size {message_queue.qsize()}')
#             await asyncio.sleep(5)

async def generate_messages():
    await chat_group.start_chat()
        
def suspend_generate_message():
    chat_group.suspend_chat()

async def resume_generate_message():
    await chat_group.resume_chat()


@app.route('/user-analyse', methods=['POST'])
async def user_analyse():
    await chat_group.a_analyse_human_performance_all()
    chat_histories = {}
    chat_histories_dir = f'{DATA_STORE_ROOT}/user_analysis'
    
    # Get all JSON files in the chat_histories directory
    json_files = [f for f in os.listdir(chat_histories_dir) if f.endswith('.json')]
    
    # Load each JSON file and add it to chat_histories
    for file in json_files:
        character_name = Path(file).stem  # Remove .json extension
        with open(os.path.join(chat_histories_dir, file), 'r') as f:
            analysis = json.load(f)
            if type(analysis) == dict:
                assert len(analysis) == 1
                key = list(analysis.keys())[0] 
                assert type(analysis[key]) == list
                chat_histories[character_name] = analysis[key]
            elif type(analysis) == list:
                chat_histories[character_name] = analysis
            else:
                raise ValueError(f'Unexpected type for analysis: {type(analysis)}')
    
    ttl_constr, ttl_aggr = 0,0
    for char_anlys in chat_histories.values():
        for line in char_anlys:
            ttl_constr += line.get('constructive',0)
            ttl_aggr += line.get('aggressive',0)

    with open(f'{DATA_STORE_ROOT}/impression_from_others.json') as f:
        impression_from_others = json.load(f)
    
    return jsonify({
        'ttl_constr': ttl_constr,
        'ttl_aggr': ttl_aggr,
        'histories': chat_histories,
        'impression_from_others': impression_from_others
    })

@app.route('/roll-back', methods=['POST'])
async def roll_back():
    data = await request.json
    time = data.get('timestamp')
    chat_group.rollback(time)
    return jsonify({'status': 'success', 'message': 'Roll back successful'}), 200

def get_topk_emotions(emotion_data, topk=3):
    """ 
        emotion_data = {
        "P1": {
            "emotion": {
                "joy": 2, "trust": 4, "fear": 2, "surprise": 0, "sadness": 3, "disgust": 2, "anger": 3, "anticipation": 2
            }
        },
        "P2": {
            "emotion": {
                "joy": 4, "trust": 4, "fear": 1, "surprise": 1, "sadness": 7, "disgust": 2, "anger": 1, "anticipation": 9
            }
        }
    }
    """
    # top_k_emotions = {}
    # for char, data in emotion_data.items():
    #     sorted_emotions = sorted(data["emotion"].items(), key=lambda x: x[1], reverse=True)
    #     top_k_emotions[char] = {'emotion': dict(sorted_emotions[:topk])}
    
    sorted_emo = sorted(emotion_data.items(), key=lambda x: x[1], reverse=True)
    top_k_emotions = dict(sorted_emo[:topk]) 
    return top_k_emotions

@app.route('/get-inner-status')
async def get_inner_status():
    global chat_group
    if chat_group:
        status_dict = {}
        chat_group.update_all_agent_states()
        
        # interesting_status = ['emotion', 'psystage']
        # for agent in chat_group.agents:
        #     if agent == chat_group.human_agent:
        #         continue
        #     for status in interesting_status:
        #         status_dict[agent.name].update(agent.inner_states_dict.get(status, {}))
        
        if os.path.exists(f'{DATA_STORE_ROOT}/emotion.json'):
            with open(f'{DATA_STORE_ROOT}/emotion.json') as f:
                emotions = json.load(f)
        if os.path.exists(f'{DATA_STORE_ROOT}/psystage.json'):    
            with open(f'{DATA_STORE_ROOT}/psystage.json') as f:
                psystages = json.load(f)
                
        emotions = {k: json.loads(v) for k,v in emotions.items()}
        char2status = {}
        for k, v in emotions.items():
            if k!=chat_group.human_agent.name:
                emotion_ls = get_topk_emotions(v['__data__']['emotion'])
                complex_emo = v['__data__']['complex_emotion']
                char2status.update( {k: {'emotion':emotion_ls, 'complex_emotion':complex_emo}} )
                char2status[k].update({'psystage': str(psystages.get(k, {}))[1:-1] }) 
            # status_dict['emotions'] = decoded_emotions

        return jsonify(char2status)
    return jsonify([])

@app.route('/public-input', methods=['POST'])
async def handle_input():
    data = await request.json
    user_input = data.get('input')
    response = await chat_group.a_get_human_input(user_input)
    return jsonify({'response': response})


@app.route('/public-messages', methods=['POST'])
async def public_messages():
    return chat_group.messages_and_states
    # if os.path.exists(f'{DATA_STORE_ROOT}/groupchat.csv'):
    #     df = pd.read_csv(f'{DATA_STORE_ROOT}/groupchat.csv')
    #     print(df.to_dict('records')[-1])
    #     records = df.tail().to_dict('records')
    #     return jsonify([str(record) for record in records])
    # else:
    #     return jsonify([])

@app.route('/dm-input', methods=['POST'])
async def dm_input():
    data = await request.json
    user_input = data.get('message')
    recipient = data.get('recipient')
    response = await chat_group.a_direct_message(recipient=recipient, message=user_input)
    return jsonify({})
    # return jsonify({'response': response})

@app.route('/dm-history', methods=['POST'])
async def dm_history():
    data = await request.json
    recipient = data.get('recipient')
    return chat_group.get_dm_history(recipient)

@app.route('/')
async def serve_index():
    # return await send_from_directory(app.static_folder, 'splited_index.html')
    return await render_template('index.html')

@app.route('/analyse')
async def analyse():
    return await render_template('analyse.html')
    
@app.route('/<path:path>')
async def serve_static(path):
    return await send_from_directory(app.static_folder, path)

@app.websocket('/ws')
async def ws():
    clients.add(websocket._get_current_object())
    print("WebSocket connection established")
    try:
        while True:
            message = await message_queue.get()  # Consume message from the queue
            # print(f"Message retrieved from queue: {message}")
            for client in clients:
                await client.send(message)
                # print(f"Message sent to client: {message}")
            message_queue.task_done()
    except asyncio.CancelledError:
        pass
    finally:
        clients.remove(websocket._get_current_object())
        print("WebSocket connection closed")

@app.route('/get-token', methods=['GET'])
async def get_token():
    return jsonify({'token': SPEECH_KEY, 'region': SPEECH_REGION, 'language': SPEECH_LANGUAGE})

@app.route('/suspend-conversation', methods=['POST'])
async def suspend_conversation():
    global conversation_started
    if conversation_started:
        suspend_generate_message()
        conversation_started = False
        return jsonify({'status': 'success', 'message': 'Conversation suspended'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Conversation not started'}), 400

@app.route('/resume-conversation', methods=['POST'])
async def resume_conversation():
    global conversation_started
    if not conversation_started:
        conversation_started = True
        app.add_background_task(resume_generate_message)
        return jsonify({'status': 'success', 'message': 'Conversation started'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Conversation already started'}), 400

@app.route('/start-conversation', methods=['POST'])
async def start_conversation():
    global conversation_started
    if not conversation_started:
        conversation_started = True
        app.add_background_task(generate_messages)
        return jsonify({'status': 'success', 'message': 'Conversation started'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Conversation already started'}), 400

@app.route('/set-username', methods=['POST'])
async def set_username():
    data = await request.json
    username = data.get("username")
    global chat_group 
    chat_group = build_chatgroup(username)
    return jsonify({'status': 'success', 'message': f'Username is set as {chat_group.human_agent.name}'}), 200

@app.before_serving
async def startup():
    pass

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)