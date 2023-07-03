import nbformat
import subprocess
import shutil
import yaml

from .utils import peek, is_empty

from otter.utils import loggers
from pathlib import Path
from ograder.config import Config
from ograder.local_grader import LocalGrader
import warnings

LOGGER = loggers.get_logger(__name__)

class Question():
    def __init__(self, name, score, possible):
        self.name = name
        self.score = score
        self.possible = possible

class Assignment():
    def __init__(self, config: Config, name: str, assignment=False):
        self.name = name
        
        # this is a little inefficient
        self.instructions = config.otter_notebook_config.export_cell.instructions
        
        if assignment:
            documents = config.assignments
        else:
            documents = config.exercises
            
        for exercise in documents:
            if exercise['exercise'] == name:
                #self.number_of_questions = exercise['number_of_questions'] if exercise['number_of_questions'] > 0 else 0
                if exercise['instructions'] != None:
                    self.instructions = exercise['instructions']
                

        self.assignment = assignment
        self.config : Config = config
        self.main_dir : Path = config.assign.main_dir / Path(name)
        self.student_dir : Path = config.assign.students_dir / Path(name)
        self.solution_dir : Path = config.assign.solutions_dir / Path(name)
        self.autograder_dir : Path = config.assign.autograder_dir / Path(name)
        self.submission_dir: Path = config.assign.submission_dir / Path(name)
        self.tmp_dir : Path = config.assign.tmp_dir / Path(name)
        #self.notebook = self.__read_notebook(self.main_dir)
        
    def upgrade_notebook(self, n=0) -> None:
        requires_update = False
        notebook = self.__read_notebook()
        if notebook == None:
            LOGGER.info(f'Could not upgrade notebook for assignment {self}, since it does not exists. Therefore it will be initialized.')
            notebook = self.init_notebook(n, save=True)
            #notebook = self.__read_notebook()
            requires_update = True
        else:
            questions = self.read_questions(notebook)
            if n > len(questions):
                self.add_questions(n-len(questions), notebook)
                requires_update = True
        
        cells = notebook.cells
                
        otter_config_dict = self.config.otter_notebook_config.get_user_config()
        
        if peek(self.main_dir.glob('requirements.txt'))[0] != None:
            otter_config_dict['requirements'] = 'requirements.txt'
            
        files = []
        for file in self.main_dir.rglob('[!.]*'):
            rel_file = file.relative_to(self.main_dir)
            if not str(rel_file).startswith('.') and not file.is_dir() and not str(rel_file).endswith('.ipynb'):
                files.append(str(rel_file))
        otter_config_dict['files'] = files
        
        otter_config_dict['name'] = self.name
        if self.instructions != None:
            otter_config_dict['export_cell']['instructions'] = self.instructions
            
        otter_raw_config = self.__to_otter_meta(yaml.safe_dump(otter_config_dict, allow_unicode=True))

        if len(cells) == 0:
            cells.append(nbformat.v4.new_raw_cell(otter_raw_config))
            LOGGER.info(f'Insert missing config cell of {self}.')
        else:
            # Check that the cell is a raw cell to prevent the removal of important cells
            if cells[0].cell_type == "raw" and cells[0].source != otter_raw_config:
                cells[0] = nbformat.v4.new_raw_cell(otter_raw_config)
                requires_update = True
            elif cells[0].cell_type != "raw":
                LOGGER.error(f'Could not update notebook {self} since its first cell has a different type than "raw".')
                return
            
        if requires_update:
            LOGGER.info(f'Update {self}.')
        
            # set kernel spec
            #notebook.metadata['kernelspec'] = {'language': 'python', 'name': 'python3'}
            notebook.nbformat = 4
            notebook.nbformat_minor = 5
            
            notebook = self.__normalize(notebook)
            self.__save(notebook, override=True, exist_ok=True)
        else:
            LOGGER.info(f'No update required for {self}.')
        
    def __normalize(self, notebook):
        nchanges, notebook = nbformat.validator.normalize(notebook)
        return notebook
        
    def __to_otter_meta(self, raw):
        return '# ASSIGNMENT CONFIG\n' + raw
    
    def __question_cells(self, n:int, k:int=0):
        points = 1
        #k = len(self.read_questions())
        cells = []
        for i in range(n):
            q_begin = f'# BEGIN QUESTION\nname: q{i+1+k}\npoints: {points}'
            cell = nbformat.v4.new_raw_cell(q_begin)
            cells.append(cell)
            
            q_question_text = f'***Aufgabe {i+1+k}.***'
            cell = nbformat.v4.new_markdown_cell(q_question_text)
            cells.append(cell)
            
            q_begin_sol = f'# BEGIN SOLUTION'
            cell = nbformat.v4.new_raw_cell(q_begin_sol)
            cells.append(cell)
            
            cell = nbformat.v4.new_code_cell()
            cells.append(cell)
            
            q_end_sol = f'# END SOLUTION'
            cell = nbformat.v4.new_raw_cell(q_end_sol)
            cells.append(cell)
            
            q_begin_tests = f'# BEGIN TESTS'
            cell = nbformat.v4.new_raw_cell(q_begin_tests)
            cells.append(cell)
            
            cell = nbformat.v4.new_code_cell()
            cells.append(cell)
            
            q_end_tests = f'# END TESTS'
            cell = nbformat.v4.new_raw_cell(q_end_tests)
            cells.append(cell)
            
            q_end = f'# END QUESTION'
            cell = nbformat.v4.new_raw_cell(q_end)
            cells.append(cell)
        return cells
    
    def add_questions(self, n: int, notebook=None, save=True) -> None:
        if notebook == None:
            notebook = self.__read_notebook()
        cells = notebook.cells
        cells.extend(self.__question_cells(n, len(self.read_questions(notebook))))
        if save:
            self.__save(notebook, override=True, exist_ok=True)
        
        
    def init_notebook(self, n=0, save=True, override=False, exist_ok=False) -> nbformat.NotebookNode:
        cells = []
        otter_config_dict = self.config.otter_notebook_config.get_user_config()
        otter_config_dict['name'] = self.name
        if self.instructions != None:
            otter_config_dict['instructions'] = self.instructions
        otter_raw_config = self.__to_otter_meta(yaml.safe_dump(
            otter_config_dict, allow_unicode=True))
        
        # add assignment config
        cells.append(nbformat.v4.new_raw_cell(otter_raw_config))
        
        # add questions template
        cells.extend(self.__question_cells(n))
        
        notebook = nbformat.v4.new_notebook(cells=cells)
        #notebook.metadata['kernelspec'] = {'language': 'python', 'name': 'python3'}
        # to avoid nbformat warning when otter removes ids, this is a little hacky
        notebook.nbformat = 4
        notebook.nbformat_minor = 5
        
        notebook = self.__normalize(notebook)
        if save:
            self.__save(notebook, override, exist_ok)
        return notebook
    
    def grade(self, timeout=None):
        result_dir = self.submission_dir / Path('results')
        result_dir.mkdir(parents=True, exist_ok=True)
        grader = LocalGrader(self.autograder_dir, self.submission_dir, result_dir) # TODO: result_dir is currently unused
        grader.grade(moodle_assignment=True, timeount_in_seconds=timeout)
    
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
                    LOGGER.info(f'Written to {notebook_path}')
                except Exception as e:
                    LOGGER.error(f'Could not write to {notebook_path}.')
                    raise e
    
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
            LOGGER.info(f'moved {self.tmp_dir / Path("student")} -> {self.student_dir}')
            
            # extract the zip file to grade
            self.remove_autograding_notebook()
            self.autograder_dir.mkdir(parents=True, exist_ok=True)
            zip_file = self.__find_zip(self.tmp_dir / Path('autograder'))
            if zip_file == None:
                LOGGER.error(f'There is no zip file in {self.tmp_dir / Path("autograder")}')
            
            zip_file.rename(self.autograder_dir / zip_file.name)
            LOGGER.info(
                f'moved {zip_file} -> {self.autograder_dir / zip_file.name}')
                        
            # extract the solution notebook
            self.solution_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(self.tmp_dir / Path('autograder'), self.solution_dir)
            LOGGER.info(
                f'moved {self.tmp_dir / Path("autograder")} -> {self.solution_dir}')
            
            shutil.rmtree(str(self.tmp_dir))
            LOGGER.info( f'removed {self.tmp_dir}')
            
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
            LOGGER.info(
                f'remove {self.autograder_dir}')
            #print(f'remove {self.autograder_dir}')
    
    ####### TODO Refectoring
    
    def find_key(self, label, split, default=None):
        for line in split:
            if line.startswith(label):
                return line.split(':')[1]
        return default
    
    def read_questions(self, notebook=None):
        """
        Computes a partition of the notebook cells such that each part consist of the cells of one question.
        This makes it easy to extract questions from a notebook and insert it into another notebook.

        Returns:
            list: list of list of cells, i.e, the partition.
        """
        if notebook == None:
            notebook = self.__read_notebook()
        
        cells = notebook.cells
        
        i_start = None
        i_end = None
        
        questions = []
        
        for i, cell in enumerate(cells):
            if cell.source.startswith('# BEGIN QUESTION'):
                i_start = i
                i_end = None
                #split = cell.source.split('\n')
                #meta_begin_question = split[0]
                #name = self.find_key('name', split)
                #points = self.find_key('points', split)
                #manual = self.find_key('manual', split, 'false')
                #print(f'{name} {points} {manual}')
                
            if cell.source.endswith('# END QUESTION'):
                i_end = i
                if i_start == None or i_start >= i_end:
                    raise Exception('Invalid notebook: missing "# END QUESTION" mark.')
                questions.append(cells[i_start:i_end+1])
        return questions
    #######
    
    
    def __read_notebook(self) -> nbformat.NotebookNode:
        path_to_notebook, _ = peek(self.main_dir.glob('*.ipynb'))
        if path_to_notebook != None:
            #print(path_to_notebook)
            with open(path_to_notebook, mode='r', encoding='utf-8') as file:
                try:
                    notebook = nbformat.read(file, as_version=nbformat.NO_CONVERT)
                    return notebook
                except Exception as e:
                    LOGGER.error(f'Could not read from {file}')
                    return None
        
    def __find_notebook(self, dir : Path) -> Path:
        return peek(dir.glob('*.ipynb'))[0]
    
    def __find_zip(self, dir: Path) -> Path:
        zips_it = dir.glob('*.zip')
        return peek(zips_it)[0]
    
    def __repr__(self) -> str:
        return f'{self.name}'