# external modules
from pathlib import Path
from .config import Config
from .assign import Assignment

import shutil
import subprocess
from .utils import peek, is_empty
import warnings

from otter.utils import loggers

LOGGER = loggers.get_logger(__name__)

class Grader:
    """
    The Grader helps to further automate the grading of otter notebooks using the otter grader without access to Gradescope.
    The assumption is that all students assignments are within some directory src.
    Furthermore each assignment consists of a directory named: [surname][SPACE][forenames]_[something]
    and in it is a zip file which contains the complete student assignment.
    
    The structure looks like the following:
    src
     |
     |----student1
              |
              |------ student_assignment.zip
     |----student2
              |
              |------ student_assignment.zip
     |----...
              
    Grader constructs a new directory containing all the renamed zip-files:
    assignments
     |
     |----student1.zip
     |----student2.zip
     |----...
    such that all assignments can be graded by otter grader and the results can be matched
    """
    
    def __init__(self, config: Config, src: str, dest: str):
        """
        :param config: ograder config
        :type config: Config
        
        :param src: path to a zip file containing all assignments.
        :type src: str
        
        :param dest: path of a directory where the evaluation / auto-grading will be executed.
        :type dest: str
        
        :rtype: Grader
        :return: A new grader to grade from a moodle download.
        
        """
        self.config = config
        self.src : Path = Path(src)
        self.dest : Path = Path(dest)
        self.zips = Path('zips')
        self.invalid = Path('invalid')
        
    def clear(self) -> None:
        """
        deletes the assignments directory.
        """
        if self.dest.exists():
            shutil.rmtree(str(self.dest))
         
    def __unzip(self) -> None:
        """
        unzips the zip file that contains all assignments directories.
        """
        with zipfile.ZipFile(self.src, 'r') as zip_ref:
            zip_ref.extractall(self.dest)
    
    def __is_valid(self, assignment_dict: Path) -> bool:
        """
        True if and only if the assignment directory (of a student) is valid.
        """
        if not assignment_dict.is_dir():
            LOGGER.info(f'invalid assignment, {assignment_dict} is not a directory')
            return False
        if sum(1 for _ in assignment_dict.glob('*')) > 1:
            LOGGER.info(f'Too many files in {assignment_dict} expect exactly one zip file for each assignment.')
            return False
        for file in assignment_dict.iterdir():
            if file.suffix == '.zip':
                LOGGER.info(f'valid assignment, {assignment_dict}.')
                return True
            else:
                LOGGER.info(f'invalid assignment, wrong suffix ({file}) for {assignment_dict}.')
        
    def __get_zip_assignment(self, assignment_dict: Path) -> Path:
        """
        returns the path of the first zip file inside assignment_dict
        """
        element, rest = peek(assignment_dict.glob('*.zip'))
        return element
    
    def __extract_name(self, student_dir) -> str:
        """
        constructs and returns a nice name by extracting information from the assignment directory name
        """
        student_name = student_dir.name
        student_name = student_name.split('_')[0]
        student_name = student_name.replace(' ', '_')
        return student_name        
    
    def unpack(self, rename=True) -> None:
        """
        Unpacks all the files in the zip file.
        Invalid assignment directories are moved to the invalid directory.
        They will not be auto-graded.
        """
        
        self.dest.mkdir(parents=True, exist_ok=True)
        Path(self.dest / self.zips).mkdir(parents=True, exist_ok=True)
        Path(self.dest / self.invalid).mkdir(parents=True, exist_ok=True)
        LOGGER.info(f'create dir: {self.dest}')
        
        #self.__unzip()
        
        valid_dirs = list(filter(lambda d: d.is_dir() and self.__is_valid(d) and d.name not in [str(self.zips), str(self.invalid)], self.src.iterdir()))
        invalid_dirs = list(filter(lambda d: d.is_dir() and not self.__is_valid(d) and d.name not in [str(self.zips), str(self.invalid)], self.src.iterdir()))
        for directory in valid_dirs:
            student_name = self.__extract_name(directory)          
            zip_file = self.__get_zip_assignment(directory)
            
            if rename:
                new_path = Path(self.dest / self.zips / (student_name+zip_file.suffix))
                shutil.copy(zip_file, new_path)
                #zip_file.rename(new_path)
            else:
                new_path = Path(self.dest / self.zips / (zip_file.name))
                shutil.copy(zip_file, new_path)
                #zip_file.rename(new_path)
            
            LOGGER.info(f'unpack valid assignment: {zip_file} -> {new_path}')
            #shutil.rmtree(str(directory))
            #LOGGER.info(f'{directory} deleted')    
        
        for directory in invalid_dirs: 
            student_name = self.__extract_name(directory)
            if rename:
                new_path = Path(self.dest / self.invalid / (student_name))
                #directory.rename(new_path)
                shutil.copytree(directory, new_path, dirs_exist_ok=True)
            else:
                new_path = Path(self.dest / self.invalid / (directory.name))
                #directory.rename(new_path)
                shutil.copytree(directory, new_path, dirs_exist_ok=True)
            
            LOGGER.info(f'unpack invalid assignment: {directory} -> {new_path}')  
    
    #otter grade -p zips -a dist/autograder/CT-WS2022-Pyramiden-autograder_2022_10_30T20_44_42_546298.zip -vz --timeout 60
    def grade(self, assignment: Assignment, timeout_in_sec=120, clear=False) -> None:
        """
        grades the assignments contained in the zip file.
        Invalid assignment directories are moved to the invalid directory.
        They will not be auto-graded.
        """
        
        if clear:
            self.clear()
            self.unpack()
        
        # TODO are we sure?
        #if not self.dest.exists():
        #    self.unpack()
        
        if not is_empty(assignment.autograder_dir.glob('**/*.zip')):
            LOGGER.info(f'found autograder .zip for assignment {assignment}')
            file = next(assignment.autograder_dir.glob('**/*.zip'))
            LOGGER.info(f'otter grade -p {Path(self.dest / self.zips)} -a {file} -o {self.dest} -vz --timeout {timeout_in_sec}')
            subprocess.check_call(['otter', 'grade',
                '-p', str(Path(self.dest / self.zips)),
                '-a', str(next(assignment.autograder_dir.glob('**/*.zip'))), 
                '-o', str(self.dest), 
                '-vz', 
                '--timeout', str(timeout_in_sec)])
        elif not is_empty(assignment.autograder_dir.glob('**/*.ipynb')):
            LOGGER.info(f'found autograder .ipynb for assignment {assignment}')
            file = next(assignment.autograder_dir.glob('**/*.ipynb'))
            LOGGER.info(f'otter grade -p {Path(self.dest / self.zips)} -a {file} -o {self.dest} -v --timeout {timeout_in_sec}')
            subprocess.check_call(['otter', 'grade', 
                '-p', str(Path(self.dest / self.zips)),
                '-a', str(next(assignment.autograder_dir.glob('**/*.zip'))), 
                '-o', str(self.dest), 
                '-v', 
                '--timeout', str(timeout_in_sec)])
        else:
            warnings.warn(f'missing autograder file for {assignment}')
        
    
#def main(src: str, dest : str = 'assignments', dist : str ='dist'):
#    Grader(src, dest, dist).grade()