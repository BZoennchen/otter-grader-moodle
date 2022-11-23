__author__ = 'Benedikt Zoennchen'

from ograder.config import Config
from ograder.assign import Assignment
from ograder.grade import Grader
from ograder.project import Project
from ograder.config import load as load

from ograder.cli import load_config as load_config

from .version import __version__