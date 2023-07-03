import click
from .version import print_version_info
from .grade import Grader
from .local_grader import LocalGrader
from .project import Project
from .assign import Assignment
import ograder.config as conf
import os
from otter.cli import _verbosity

CONFIG_PATH = os.path.expanduser("~") + '/ograder.yml'

def load_config() -> conf.Config:
    """
    Loads and returns the ograder configuration which defines
    the structure of your ograder projects.

    Returns:
        conf.Config: the ograder user specific configuration
    """
    return conf.load(CONFIG_PATH)

@click.group(invoke_without_command=True)
@_verbosity
@click.option("--version", is_flag=True, help="Show the version and exit")
@click.option("--config", is_flag=True, help="Show the path to the config file")
def cli(version, config):
    """
    Command-line utility for ograder, a Python-based autograder that uses Otter-Grader
    to create, manage and grade Jupyter-Notebook assignments.
    """
    if version:
        print_version_info(logo=True)
        return
    elif config:
        print(CONFIG_PATH)

@click.command()
@_verbosity
@click.option('-t', '--tests', default= True, is_flag=True, show_default=True, type=bool, help='prevents the evaluation of tests.')
@click.argument('names', nargs=-1)
def assign(tests: bool, names: list[str]):
    """
    Generates for each assignment, identified by names, all three required parts:
    (1) student: a notebook that contains the exercise without the solution
    (2) solution: a notebook that contains the solution
    (3) autograder: a zip file to grade the students solution
    """
    return __assign(tests, names)

def __assign(tests: bool, names: list[str]):
    """
    Generates for each assignment, identified by names, all three required parts: 
    (1) student: a notebook that contains the exercise without the solution
    (2) solution: a notebook that contains the solution
    (3) autograder: a zip file to grade the students solution
    """
    config = load_config()
    assignments = []
    if len(names) > 0:
        for name in names:
            assignment = Assignment(config, name)
            if assignment.main_notebook_exists():
                assignment.generate(run_tests=tests)
                assignments.append(assignment)
            else:
                click.echo(f'main notebook for {assignment} does not exists.', err=True)
    else:
        project = Project(config)
        project.generate_all(run_tests=tests)
        assignments =  project.all_assignments()
    return assignments
    
@click.command()
@_verbosity
@click.argument('names', nargs=-1)
def extract_questions(names: list[str]):
    __extract_questions(names)

def __extract_questions(names: list[str]):
    config = load_config()
    if len(names) > 0:
        for name in names:
            assignment = Assignment(config, name)
            if assignment.main_notebook_exists():
                assignment.read_questions()
            else:
                click.echo(f'main notebook for {assignment} does not exists.', err=True)
    else:
        project = Project(config)
        project.read_questions()

@click.command()
@_verbosity
@click.option('-t', '--timeout', default=None, show_default=True, type=float, help='time after the grading of a notebook will be terminated')
@click.argument('names', nargs=-1)
def grade(timeout: float, names: list[str]):
    return __grade(timeout, names)


def __grade(timeout: float, names: list[str]):
    config = load_config()
    assignments = []
    print(f'grading {names}')
    if len(names) > 0:
        for name in names:
            assignment = Assignment(config, name)
            if assignment.main_notebook_exists():
                assignment.grade(timeout=timeout)
            else:
                click.echo(
                    f'main notebook for {assignment} does not exists.', err=True)
    else:
        project = Project(config)
        project.grade_all(timeout=timeout)
        assignments = project.all_assignments()
    return assignments


#@click.command()
#@_verbosity
#@click.option('-c', '--clear', default= False, is_flag=True, show_default=True, type=bool, help='Remove all unpacked files and restart from new.')
#@click.argument('name')
#@click.argument('src', type=str)
#@click.argument('dst', type=str)
#def grade(clear: bool, name: str, src: str, dst: str):
#    """
#    Grades an existing assignment where SRC is the path to a directory containing all submissions.
#    Each submission has to consists of one zip file containing the student notebook.
#    
#    Args:
#        clear (bool): clear everything and re-run it. If you have manipluated the submission your changes will be lost.
#        name (str): name of the assignment
#        src (str): the path to the directory containing all submissions (a directory for each student with a otter-zip-file)
#        dst (str): the path to a directory at which everything will be extracted and graded.
#    """
#    
#    config = load_config()
#    LocalGrader(config., config.)
#    
    #assignments = __assign(tests=True, names=[name])
    #grader = Grader(load_config(), src, dst)
    #grader.grade(assignments[0], clear=clear)

@click.command()
@_verbosity
@click.argument('n', type=int)
@click.argument('names', nargs=-1)
def add_questions(n, names: list[str]):
    """
    Initializes the complete ograder project, i.e., directory structure using the ograder.yml file in your home directory.
    """

    config = load_config()
    if len(names) > 0:
        for name in names:
            assignment = Assignment(config, name)
            if assignment.main_notebook_exists():
                assignment.add_questions(n)
            else:
                click.echo(f'main notebook for {assignment} does not exists.', err=True)
    else:
        project = Project(config)
        project.add_questions(n)

@click.command()
@_verbosity
@click.argument('n', type=int)
def init(n=0):
    """
    Initializes the complete ograder project, i.e., directory structure using the ograder.yml file in your home directory.
    """

    config = load_config()
    project = Project(config)
    if not project.exists():
        project.init(n, exist_ok=False)
    else:
        click.echo("The directory/file structure already exists. Therefore, initialization is impossible.")
    
@click.command()
@_verbosity
#@click.option('-o', '--override', default= False, is_flag=True, help='Override existing notebooks.')
@click.argument('n', type=int)
def upgrade(n=0):
    """
    Upgrades all notebooks accoding to your ograder.yml file in your home directory.
    """

    config = load_config()
    project = Project(config)
    project.upgrade_notebooks(n)         

cli.add_command(init)
cli.add_command(upgrade)
cli.add_command(assign)
cli.add_command(grade)
cli.add_command(add_questions)
#cli.add_command(extract_questions)

if __name__ == '__main__':
    cli()