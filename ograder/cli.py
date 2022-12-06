import click
from .version import print_version_info
from .grade import Grader
from .project import Project
from .assign import Assignment
import ograder.config as conf
import os
from otter.cli import _verbosity

def load_config() -> conf.Config:
    return conf.load(os.path.expanduser("~") + '/ograder.yml')

@click.group(invoke_without_command=True)
@_verbosity
@click.option("--version", is_flag=True, help="Show the version and exit")
def cli(version):
    """
    Command-line utility for ograder, a Python-based autograder that uses Otter-Grader
    to create, manage and grade Jupyter-Notebook assignments.
    """
    if version:
        print_version_info(logo=True)
        return

@click.command()
@_verbosity
@click.option('-t', '--tests', default= True, is_flag=True, show_default=True, type=bool, help='Name of the assigment/exercise.')
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
@click.option('-c', '--clear', default= False, is_flag=True, show_default=True, type=bool, help='Remove all unpacked files and restart from new.')
@click.argument('name')
@click.argument('src', type=str)
@click.argument('dst', type=str)
def grade(clear: bool, name: str, src: str, dst: str):
    """
    Grades an existing assignment wherer src is the path to a zip file containing all submissions.
    Each submission has to consists of one zip file containing the student notebook.
    
    Args:
        clear (bool): clear everything and re-run it. If you have manipluated the submission your changes will be lost.
        name (str): name of the assignment
        src (str): the path to the directory containing all submissions (a directory for each student with a otter-zip-file)
        dst (str): the path to a directory at which everything will be extracted and graded.
    """
    
    assignments = __assign(tests=True, names=[name])
    grader = Grader(load_config(), src, dst)
    grader.grade(assignments[0], clear=clear)

@click.command()
@_verbosity
def init():
    """
    Initializes the complete ograder project, i.e., directory structure using the ograder.yml file in your home directory.
    """

    config = load_config()
    project = Project(config)
    project.init(exist_ok=False)
    project.init_notebooks(exist_ok=False)
    
@click.command()
@_verbosity
@click.option('-o', '--override', default= False, is_flag=True, help='Override existing notebooks.')
def upgrade(override: bool):
    """
    Upgrades the complete ograder project, i.e., directory structure using the ograder.yml file in your home directory.
    Args:
        override (bool): if True overrides all existing notebooks with a blank new one.
    """

    config = load_config()
    project = Project(config)
    #project.init(exist_ok=True)
    project.upgrade_notebooks()         

cli.add_command(init)
cli.add_command(upgrade)
cli.add_command(assign)
cli.add_command(grade)

if __name__ == '__main__':
    cli()