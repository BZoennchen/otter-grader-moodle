from pathlib import Path

import fica
import yaml

from otter.utils import loggers

LOGGER = loggers.get_logger(__name__)

class Config(fica.Config):
    """
    The Config class is a representation of all required configurations, such as:
    
    + system paths, 
    + git configurations, 
    + otter configurations.
    """
    root_dir = fica.Key()
    semester = fica.Key()
                
    def __init__(self, user_config, documentation_mode=False):
        if not documentation_mode:
            user_config['root_dir'] = Path(user_config['root_dir'])
            semester_dir = user_config['root_dir'] / Path(user_config['semester'])
            user_config['assign']['main_dir'] = semester_dir/ Path(user_config['assign']['main_dir'])
            user_config['assign']['students_dir'] = semester_dir / Path(user_config['assign']['students_dir'])
            user_config['assign']['solutions_dir'] = semester_dir / Path(user_config['assign']['solutions_dir'])
            user_config['assign']['autograder_dir'] = semester_dir  / Path(user_config['assign']['autograder_dir'])
            user_config['assign']['submission_dir'] = semester_dir / Path(user_config['assign']['submission_dir'])
            user_config['assign']['tmp_dir'] = semester_dir / Path(user_config['assign']['tmp_dir'])
        super().__init__(user_config, documentation_mode=documentation_mode)
        
    class AssignmentConfig(fica.Config):
        """
        Parameters that are used for the generation of an assignment given a main/master otter notebook.
        """
        main_dir = fica.Key()
        students_dir = fica.Key()
        solutions_dir = fica.Key()
        autograder_dir = fica.Key()
        submission_dir = fica.Key()
        tmp_dir = fica.Key()
        
    class ExecisesConfig(fica.Config):        
        exercises = fica.Key(type_=list, default=[])
        
    class OtterNotebookConfig(fica.Config):
        """
        Parameters that are used for the initiation or update of a new main/master otter notebook.
        It represents the yaml meta configuration of a main notebook at inserted in the very first cell of that notebook.
        """
        init_cell = fica.Key()
        solutions_pdf = fica.Key()
        check_all_cell = fica.Key()

        class OtterNotebookGenerateConfig(fica.Config):
            zips = fica.Key()
    
        class OtterNotebookExportCellConfig(fica.Config):
            instructions = fica.Key()
            force_save = fica.Key()
            pdf = fica.Key()
            
        class OtterNotebookTestsConfig(fica.Config):
            ok_format = fica.Key()
         
        generate = fica.Key(subkey_container=OtterNotebookGenerateConfig)
        export_cell = fica.Key(subkey_container=OtterNotebookExportCellConfig)     
        tests = fica.Key(subkey_container=OtterNotebookTestsConfig)  
        
    class GitConfig(fica.Config):

        class GitStudentConfig(fica.Config):
            jupyterhub_url = fica.Key()
            git_hub_repo = fica.Key()
            git_lab_repo = fica.Key()
            git_hub_branch = fica.Key()
            git_lab_branch = fica.Key()
            path = fica.Key()
            app = fica.Key()
            git_lab_branch = fica.Key()
            
        class GitMainConfig(fica.Config):
            git_lab_repo = fica.Key()
            path = fica.Key()
        
        students = fica.Key(subkey_container=GitStudentConfig)
        main = fica.Key(subkey_container=GitMainConfig)
    
    assign = fica.Key(subkey_container=AssignmentConfig)
    git = fica.Key(subkey_container=GitConfig)
    otter_notebook_config = fica.Key(subkey_container=OtterNotebookConfig)
    exercises = fica.Key(subkey_container=ExecisesConfig)
    assignments = fica.Key(subkey_container=ExecisesConfig)
              
def load(config_file: str) -> Config: 
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        return Config(config)
    except Exception as e:
        LOGGER.error("could read/load the ograder config file: {config_file}")
        raise e