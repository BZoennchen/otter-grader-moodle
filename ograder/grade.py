# external modules
from pathlib import Path
import zipfile
import shutil
import subprocess

class Grader:
    """
    The Grader helps to further automate the grading of otter notebooks using the otter grader without access to Gradescope.
    The assumption is that all students assignments are within some zip file.
    Furthermore each assignment consists of a directory named: [surname][SPACE][forenames]_[something]
    and in it is a zip file which contains the complete student assignment.
    
    The structure looks like the following:
    zip-file
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
    
    def __init__(self, src: str, dest: str, dist: str):
        """
        :param src: path to a zip file containing all assignments.
        :type nrows: str
        
        :param dest: path of a directory where the evaluation / auto-grading will be executed.
        :type nrows: str
        
        :rtype: Grader
        :return: A new grader to grade from a moodle download.
        
        """
        self.src : Path = Path(src)
        self.dest : Path = Path(dest)
        self.dist : Path = Path(dist)
        self.zips = Path('zips')
        self.invalid = Path('invalid')
        
    def clear(self):
        """
        deletes the assignments directory.
        """
        if self.dest.exists():
            shutil.rmtree(str(self.dest))
        
    def __unzip(self):
        """
        unzips the zip file that contains all assignments directories.
        """
        self.dest.mkdir(parents=True, exist_ok=True)
        Path(self.dest / self.zips).mkdir(parents=True, exist_ok=True)
        Path(self.dest / self.invalid).mkdir(parents=True, exist_ok=True)
        print(f'create dir: {self.dest}')
        with zipfile.ZipFile(self.src, 'r') as zip_ref:
            zip_ref.extractall(self.dest)
    
    def __is_valid(self, assignment_dict: Path):
        """
        True if and only if the assignment directory (of a student) is valid.
        """
        if not assignment_dict.is_dir():
            return False
        if sum(1 for _ in assignment_dict.glob('*')) > 1:
            print('Too many files, expect exactly one zip file for each assignment.')
            return False
        for file in assignment_dict.iterdir():
            return file.suffix == '.zip'
        
    def __get_zip_assignment(self, assignment_dict: Path):
        """
        returns the path of the first zip file inside assignment_dict
        """
        return next(assignment_dict.glob('*.zip'))
    
    def __extract_name(self, student_dir):
        """
        constructs and returns a nice name by extracting information from the assignment directory name
        """
        student_name = student_dir.name
        student_name = student_name.split('_')[0]
        student_name = student_name.replace(' ', '_')
        return student_name        
    
    def unpack(self, rename=True):
        """
        Unpacks all the files in the zip file.
        Invalid assignment directories are moved to the invalid directory.
        They will not be auto-graded.
        """
        self.__unzip()
        
        valid_dirs = list(filter(lambda d: d.is_dir() and self.__is_valid(d) and d.name not in [str(self.zips), str(self.invalid)], self.dest.iterdir()))
        invalid_dirs = list(filter(lambda d: d.is_dir() and not self.__is_valid(d) and d.name not in [str(self.zips), str(self.invalid)], self.dest.iterdir()))
        
        for directory in valid_dirs: 
            student_name = self.__extract_name(directory)          
            zip_file = self.__get_zip_assignment(directory)
            
            if rename:
                new_path = Path(self.dest / self.zips / (student_name+zip_file.suffix))
                zip_file.rename(new_path)
            else:
                new_path = Path(self.dest / self.zips / (zip_file.name))
                zip_file.rename(new_path)
                
            print(f'valid assignment: {zip_file} -> {new_path}')    
            shutil.rmtree(str(directory))
            print(f'{directory} deleted')    
        
        for directory in invalid_dirs: 
            student_name = self.__extract_name(directory)
            if rename:
                new_path = Path(self.dest / self.invalid / (student_name))
                directory.rename(new_path)
            else:
                new_path = Path(self.dest / self.invalid / (directory.name))
                directory.rename(new_path)
            
            print(f'invalid assignment: {directory} -> {new_path}')
                    
    def __find_master(self):
        return next(self.dist.glob('**/*.zip'))
            
    #otter grade -p zips -a dist/autograder/CT-WS2022-Pyramiden-autograder_2022_10_30T20_44_42_546298.zip -vz --timeout 60
    def grade(self, timeout_in_sec=120):
        """
        grades the assignments contained in the zip file.
        Invalid assignment directories are moved to the invalid directory.
        They will not be auto-graded.
        """
        subprocess.check_call(['otter', 'grade', 
            '-p', str(Path(self.dest / self.zips)),
            '-a', str(self.__find_master()), 
            '-o', str(self.dest), 
            '-vz', 
            '--timeout', str(timeout_in_sec)])
    
def main(src: str, dest : str = 'assignments', dist : str ='dist'):
    Grader(src, dest, dist).grade()