import openai
import json

class ChatGPT:
    def __init__(self, api_key) -> None:
        openai.api_key = api_key
        #self.dialog = [{'role': 'system', 'content': role}]
        self.dialog = []
    
    def question(self, n_questions, topic, difficulty):
        
        PROMPT = f'''
        You are a professor teaching students in computer science where they have to learn programming with Python.
        This week you want to teach them about \"{topic}\".
        You want to create {n_questions} programming exercises for students to test their abilities. 
        Each exercise should be {difficulty}.
        Return a json list where each entry is an exercise consisting of the \"question\" (text), the \"solution\" (Python code), \"tests\" a list of multiple unit tests (Python code). 
        The question should be in german.
        '''
        
        self.dialog.append({'role':'system','content': PROMPT})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.dialog,
        )
        answer = response.choices[0].message.content
        self.dialog.append({'role':'assistant','content': answer})
        
        print(answer)
        exercises = json.loads(answer)
        return exercises
