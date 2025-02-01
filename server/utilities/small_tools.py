from datetime import datetime
import os
import glob
import re
import subprocess

from constant.global_var import TIMESTAMP_FORMAT


def keep_latest_k_files(folder_path, k, suffix=".mp3"):
    # Get all files with suffix in the folder
    interest_files = glob.glob(os.path.join(folder_path, f"*{suffix}"))
    
    # Sort files by modification time (newest first)
    interest_files.sort(key=os.path.getmtime, reverse=True)
    
    # Remove files if there are more than K
    if len(interest_files) > k:
        files_to_delete = interest_files[k:]
        for file_path in files_to_delete:
            os.remove(file_path)
            # print(f"Deleted: {file_path}")
            

def get_audio_duration(file_path):
    result = subprocess.run(
        [
            'ffprobe', '-i', file_path, '-show_entries', 'format=duration',
            '-v', 'quiet', '-of', 'csv=p=0'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    duration = float(result.stdout)
    return duration

def extract_json_from_markdown(markdown_text):
        # Regular expression to match the content inside ```json``` tags
        pattern = r'```json\n(.*?)```'
        # Find all matches
        matches = re.findall(pattern, markdown_text, re.DOTALL)
        # If there are matches, return the first one
        if matches:
            # Remove leading and trailing whitespace and newlines
            json_content = matches[0].strip()
            return json_content
        else:
            return markdown_text
        
def rollback_to_time(data, time_str):
    """
    Rolls back the list of dictionaries to a specific time.
    
    Args:
        data (list of dict): The list of dictionaries to rollback.
        time_str (str): The time in the format TIMESTAMP_FORMAT to roll back to.
    
    Returns:
        list of dict: The rolled back list of dictionaries.
    """
    target_time = datetime.strptime(time_str, TIMESTAMP_FORMAT)
    rolled_back_data = []
    
    for item in data:
        assert 'timestamp' in item, f'The item does not have a timestamp field. Item: {item}'
        item_time = datetime.strptime(item['timestamp'], TIMESTAMP_FORMAT)
        if item_time <= target_time:
            rolled_back_data.append(item)
    
    return rolled_back_data
        
ANALYSE_PROMPT = '''
You are a helpful teacher. Now you are going to analyse if the reaction of the user is proper in the social context.

Please analyse each line of this user's behavior, as detailed as possible. Do not analyse other roles.

You will receive a json object in the following JSON format,

for example:
input:
[
    {{"role":"CharC", "content":"How are you?"}},
    {{"role":"User', "content":"I am fine."}}, 
    {{"role":"CharC", "content":"Have your heard about the party tonight?"}},
    {{"role":"User', "content":"What!?!? I am not invited again?"}},
]
return in this format
{{
    "output": 
    [
        {{"role":"CharC", "content":"How are you?", "analyse": "null"}},
        {{"role":"User', "content":"I am fine.", "analyse": "The student reacts in a polite manner."}}, 
        {{"role":"CharC", "content":"Have your heard about the party tonight?", "analyse": "null"}},
        {{"role":"User', "content":"What!?!? I am not invited again?", "analyse": "While this response conveys strong emotion, it is not necessarily impolite. The use of an exclamation ("What!?!?") might seem dramatic, but it is a valid way to express surprise and disappointment. The student is not being rude or aggressive; they are simply voicing their feelings. This can be seen as a legitimate reaction to a perceived social slight, especially if the student feels consistently excluded."}},
    ]
}}

Now analyse the following message history: 
{message_history}
'''