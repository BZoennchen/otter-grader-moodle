
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

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import threading
from multiprocessing import Process, Queue
import concurrent.futures
import time

from dataclasses import dataclass, field

LOGGER = loggers.get_logger(__name__)

OVERALL_POINTS_LABEL = 'overall'

@dataclass
class Question():
    """Class representing an answer of a question given by a student."""
    name: str
    score: float
    possible: float
   
@dataclass
class Student():
    name: str
    forname: str
    questions:dict[str:Question] = field(default_factory=dict)
    file: Path = field(default_factory=Path)
    
    def score_sum(self) -> float:
        s = 0
        for question_name in self.questions:
            s += self.questions[question_name].score
        return s

    @staticmethod
    def to_dict(students:list, manual_questions:list[str]) -> dict:
        d = {}
        for i in range(len(students)):
            student = students[i]
            if i == 0:
                d = {question_name: [] for question_name in student.questions}

                for manual_question in manual_questions:
                    d[manual_question] = []

                d[OVERALL_POINTS_LABEL] = []
                for v in vars(student):
                    if v != 'questions':
                        d[v] = []
            for question_name in student.questions:
                d[question_name].append(student.questions[question_name].score)

            for manual_question in manual_questions:
                d[manual_question].append(np.nan)

            for v in vars(student):
                if v != 'questions':
                    d[v].append(vars(student)[v])

            d[OVERALL_POINTS_LABEL].append(student.score_sum())
        return d

class LocalGrader:

    def __init__(self, autograde: Path, src: Path):
        """
        Grades (Moodle) assignments by running the code locally on this machine in its current environment, i.e., without Docker.

        Args:
            autograde (Path): path to the autograder zip file
            src (Path): path to the directory containing all submissions (either a single zip or directories/notebooks)
            dest (Path): path to the directory where the results will be wirtten
        """
        self.autograde: Path = autograde
        self.src: Path = src
    
    @staticmethod
    def wrapper_grade_submission(queue:Queue, func, submission_path:Path, ag_path:str, quiet:bool, debug:bool):
        try:
            ret = func(submission_path, ag_path, quiet, debug)
            result_dict = ret.to_dict()
            questions = {}
            for test_name in ret.results:
                questions[test_name] = Question(test_name, float(result_dict[test_name]['score']), float(result_dict[test_name]['possible']))
            queue.put(questions)
        except Exception as e:
            queue.put(e)
    
    @staticmethod
    def __extract_student(student_dir:Path) -> Student:
        """
        constructs and returns a nice name by extracting information from the assignment directory name
        """
        student_name = student_dir.name
        student_name = student_name.split('_')[0]
        #student_name = student_name.replace(' ', '_')
        student_name = student_name.split(' ')#
        return Student(student_name[0], ' '.join(student_name[1:]))
    
    @staticmethod
    def handle_error(error_dir:Path, student:Student, student_zip_path:Path):
        new_path = error_dir / Path(student.file)
        LOGGER.error(f'Unable to grade {student.file}, therefore moving the file to {new_path}')
        student_zip_path.rename(new_path)
    
    def grade(self, manual_questions:list[str]=[], moodle_assignment=True, timeount_in_seconds:float=None, plot=False):
        autograder_zip, _ = peek(self.autograde.rglob('*.zip'))
        if autograder_zip == None:
            LOGGER.error(f'autograde zip file is missing, you may have to execute ograder assign [assignment name]')
            return
        
        # check if there is exactly one submssion zip-file (containing all student assignments)
        if len(list((self.src.glob('*.zip')))) == 1:
            print(self.src)
            with chdir(self.src):
                time_str = time.strftime("%Y%m%d_%H%M%S")
                grading_dir = Path(f'grading_{time_str}')
                grading_dir.mkdir()
                
                error_dir = Path(grading_dir / Path('errors'))
                error_dir.mkdir()
                
                zip_file, _ = peek(self.src.glob('*.zip'))
                if moodle_assignment:
                    valid_students = [] # grading was succesful
                    error_students = [] # grading timed out
                    
                    # extract students information from the path generated by Moodle
                    print(zip_file)
                    students = self.__pase_moodle_zip(zip_file, grading_dir)
                    
                    for student in students:
                        LOGGER.info(f'grading {student}')
                        student_zip_path = grading_dir / Path(student.file)
                        
                        queue = Queue()
                        process = Process(target=LocalGrader.wrapper_grade_submission, args=(queue, grade_submission, student_zip_path, str(autograder_zip), False, False))
                        process.start()
                        process.join(timeout=timeount_in_seconds)
                        
                        if process.is_alive():
                            LOGGER.info(f'grading {student} timed out')
                            process.terminate()
                            process.join()
                            LocalGrader.handle_error(error_dir, student, student_zip_path)
                            error_students.append(student)
                        else:
                            questions = queue.get()
                            if isinstance(questions, Exception):
                                LOGGER.error(f'grading {student} was unsucessful due to {questions}')
                                LocalGrader.handle_error(error_dir, student, student_zip_path)
                                error_students.append(student)
                            else:
                                student.questions = questions
                                valid_students.append(student)
                                
                    data = pd.DataFrame(Student.to_dict(valid_students, manual_questions)).sort_values('name')
                    data.to_csv(grading_dir / Path(f'grading_result_{time_str}.csv'), sep=';')
                    LOGGER.info(data)
                    
                    if plot:
                        print(data)
                        data['overall'].plot.hist(bins=20, alpha=0.5)
                        plt.show()
                    
                else:
                    LOGGER.error(f'Only moodle assignments are supported right now. If it is a moodle assignment it is possible to extract the students name.')
        
    def __pase_moodle_zip(self, moodle_zip: Path, grading_dir: Path) -> list[Student]:
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
            for student_dir in Path(tmp).iterdir():
                if student_dir.is_dir() and not str(student_dir).endswith('__MACOSX'):
                    #print(f'student dir: {student_dir}')
                    student = LocalGrader.__extract_student(student_dir)
                    
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
                    new_zip_path.rename(grading_dir / new_zip_path)
            return students