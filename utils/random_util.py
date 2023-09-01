"""
    Compile-time random variables are generated here.
    Seeded for reproducability
"""

import random
import string
import uuid


class RandomUtil():
    def __init__(self, seed):
        self.seed = seed

        self.rnd = random.Random()
        self.rnd.seed(123) # NOTE: Of course don't use a static seed in production

        # I can't imagine ever having a collision but ig this doesn't hurt
        self.function_names = []

    def generate_function_name(self):
        func_name = ''
        while func_name not in self.function_names:
            uuid_str =  str(uuid.UUID(int=self.rnd.getrandbits(128), version=4))
            func_name = 'func_' + uuid_str
            self.function_names.append(func_name)
        
        return func_name

    def generate_link_name(self):
        func_name = ''
        while func_name not in self.function_names:
            uuid_str =  str(uuid.UUID(int=self.rnd.getrandbits(128), version=4))
            func_name = 'link_' + uuid_str
            self.function_names.append(func_name)
        
        return func_name
    
    def generate_id(self):
        id_length = 6
        characters = string.ascii_lowercase + string.ascii_uppercase + string.digits
        return ''.join(self.rnd.choices(characters, k=id_length))
    
    