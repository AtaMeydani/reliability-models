import numpy as np

class Component:
    """
    Represents a single node (component) in the system graph.
    """
    def __init__(self, name, lam, mu=0.0, capacity=1.0):
        self.name = name
        self.lam = lam
        self.mu = mu
        self.capacity = capacity
        
        self.is_working = True
        self.next_event_time = 0.0
        self.next_event_type = 'FAILURE'
        
        self.schedule_next_event(0.0)

    def schedule_next_event(self, current_time, rng=None, failure_multiplier=1.0):
        """
        Calculates when the next state change will happen based on 
        current state and exponential distributions.
        """
        rng = rng if rng is not None else np.random
        if self.is_working:
            if self.lam > 0:
                duration = rng.exponential(1.0 / (self.lam * failure_multiplier))
                self.next_event_time = current_time + duration
                self.next_event_type = 'FAILURE'
            else:
                self.next_event_time = float('inf')
                self.next_event_type = 'NONE'
        else:
            if self.mu > 0:
                duration = rng.exponential(1.0 / self.mu)
                self.next_event_time = current_time + duration
                self.next_event_type = 'REPAIR'
            else:
                self.next_event_time = float('inf')
                self.next_event_type = 'NONE'

    def toggle_state(self):
        self.is_working = not self.is_working
        return self.is_working

    def reset(self, rng=None):
        self.is_working = True
        self.schedule_next_event(0.0, rng)
