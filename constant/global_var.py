from asyncio import Queue
from datetime import datetime
from pathlib import Path

message_queue = Queue()

def put_message(message):
    message_queue.put_nowait(message)
    
conversation_started = False

RECORD_DIR='data_record'
THIS_MOMENT = datetime.strftime(datetime.now(), '%m-%d-%H:%M')
DATA_STORE_ROOT = Path(f'{RECORD_DIR}/{THIS_MOMENT}')

TIMESTAMP_FORMAT = '%H:%M:%S'  # time format for the timestamp in the chat history

VICTIM_NAME = 'Victeem'