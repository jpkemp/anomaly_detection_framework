# pylint: disable=W0201 ## flags self.logger assigned outside init
'''Logging functions for MBS and PBS tests'''
# import atexit
import logging
import os
import subprocess
import sys
from datetime import datetime
from distutils.dir_util import copy_tree
from pathlib import Path

class LoggingStructure:
    '''Create the logging structure on enter'''
    def __init__(self, test_name, copy_path=None):
        self.copy_path = copy_path
        self.test_name = test_name
        self.output_path = self.create_output_folder(test_name)
        sys.excepthook = self.handle_exception
        self.file_name = self.output_path / f"{test_name}.log"
        self.logger = logging.getLogger()
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(message)s',
                            filename=self.file_name)
        # atexit.register(self.finalise)
        self.log(f"Starting {test_name}")
        self.log(subprocess.check_output(["git", "describe", "--always"]).strip())

    def finalise(self):
        '''Copy directory and finish log at test end'''
        self.log("Finalising")
        if self.copy_path is not None:
            if not isinstance(self.copy_path, str):
                raise TypeError("Copy path must be a string directory")

            path = Path(self.copy_path)
            if not path.exists():
                print(f"Cannot find {self.copy_path}")

                return

            name = self.output_path.name
            copy_folder = path / name
            os.mkdir(copy_folder)

            copy_tree(self.output_path.absolute().as_posix(), copy_folder.absolute().as_posix())

        handlers = self.logger.root.handlers.copy()
        for handler in handlers:
            self.logger.root.removeHandler(handler)
            handler.flush()
            handler.close()

    @classmethod
    def create_output_folder(cls, test_name):
        '''create an output folder for the log and any test results'''
        current = datetime.now().strftime("%Y%m%dT%H%M%S")
        output_folder = Path(os.getcwd()) / "Output" / f"{test_name}_{current}"
        os.makedirs(output_folder)

        return output_folder

    def get_file_path(self, filename):
        '''combines a filename with the logger output path'''
        if self.output_path is None:
            return filename

        return self.output_path / filename

    def handle_exception(self, exc_type, exc_value, exc_traceback, from_exit=False):
        '''log exceptions to file'''
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        if from_exit:
            self.logger.info("Uncaught exception", exc_info=1)
        else:
            self.logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
            raise exc_type(exc_value)

    def log(self, line, line_end='...'):
        '''add to log file'''
        print(f"{datetime.now()} {line}{line_end}")
        self.logger.info(line)

class Logger:
    '''Logging functions and output path'''
    def __init__(self, test_name, copy_path=None):
        # self.name = name
        self.test_name = test_name
        self.copy_path = copy_path
        self.logger: LoggingStructure

    def __enter__(self):
        self.logger = LoggingStructure(self.test_name, self.copy_path)

        return self.logger

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self.logger.handle_exception(exc_type, exc_type, traceback, True)

        self.logger.finalise()
