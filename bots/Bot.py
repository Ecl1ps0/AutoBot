from abc import abstractmethod, ABC

from selenium.webdriver.support.wait import WebDriverWait
from seleniumwire import webdriver

from api.APIClient import APIClient
from configs.logger import get_logger


class Bot(ABC):
    def __init__(self, client: APIClient, token: dict | None = None, proxy: str | None = None):
        self.token = token
        self.proxy = proxy

        self.driver_options = {
            'proxy': {
                'http': f'http://{proxy}',
            }
        }

        self.driver = webdriver.Chrome(seleniumwire_options=self.driver_options)
        self.wait = WebDriverWait(self.driver, timeout=300)
        self.client = client

        self.is_banned = False

        self.logger = get_logger(__name__)

    @abstractmethod
    def _login(self) -> bool:
        raise NotImplemented

    @abstractmethod
    def _register(self, email: str | None = None) -> bool:
        raise NotImplemented

    def _close_driver(self) -> None:
        if self.driver.session_id is not None:
            try:
                self.driver.close()
            except Exception as e:
                self.logger.exception(f"Failed to close webdriver with this exception: {str(e)}")
                print(f"Error closing WebDriver: {str(e)}")
