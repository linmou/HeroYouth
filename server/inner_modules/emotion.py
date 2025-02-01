from collections import defaultdict
from typing import Dict
import random
import json

from server.utilities.serialization import serializable

@serializable
class Emotion:
    """Emotion of the agent. It is a dictionary of several emotions, each with a float value between 0 and 10.
    """
    emotional_options = [ "trust", "fear", "sadness", "anger", "anticipation", "disgust", "joy", "surprise"]
    positive_emotions = [ "trust", "anticipation", "surprise"] # 
    negative_emotions = ["fear", "sadness", "anger", "disgust"] #"", 
    emoji_dict = {
        'anticipation': '🤞',
        'anger': '😡',
        'disgust': '🤢',
        'sadness': '😢',
        'fear': '😨',
        'trust': '🤝',
        'joy': '😊',
        'surprise': '😲'
    }

    complex_emotion_formula_zh = {
        'aggressiveness': ({'anticipation', 'anger'}, '😡🔥'),
        'contempt': ({'disgust', 'anger'}, '😤😒'),
        'remorse': ({'sadness', 'disgust'}, '😔😞'),
        'disapproval': ({'surprise', 'sadness'}, '😮😟'),
        'awe': ({'fear', 'surprise'}, '😨😲'),
        'submission': ({'trust', 'fear'}, '😌🙏'),
        'love': ({'joy', 'trust'}, '😍❤️'),
        'optimism': ({'anticipation', 'joy'}, '😄😊')
    }

    
    def __init__(self, emotion: Dict[str, float]=None, update_alpha=0.7, decay_alpha=0.01) -> None:
        self.emotion = dict()
        self.random_init_emotions()
        if emotion is not None:
            for k, v in emotion.items(): 
                v = float(v)
                assert 0 <= v <= 10, f"the emotions should be kept between 0 and 10. Your emotion is {emotion}"
                if k in self.emotional_options:
                    self.emotion[k] = v
        self.update_alpha = update_alpha # the weight of the new emotion value
        self.passive_decay_alpha = decay_alpha # the decay rate of the emotion when there is no new emotion input
        self.impressive_event:dict[str,dict[str, str]] = dict() # the event that causes the emotion
    
    def random_init_emotions(self):
        """
        Ensure the initial emotion is not too extreme.
        """
        for key in self.emotional_options:
            if random.random() < 0.1:
                self.emotion[key] = random.randint(6, 10)
            elif random.random() < 0.8:
                self.emotion[key] = random.randint(0, 4)
            else:
                self.emotion[key] = random.randint(4, 6) 
    
    def update(self, emotions: list[dict]=None) -> None:
        '''
        "emotions": [
            {
                "emotion": "joy",
                "change": 4,
                "explanation": "I feel much happy beacause I get a gift from my friend Jay."
            },
            {
                "emotion": "trust",
                "change": 2,
                "explanation": "I trust my Jay, he is a kind man."
            },
            {
                "emotion": "supprise",
                "change": 2,
                "explanation": "I am supprised that Jay gives me a gift. I didn't expect that. And the gift happend to be on my gift list."
            }
        ]
        '''
        if emotions is None:
            self.passive_update()
        else:
            for emotion in emotions:
                emo_name, intensity_change, event = emotion.get('emotion'), emotion.get('change'), emotion.get('explanation')
                try:
                    self.update_single_emotion(emo_name, intensity_change, event)
                except:
                    pass
                    
    def update_single_emotion(self, emotion: str, intensity_change: float, event:str = None) -> None:
        assert emotion in self.emotional_options, f"the emotion should be in the emotional_options. Your emotion is {emotion}"
        intensity_change =  max(-5, min(intensity_change , 5))
        self.emotion[emotion] += intensity_change # self.update_alpha * intensity + (1 - self.update_alpha) * self.emotion[emotion] may exceed 1
        self.emotion[emotion] = min(self.emotion[emotion] ,10)
        self.emotion[emotion] = max(self.emotion[emotion] ,0) 
        if event:
            self.impressive_event_update(emotion, intensity_change, event)        
    
    def passive_update(self, emotion=None, decay_alpha=None):
        if decay_alpha is None: decay_alpha = self.passive_decay_alpha
        
        if emotion is None: # update all the emotions in the current state
            for key in self.emotion.keys():
                if self.emotion[key] > 7: 
                    self.emotion[key] -= self.emotion[key] * random.uniform(0, 10) * decay_alpha # exptreme high emotion will randomly decrease by 0~10%
                    self.emotion[key] -= self.emotion[key] * random.randrange(0, 10) * decay_alpha # exptreme high emotion will randomly decrease by 0~10%
                else:
                    self.emotion[key] += self.emotion[key] * random.randrange(0, 5) * decay_alpha # normal emotion will randomly in/decrease by 0~5%
        else:
            if self.emotion[emotion] > 7: 
                self.emotion[emotion] -= self.emotion[emotion] * random.randrange(-5, 5) * decay_alpha 
            else:
                self.emotion[emotion] += self.emotion[emotion] * random.randrange(-5, 5) * decay_alpha
        for emo in self.emotion.keys():
            self.emotion[emo] = max(0, min(10, round(self.emotion[emo], 2)))
                
    def impressive_event_update(self, emotion, emotion_delta, event:str):
        pre_emo_dif = self.impressive_event.get(emotion, dict()).get('emo_delta', 1) 
        if pre_emo_dif < emotion_delta:
            self.impressive_event[emotion].update({'emo_delta': emotion_delta, 'event': event})
        else: 
            self.impressive_event[emotion].update({'emo_delta': min(1, pre_emo_dif-self.passive_decay_alpha*50), 'event': event})
            
    @property
    def complex_emotion(self) -> str:
        '''
        More complex emotions can be represented using combinations of the above emotions, for example:
            - agreesiveness = anticipation + anger
            - contempt = disgust + anger
            - remorse = sadness + disgust
            - disapproval = surprise + sadness
            - awe = fear + surprise
            - submission = trust + fear
            - love = joy + trust
            - optimism = anticipation + joy
        '''
        
        highest_two_emo = sorted(self.emotion.items(), key=lambda x: x[1], reverse=True)[:2]
        emo1, emo2 = highest_two_emo[0][0], highest_two_emo[1][0]
        for key, value in self.complex_emotion_formula_zh.items():
            if set([emo1, emo2]) == value[0]:
                return {"emotion": key, "emoji": value[1]}
        
        emotion = list(self.extreme_emotion.keys())[0]
        return {"emotion": emotion, "emoji": self.emoji_dict[emotion]}
            
    @property
    def impression(self) -> Dict[str, float]:
        return self.emotion
     
    @property
    def most_impressive_event(self):
        '''
        return event_description and event emotion
        '''
        highest_emo_delta = 0
        impressive_event, event_emo = '',''
        for key in self.impressive_event.keys():
            emo_delta = self.impressive_event[key].get('emo_delta',0) 
            if emo_delta > highest_emo_delta:
                highest_emo_delta = emo_delta
                impressive_event = self.impressive_event[key].get('event', None)
                event_emo = key
                assert impressive_event is not None, f'event is None, your event is {impressive_event}'
        return impressive_event, event_emo
         
    @property
    def extreme_emotion(self) -> dict:
        ext_emo_cate = max(self.emotion, key=self.emotion.get)
        return {ext_emo_cate: f"{self.emotion[ext_emo_cate]}/10"}

    @property
    def extreme_emotion_name(self) -> dict:
        ext_emo_cate = max(self.emotion, key=self.emotion.get)
        return ext_emo_cate

    @property
    def extreme_emotion_value(self) -> dict:
        ext_emo_cate = max(self.emotion, key=self.emotion.get)
        return self.emotion[ext_emo_cate]
    
    def __repr__(self) -> str:
        return f"""Emotion: {self.emotion}
                Extreme Emotion: {self.extreme_emotion}"""
    
    def to_dict(self):
        return{
            'emotion': self.emotion,
            'extreme_emotion': self.extreme_emotion,
            'impressive_event': self.impressive_event,
            'complex_emotion': self.complex_emotion,
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(emotion=data['emotion'])
                
                
if __name__ == '__main__':
    print(Emotion().emotional_options)