
from .assign import Assignment

class Project:
    def __init__(self, config):
        self.config = config
        self.exercises = [Assignment(self.config, name=exercise['exercise'], assignment=False) for exercise in self.config.exercises]
        self.assignments = [Assignment(self.config, name=exercise['exercise'], assignment=True) for exercise in self.config.assignments]

    def init(self, exist_ok=True) -> None:
        self.config.root_dir.mkdir(parents=True, exist_ok=True)
        self.config.assign.main_dir.mkdir(parents=True, exist_ok=exist_ok)
        self.config.assign.students_dir.mkdir(parents=True, exist_ok=exist_ok)
        self.config.assign.solutions_dir.mkdir(parents=True, exist_ok=exist_ok)
        self.config.assign.autograder_dir.mkdir(parents=True, exist_ok=exist_ok)
    
    def init_notebooks(self, override=False, exist_ok=False) -> None:
        for exercise in self.exercises:
            exercise.init_notebook(save=True, override=override, exist_ok=exist_ok)
            
        for assignment in self.assignments:
            assignment.init_notebook(save=True, override=override, exist_ok=exist_ok)
            
    def generate_all(self, run_tests=True) -> None:
        for exercise in self.exercises:
            exercise.generate(run_tests=run_tests)
            
        for assignment in self.assignments:
            assignment.generate(run_tests=run_tests)        
    
    def all_assignments(self) -> list[Assignment]:
        return self.exercises + self.assignments
    
    def __repr__(self) -> str:
        out = 'exercises: ['
        for exercise in self.exercises:
            out += f'{exercise},'
        out = out[0:-1] + ']'
        
        out = 'assignments: ['
        for assignment in self.assignments:
            out += f'{assignment},'
        out = out[0:-1] + ']'
        
        return out