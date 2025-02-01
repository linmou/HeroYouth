from server.utilities.serialization import serializable

@serializable
class PsyStageBully:
    # 1. Contempt for victim: the bully views the victim with contempt or disdain.
    #     2. Awareness of wrongdoing: Beginning of a shift in the bully's perspective. The bully starts to realize that their behavior is wrong and harmful.
    #     3. Cognitive dissonance:  bully experiences discomfort due to the conflict between their previous behavior and their growing awareness that it was wrong
    #     4. Emotional understanding: As the bully processes their cognitive dissonance, they may develop a deeper emotional understanding of the harm they have caused. This stage involves empathy, where the bully starts to emotionally connect with the victim's experience
    #     5. Value internalization
    STATES = ['Contempt for victim', 'Awareness of wrongdoing', 'Cognitive dissonance', 'Emotional understanding', 'Value internalization']
    def __init__(self, state) -> None:
        assert state in self.STATES, f'Invalid state {state}'
        self.state = state
    def update(self, state):
        self.state = state
        
    def __str__(self):
        return self.state
    
    def to_dict(self):
        return {'psystage': self.state}
    
    @classmethod
    def from_dict(cls, data):
        return cls(state=data['psystage'])

@serializable
class PsyStageVictim:
    STATES = [
        (-1, "Feeling relieved"),
        (1, "Confusion and bewilderment"),
        (2, "Guilt and shame"),
        (3, "Depression and isolation"),
        (4, "Long-term psychological trauma"),
        (4.5, "Trauma recovery period")
    ]

    def __init__(self, state=0, state_name=None, move_step=0.5):
        self.state = state
        if state_name:
            for i, (state, name) in enumerate(self.STATES):
                if state_name == name:
                    self.state = state
                    break
        self.move_step = move_step

    def get_state_name(self):
        for i, (state, name) in enumerate(self.STATES):
            if self.state == state:
                return name
            if self.state < state:
                return self.STATES[max(0, i-1)][1]
        return self.STATES[-1][1]
    
    def update(self, intervention: bool):
        if intervention:
            if self.state == 4:  # Long-term psychological trauma
                self.state = 4.5  # Trauma recovery period
            elif self.state == 4.5:  # Trauma recovery period
                pass  # Stay in trauma recovery period
            elif self.state > 0:
                self.state = max(self.state - self.move_step, 0)
                self._round_state()
                
        else:
            if self.state == 4.5:  # Trauma recovery period
                self.state = 4  # Long-term psychological trauma
            elif self.state < 4:
                self.state = min(self.state + self.move_step, 4)
                self._round_state()

    def _round_state(self):
        self.state = round(self.state * 2) / 2


    def __str__(self):
        return f"{self.get_state_name()}"
    
    def to_dict(self):
        return{
           'psystage': self.get_state_name()
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(state_name=data['psystage'])
    
if __name__ == '__main__':
    victim = PsyStageVictim()
    print(victim)
    actions = [1,0,0,0,0,1,0,0,0,0,0,0,0,1,1,1,1,1,1]

    for action in actions:
        victim.update(action)
        print(f"Action: {action}, stage {victim}")