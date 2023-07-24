
from pathlib import Path
from .assign import Assignment
from .config import Config
from otter.utils import loggers

LOGGER = loggers.get_logger(__name__)

class Project:
    def __init__(self, config: Config):
        self.config = config
        self.exercises : list[Assignment] = [Assignment(self.config, name=exercise['exercise'], assignment=False) for exercise in self.config.exercises]
        self.assignments : list[Assignment] = [Assignment(self.config, name=exercise['exercise'], assignment=True) for exercise in self.config.assignments]

    def exists(self):
        """
        Returns:
            boolean: True if and only if the project already exists on the hard drive.
        """
        if not self.config.root_dir.exists():
            return False
        return (self.config.root_dir / Path(self.config.semester)).exists()

    def init(self, n=0, override=False, exist_ok=False) -> None:
        self.init_directories(exist_ok)
        self.init_notebooks(n, override, exist_ok)
    
    def init_directories(self, exist_ok=True) -> None:
        self.config.root_dir.mkdir(parents=True, exist_ok=True)
        self.config.assign.main_dir.mkdir(parents=True, exist_ok=exist_ok)
        self.config.assign.students_dir.mkdir(parents=True, exist_ok=exist_ok)
        self.config.assign.solutions_dir.mkdir(parents=True, exist_ok=exist_ok)
        self.config.assign.autograder_dir.mkdir(parents=True, exist_ok=exist_ok)
    
    def init_notebooks(self, n=0, override=False, exist_ok=False) -> None:
        for exercise in self.exercises:
            exercise.init_notebook(n, save=True, override=override, exist_ok=exist_ok)
            
        for assignment in self.assignments:
            assignment.init_notebook(n, save=True, override=override, exist_ok=exist_ok)
    
    def add_empty_questions(self, n: int):
        for exercise in self.exercises:
            exercise.add_empty_questions(n)
            
        for assignment in self.assignments:
            assignment.add_empty_questions(n)
    
    def grade_all(self, timeout=None, plot=False):
        for exercise in self.exercises:
            exercise.grade(timeout=timeout, plot=plot)
            
        for assignment in self.assignments:
            assignment.grade(timeout=timeout, plot=plot)
    
    def upgrade_notebooks(self, n=0) -> None:
        for exercise in self.exercises:
            exercise.upgrade_notebook(n)
            
        for assignment in self.assignments:
            assignment.upgrade_notebook(n)
    
    def generate_all(self, run_tests=True, seal_students_nb=True) -> None:
        for exercise in self.exercises:
            exercise.generate(run_tests=run_tests, seal_student_nb=seal_students_nb)
            
        for assignment in self.assignments:
            assignment.generate(run_tests=run_tests, seal_student_nb=seal_students_nb)
    
    def read_questions(self) -> None:
        for exercise in self.exercises:
            exercise.read_questions()
            
        for assignment in self.assignments:
            assignment.read_questions()        
    
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