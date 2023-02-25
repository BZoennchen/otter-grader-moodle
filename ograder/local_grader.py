
from pathlib import Path
from otter.api import grade_submission
from .utils import peek, is_empty
from otter.utils import loggers
from otter.utils import chdir
import warnings

import time
import zipfile
import tempfile
import shutil

import multiprocessing
import time

LOGGER = loggers.get_logger(__name__)

class Student():
    def __init__(self, name, forname, file=None):
        self.name = name
        self.forname = forname
        self.file = file
    
    def __repr__(self) -> str:
        return f'{self.forname}\n{self.name}'

# ograder grade training03
class Question():
    def __init__(self, name, score, possible):
        self.name = name
        self.score = score
        self.possible = possible

    def __repr__(self) -> str:
        return f'{self.name}:{self.score} / {self.possible}'

class LocalGrader:

    def __init__(self, autograde: Path, src: Path, dest: Path):
        """_summary_

        Args:
            autograde (Path): path to the autograder zip file
            src (Path): path to the directory containing all submissions (either a single zip or directories/notebooks)
            dest (Path): path to the directory where the results will be wirtten
        """
        self.autograde: Path = autograde
        self.src: Path = src
        self.dest: Path = dest

    
    def grade(self, moodle_assignment=True, timeount_in_seconds:float=None):
        autograder_zip, _ = peek(self.autograde.rglob('*.zip'))
        if autograder_zip == None:
            LOGGER.error(f'autograde zip file is missing, you may have to execute ograder assign [assignment name]')
            return
        if len(list((self.src.rglob('*.zip')))) == 1:
            with chdir(self.src):
                grading_dir = Path(f'grading_{time.strftime("%Y%m%d_%H%M%S")}')
                grading_dir.mkdir()
                
                error_dir = Path(grading_dir / Path('errors'))
                error_dir.mkdir()
                
                zip_file, _ = peek(self.src.rglob('*.zip'))
                if moodle_assignment:
                    students = self.__pase_moodle_zip(zip_file, grading_dir)
                    for student in students:
                        #print(f'grade {self.src /grading_dir / Path(student.file)} using {str(autograder_zip)}')
                        LOGGER.info(f'grading {student}')
                        #grade_submission(self.src / grading_dir / Path(student.file), str(autograder_zip)
                        student_zip_path = grading_dir / Path(student.file)
                        p = multiprocessing.Process(target=grade_submission, args=(
                            student_zip_path, str(autograder_zip), False, False))
                        p.start()
                        p.join(timeout=timeount_in_seconds)
                        
                        if p.is_alive():
                            LOGGER.info(f'grading {student.file}')
                            warnings.warn(f'timeout for {student.file}')
                            p.terminate()
                            p.join()
                        
                        # TODO: something went wrong!
                        if p.exitcode != 0:
                            student_zip_path.rename(
                                error_dir / Path(student.file))
                else:
                    print('pass')
        
        # (1) find all assignments
        #print(f"grading {autograder_zip}, {self.src}, {self.dest}")
        #for noteboo_file in self.src.rglob('*.ipynb'):
            #print(noteboo_file)
            #result = grade_submission(str(noteboo_file), str(autograder_zip))
        
    def __pase_moodle_zip(self, moodle_zip: Path, grading_dir: Path) -> tuple[Path, list[Student]]:
        """
        A moodle assignment zip file looks like the following:
            root_zip:
                __cryptic_directory_name_with_student_a_name
                    student_a_assignment_file1
                    student_a_assignment_file2
                    ...
                __cryptic_directory_name_with_student_b_name
                    ...
        But otter requires the following structure:
            root_zip:
                student_a_zip
                student_b_zip
        where the file name is used to identify the student!
        This method extracts the student name from the cryptic directory name and rearranges the zip files or zips the files accordingly.
        
        Args:
            moodle_zip (Path): path to the moodle zip file

        Returns:
            Path: converts a moodle assignment zip file into a valid otter assignment zip that contains all the files.
        """
        students = []
        #with chdir(moodle_zip.parent):
        tmp = tempfile.mkdtemp() # temp directory
        with zipfile.ZipFile(moodle_zip) as zf:
            zf.extractall(tmp)
            #with zipfile.ZipFile(submission_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for student_dir in Path(tmp).iterdir():
                if student_dir.is_dir() and not str(student_dir).endswith('__MACOSX'):
                    #print(f'student dir: {student_dir}')
                    student = self.__extract_student(student_dir)
                    
                    new_zip_path = Path(student.name+'_'+'_'.join(student.forname.split(' '))+'.zip')
                    
                    student.file = new_zip_path
                    students.append(student)
                    
                    zip_path, _ = peek(student_dir.rglob('*.zip'))

                    # either the student assignment consist of a single zip file, this should be the default case!
                    if zip_path != None:
                        #print(f'renaming {zip_path} to {new_zip_path}')
                        zip_path.rename(new_zip_path)
                    # or the student assignment consist of many files, i.e. there is no zip
                    else:
                        with zipfile.ZipFile(new_zip_path, 'w', zipfile.ZIP_DEFLATED) as new_student_zip:
                            for file in student_dir.iterdir():
                                #print(f'adding {file.relative_to(file.parent)} to {new_zip_path}')
                                new_student_zip.write(file, file.relative_to(file.parent))
                    
                    tmp_path = Path('tmp.zip')
                    with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as tmp_zip:
                        pers_info_path = Path('PersDaten.txt')
                        with open(pers_info_path, 'w') as f:
                            f.write(f'{student}')
                        tmp_zip.write(pers_info_path)
                        tmp_zip.write(new_zip_path)
                        pers_info_path.unlink()
                        new_zip_path.unlink()
                        tmp_path.rename(new_zip_path)
                    #return
                    new_zip_path.rename(grading_dir / new_zip_path)
                    #zipf.write(new_zip_path)
                    #new_zip_path.unlink()
                        
            #moodle_zip.unlink()
            #submission_zip_path.rename(moodle_zip)
            return students
                
    def __extract_student(self, student_dir) -> Student:
        """
        constructs and returns a nice name by extracting information from the assignment directory name
        """
        student_name = student_dir.name
        student_name = student_name.split('_')[0]
        #student_name = student_name.replace(' ', '_')
        student_name = student_name.split(' ')
        return Student(student_name[0], ' '.join(student_name[1:]))
    
    
    def __grade(self, notebook_file: Path):
        result = grade_submission(str(notebook_file), str(self.autograde))
        result_dict = result.to_dict()
        for test_name in result.results:
            student.questions[test_name] = Question(
                test_name, 
                float(result_dict[test_name]['score']), 
                float(result_dict[test_name]['possible']))
