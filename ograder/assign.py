
import nbformat
import subprocess
import shutil
import yaml

from .utils import peek
from otter.utils import loggers
from pathlib import Path
from ograder.config import Config
import warnings

LOGGER = loggers.get_logger(__name__)

class Assignment():
    def __init__(self, config, name, assignment=False):
        self.name = name
        self.assignment = assignment
        self.config : Config = config
        self.main_dir : Path = config.assign.main_dir / Path(name)
        self.student_dir : Path = config.assign.students_dir / Path(name)
        self.solution_dir : Path = config.assign.solutions_dir / Path(name)
        self.autograder_dir : Path = config.assign.autograder_dir / Path(name)
        self.tmp_dir : Path = config.assign.tmp_dir / Path(name)
        #self.notebook = self.__read_notebook(self.main_dir)
    
    def init_notebook(self, save=True, override=False, exist_ok=False):
        cells = []
        otter_config_dict = self.config.otter_notebook_config.get_user_config()
        otter_config_dict['name'] = self.name
        otter_raw_config = yaml.safe_dump(otter_config_dict, allow_unicode=True)

        cells.append(nbformat.v4.new_raw_cell(otter_raw_config))
        notebook = nbformat.v4.new_notebook(cells=cells)
        self.main_dir.mkdir(parents=True, exist_ok=True)
        if save:
            if self.main_notebook_exists():
                notebook_path = self.__find_notebook(self.main_dir)
            else:
                notebook_path = self.main_dir / Path(self.name + 'ipynb')
                
            if notebook_path.exists() and override:
                 notebook_path.unlink()
            
            if notebook_path.exists() and not exist_ok:
                warnings.warn(f'could not create notebook {notebook_path} since it already exists!')
            else:
                with open(str(notebook_path), mode='w', encoding="utf-8") as file:
                    nbformat.write(notebook, file) 
            #nbformat.write(notebook, str(self.main_dir / Path(self.name+'.ipynb')))        
        return notebook
    
    def generate(self, run_tests:bool=True) -> None:        
        try:
            # remove all generated noteobook if they are there
            self.remove_notebooks()
            
            if run_tests:
                LOGGER.info(f'otter assign {str(self.__find_notebook(self.main_dir))} {str(self.tmp_dir)}')
                subprocess.check_call(
                    ['otter', 'assign', str(self.__find_notebook(self.main_dir)), str(self.tmp_dir)])
            else:
                LOGGER.info(f'otter assign --no-run-tests {str(self.__find_notebook(self.main_dir))} {str(self.tmp_dir)}')
                subprocess.check_call(
                    ['otter', 'assign', '--no-run-tests', str(self.__find_notebook(self.main_dir)), str(self.tmp_dir)])
                
            # extract the student notebook
            self.student_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(self.tmp_dir / Path('student'), self.student_dir)
            
            # extract the zip file to grade
            self.remove_autograding_notebook()
            self.autograder_dir.mkdir(parents=True, exist_ok=True)
            zip_file = self.__find_zip(self.tmp_dir / Path('autograder'))
            zip_file.rename(self.autograder_dir / zip_file.name)
            
            # extract the solution notebook
            self.solution_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(self.tmp_dir / Path('autograder'), self.solution_dir)     
            shutil.rmtree(str(self.tmp_dir))   
        except subprocess.CalledProcessError as error:
            LOGGER.error(f'otter assign failed for assignment {self}: {error}')
        except Exception as error:
            LOGGER.error(f'otter assign failed for assignment {self}: {error}')
             
    def main_notebook_exists(self):
        if self.main_dir.exists():
            return peek(self.main_dir.glob('*.ipynb')) != None
        return False
     
    def remove_notebooks(self, main=False):
        self.remove_student_notebook()
        self.remove_solution_notebook()
        self.remove_autograding_notebook()
        if main:
            self.remove_main_notebook()    
        
    def remove_main_notebook(self):
        if self.main_dir.exists():
            shutil.rmtree(str(self.main_dir))
            #print(f'remove {self.main_dir}')
        
    def remove_student_notebook(self):
        if self.student_dir.exists():
            shutil.rmtree(str(self.student_dir))
            #print(f'remove {self.student_dir}')
    
    def remove_solution_notebook(self):
        if self.solution_dir.exists():
            shutil.rmtree(str(self.solution_dir))
            #print(f'remove {self.solution_dir}')
            
    def remove_autograding_notebook(self):
        if self.autograder_dir.exists():
            shutil.rmtree(str(self.autograder_dir))
            #print(f'remove {self.autograder_dir}')
    
    def __read_notebook(self, dir : Path) -> Path:
        return nbformat.read(str(dir / self.__find_notebook(dir)), as_version=nbformat.NO_CONVERT)
        
    def __find_notebook(self, dir : Path) -> Path:
        return next(dir.glob('*.ipynb'))
    
    def __find_zip(self, dir: Path) -> Path:
        return next(dir.glob('*.zip'))
    
    def __repr__(self):
        return f'{self.name}'