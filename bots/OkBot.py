import time

import names

from api import APIClient
from .Bot import Bot

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException

from models import Source
from models import ok_token
from configs.logger import get_logger
from configs.random_date import get_random_date


class OkBot(Bot):
    def __init__(self, client: APIClient, token: dict = ok_token, proxy: str | None = None):
        super().__init__(client, token, proxy)

        self.login_link = 'https://ok.ru/'
        self.registration_link = 'https://ok.ru/dk?st.cmd=anonymRegistrationEnterPhone'
        self.source = Source.Ok

        self.logger = get_logger(__name__)

    def _login(self) -> bool:
        try:
            self.driver.get(self.login_link)
            self.logger.info(
                F"Start login to Ok account with id: {self.token['id']} and phone: {self.token['phone']}, on proxy: {self.proxy}")
            self.driver.maximize_window()
        except Exception as e:
            self.logger.exception(f"Failed to open the link with Exception: {str(e)}")

        self.wait.until(ec.element_to_be_clickable((By.ID, "field_email"))).send_keys(self.token['phone'])
        self.wait.until(ec.element_to_be_clickable((By.ID, "field_password"))).send_keys(self.token['password'])

        try:
            self.wait.until(ec.element_to_be_clickable((By.XPATH, "//*[@id=tabpanel-login-8932111615]/form/div[4]/input"))).click()

            if self.driver.current_url == "https://ok.ru/feed":
                self.logger.info("Successful logged in!")
                self._close_driver()
                return True
        except TimeoutException:
            self.logger.info("No first log in button!")
            return False

        try:
            WebDriverWait(self.driver, 30).until(ec.element_to_be_clickable((By.XPATH, "button-pro __wide"))).click()
        except TimeoutException:
            self.logger.info("No second log in button!")
            return False

        try:
            WebDriverWait(self.driver, 30).until(ec.element_to_be_clickable((By.XPATH, "button-pro __wide"))).click()
        except TimeoutException:
            self.logger.info("No third log in button!")
            return False

        time.sleep(15)

        if self.driver.current_url == "https://ok.ru/feed":
            self.logger.info("Successful logged in!")
            self._close_driver()
            return True

        self.logger.exception("Failed to register!")
        self._close_driver()
        return False

    def update_token(self) -> None:
        if not self.token["phone"]:
            self.logger.exception("Email field is empty!")
            raise Exception("The token is None! Please insert token to log in!")

        if self._login() is False:
            self.logger.exception("Fail to log in!")
            self.token["status"] = 0
            return

        self.token["status"] = 1
        self.token["proxy"] = self.proxy

        self.client.update_token(self.token)

    def _register(self, email: str | None = None) -> bool:
        try:
            self.driver.get(self.registration_link)
            self.logger.info(f"Start registration on static proxy: {self.proxy}")
            self.driver.maximize_window()
        except TimeoutException as e:
            self.logger.exception(f"Failed to open the link with Exception: {str(e)}")
            return False

        try:
            phone_number = WebDriverWait(self.driver, 1200).until(
                ec.presence_of_element_located((By.ID, "null"))).get_attribute("value")
            self.logger.info(f"The phone number is: {phone_number}")
            self.token["phone"] = phone_number
        except TimeoutException as e:
            self.logger.exception(f"Failed to find the phone number input with Exception: {str(e)}")
            return False

        self.wait.until(ec.element_to_be_clickable((By.ID, "field_password"))).send_keys("strongPASS")

        # self.wait.until(ec.element_to_be_clickable((By.XPATH, "//*[@id=hook_Block_AnonymRegistrationEnterPassword]/div[1]/div[1]/div[2]/div/form/div[2]/div[2]/input"))).send_keys(Keys.ENTER)

        self.wait.until(ec.element_to_be_clickable((By.ID, "field_fieldName"))).send_keys(names.get_first_name())
        self.wait.until(ec.element_to_be_clickable((By.ID, "field_surname"))).send_keys(names.get_last_name())

        self.wait.until(ec.element_to_be_clickable((By.ID, "field_birthday"))).send_keys(get_random_date())

        self.wait.until(ec.element_to_be_clickable((By.CLASS_NAME, "btn-group_i_t"))).click()

        # self.wait.until(ec.element_to_be_clickable((By.CLASS_NAME, "button-pro __wide"))).send_keys(Keys.ENTER)

        time.sleep(15)

        if self.driver.current_url == "https://ok.ru/feed":
            self.logger.info("Successful registration!")
            return True

        self.logger.exception("Failed to register!")
        return False

    def create_new_token(self) -> None:
        if not self._register():
            self.logger.info("Failed to register!")
            return

        self.token["proxy"] = self.proxy
        print(self.token)

        try:
            response = self.client.create_token(self.token)
            self.logger.info(f"Token successfully created! {response.content}")
            self._close_driver()
        except Exception as e:
            self.logger.exception(f"Failed to create a new token: {str(e)}")
            self._close_driver()
