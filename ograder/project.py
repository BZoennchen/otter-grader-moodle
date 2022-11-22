
from .assign import Assignment

class Project:
    def __init__(self, config):
        self.config = config
        self.exercises = [Assignment(self.config, name=name, assignment=False) for name in self.config.exercises]
        self.assignments = [Assignment(self.config, name=name, assignment=True) for name in self.config.assignments]

    def init(self, exist_ok=True):
        self.config.root_dir.mkdir(parents=True, exist_ok=True)
        self.config.assign.main_dir.mkdir(parents=True, exist_ok=exist_ok)
        self.config.assign.students_dir.mkdir(parents=True, exist_ok=exist_ok)
        self.config.assign.solutions_dir.mkdir(parents=True, exist_ok=exist_ok)
        self.config.assign.autograder_dir.mkdir(parents=True, exist_ok=exist_ok)
    
    def init_notebooks(self, override=False, exist_ok=False):
        for exercise in self.exercises:
            exercise.init_notebook(save=True, override=override, exist_ok=exist_ok)
            
        for assignment in self.assignments:
            assignment.init_notebook(save=True, override=override, exist_ok=exist_ok)
            
    def generate_all(self, run_tests=True):
        for exercise in self.exercises:
            exercise.generate(run_tests=run_tests)
            
        for assignment in self.assignments:
            assignment.generate(run_tests=run_tests)        
    
    def all_assignments(self):
        return self.exercises + self.assignments
            
    