# main.py
import os

from constants import CONFIG_FOLDER, CONFIG_FILE_NAME, LOGGER_NAME, LOGGING_CONFIG_FILE
from src.helpers.helpers_logging import init_logger_from_file
from src.helpers.helpers_serialize import get_serialized_data
from src.model import Model
from src.repository import Repository
from src.view import View

# Initialisation du logger depuis le fichier de configuration YAML
logging_config_full_path = os.path.join(
    os.path.dirname(__file__), CONFIG_FOLDER, LOGGING_CONFIG_FILE
)
logger = init_logger_from_file(
    logger_name=LOGGER_NAME, config_full_path=logging_config_full_path
)


class App:
    def __init__(self):
        config_file_path = os.path.join(
            os.path.normpath(os.getcwd()), CONFIG_FOLDER, CONFIG_FILE_NAME
        )
        self.config = get_serialized_data(config_file_path)
        self.repo = Repository(self.config)
        self.model = Model(self.repo)
        self.view = View(self.repo, self.model)

    def run(self):
        logger.info("Starting application")
        self.repo.get_data()
        self.model.process_data()
        self.view.display()
        logger.info("Application finished")


if __name__ == "__main__":
    app = App()
    app.run()
