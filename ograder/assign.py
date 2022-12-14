
import nbformat
import subprocess
import shutil
import yaml

from .utils import peek, is_empty
from otter.utils import loggers
from pathlib import Path
from ograder.config import Config
import warnings

LOGGER = loggers.get_logger(__name__)

class Assignment():
    def __init__(self, config, name, assignment=False):
        self.name = name
        
        # this is a little inefficient
        self.instructions = config.otter_notebook_config.export_cell.instructions
        if assignment:
            for exercise in config.exercises:
                if exercise['exercise'] == name and exercise['instructions'] != None:
                    self.instructions = exercise['instructions']
        else:
            for exercise in config.assignments:
                if exercise['exercise'] == name and exercise['instructions'] != None:
                    self.instructions = exercise['instructions']

        self.assignment = assignment
        self.config : Config = config
        self.main_dir : Path = config.assign.main_dir / Path(name)
        self.student_dir : Path = config.assign.students_dir / Path(name)
        self.solution_dir : Path = config.assign.solutions_dir / Path(name)
        self.autograder_dir : Path = config.assign.autograder_dir / Path(name)
        self.tmp_dir : Path = config.assign.tmp_dir / Path(name)
        #self.notebook = self.__read_notebook(self.main_dir)
        
    def upgrade_notebook(self) -> None:
        notebook = self.__read_notebook()
        if notebook == None:
            LOGGER.warn(f'Could not upgrade notebook for assignment {self}, since it does not exists.')
            return
        cells = notebook.cells
                
        otter_config_dict = self.config.otter_notebook_config.get_user_config()
        otter_config_dict['name'] = self.name
        if self.instructions != None:
            otter_config_dict['export_cell']['instructions'] = self.instructions
        otter_raw_config = yaml.safe_dump(otter_config_dict, allow_unicode=True)
        
        
        if len(cells) == 0:
            cells.append(nbformat.v4.new_raw_cell(otter_raw_config))
        else:
            new_cells = list(cells)
            cells.clear()
            cells.append(nbformat.v4.new_raw_cell(otter_raw_config))
            first = True
            for cell in new_cells:
                if not first:
                    cells.append(cell)
                first = False
        notebook.cells = cells
        print(notebook)
        self.__save(notebook, override=True, exist_ok=True)
        
    
    def init_notebook(self, save=True, override=False, exist_ok=False) -> nbformat.NotebookNode:
        cells = []
        otter_config_dict = self.config.otter_notebook_config.get_user_config()
        otter_config_dict['name'] = self.name
        if self.instructions != None:
            otter_config_dict['instructions'] = self.instructions
        otter_raw_config = yaml.safe_dump(otter_config_dict, allow_unicode=True)

        cells.append(nbformat.v4.new_raw_cell(otter_raw_config))
        notebook = nbformat.v4.new_notebook(cells=cells)
        
        if save:
            self.__save(notebook, override, exist_ok)
        return notebook
    
    def __save(self, notebook, override=False, exist_ok=False) -> None:
        self.main_dir.mkdir(parents=True, exist_ok=True)
        if self.main_notebook_exists():
            notebook_path = self.__find_notebook(self.main_dir)
        else:
            notebook_path = self.main_dir / Path(self.name + '.ipynb')
            
        if notebook_path.exists() and override:
            notebook_path.unlink()
        
        if notebook_path.exists() and not exist_ok:
            warnings.warn(f'Could not create notebook {notebook_path} since it already exists!')
        else:
            with open(str(notebook_path), mode='w', encoding='utf-8') as file:
                try:
                    file.write(nbformat.writes(notebook))
                    #nbformat.write(notebook, file) 
                except Exception as e:
                    LOGGER.error(f'Could not write to {file}.')        
    
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
             
    def main_notebook_exists(self) -> bool:
        if self.main_dir.exists():
            return not is_empty(self.main_dir.glob('*.ipynb'))
        return False
     
    def remove_notebooks(self, main=False) -> None:
        self.remove_student_notebook()
        self.remove_solution_notebook()
        self.remove_autograding_notebook()
        if main:
            self.remove_main_notebook()    
        
    def remove_main_notebook(self) -> None:
        if self.main_dir.exists():
            shutil.rmtree(str(self.main_dir))
            #print(f'remove {self.main_dir}')
        
    def remove_student_notebook(self) -> None:
        if self.student_dir.exists():
            shutil.rmtree(str(self.student_dir))
            #print(f'remove {self.student_dir}')
    
    def remove_solution_notebook(self) -> None:
        if self.solution_dir.exists():
            shutil.rmtree(str(self.solution_dir))
            #print(f'remove {self.solution_dir}')
            
    def remove_autograding_notebook(self) -> None:
        if self.autograder_dir.exists():
            shutil.rmtree(str(self.autograder_dir))
            #print(f'remove {self.autograder_dir}')
    
    def __read_notebook(self) -> nbformat.NotebookNode:
        path_to_notebook, _ = peek(self.main_dir.glob('*.ipynb'))
        if path_to_notebook != None:
            print(path_to_notebook)
            with open(path_to_notebook, mode='r', encoding='utf-8') as file:
                try:
                    notebook = nbformat.read(file, as_version=nbformat.NO_CONVERT)
                    return notebook
                except Exception as e:
                    LOGGER.error(f'Could not read from {file}')
                    return None
        
    def __find_notebook(self, dir : Path) -> Path:
        return next(dir.glob('*.ipynb'))
    
    def __find_zip(self, dir: Path) -> Path:
        return next(dir.glob('*.zip'))
    
    def __repr__(self) -> str:
        return f'{self.name}'