import time
from random import randrange

import names
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from api.APIClient import APIClient
from .Bot import Bot
from configs.logger import get_logger
from models.Source import Source
from models.tokens import outlook_token


class OutlookBot(Bot):
    def __init__(self, client: APIClient, token: dict = outlook_token, proxy: str | None = None):
        super().__init__(client, token, proxy)

        self.login_link = ''
        self.registration_link = 'https://signup.live.com/'
        self.source = Source.Outlook

        self.logger = get_logger(__name__)

    def _register(self, email: str | None = None) -> bool:
        try:
            self.driver.get(self.registration_link)
            self.logger.info(
                F"Start registration to LinkedIn account with email: {email} and proxy: {self.proxy}")
            self.driver.maximize_window()
        except Exception as e:
            self.logger.exception(f"Failed to open the link with Exception: {str(e)}")

        self.wait.until(ec.element_to_be_clickable((By.ID, "MemberName"))).send_keys(email)
        self.wait.until(ec.element_to_be_clickable((By.ID, "iSignupAction"))).click()

        self.wait.until(ec.element_to_be_clickable((By.ID, "PasswordInput"))).send_keys("strongPASS")
        self.wait.until(ec.element_to_be_clickable((By.ID, "iSignupAction"))).click()

        self.wait.until(ec.element_to_be_clickable((By.ID, "FirstName"))).send_keys(names.get_first_name())
        self.wait.until(ec.element_to_be_clickable((By.ID, "LastName"))).send_keys(names.get_last_name())
        self.wait.until(ec.element_to_be_clickable((By.ID, "iSignupAction"))).click()

        month_select_element = self.wait.until(
            ec.element_to_be_clickable((By.ID, "BirthMonth")))
        month_select = Select(month_select_element)
        month_select.select_by_value(str(randrange(1, 12)))

        day_select_element = self.wait.until(
            ec.element_to_be_clickable((By.ID, "BirthDay")))
        day_select = Select(day_select_element)
        day_select.select_by_value(str(randrange(1, 28)))

        self.wait.until(ec.element_to_be_clickable((By.ID, "BirthYear"))).send_keys(str(randrange(1990, 2000)))
        self.wait.until(ec.element_to_be_clickable((By.ID, "iSignupAction"))).click()

        verification_code_input = self.wait.until(ec.element_to_be_clickable((By.ID, "VerificationCode")))

        time.sleep(40)

        onesecmail_params = {
            'action': 'getMessages',
            'login': email.split('@')[0],
            'domain': '1secmail.com',
        }

        verification_code = self.client.get_verification_code(onesecmail_params, Source.Outlook, True)
        verification_code_input.send_keys(verification_code)
        self.wait.until(ec.element_to_be_clickable((By.ID, "iSignupAction"))).click()

        self.wait.until(ec.presence_of_element_located((By.ID, "StickyFooter"))).find_element(By.ID, "id__0").click()

        self.wait.until(ec.element_to_be_clickable((By.ID, "idSIButton9"))).click()

        try:
            self.wait.until(ec.presence_of_element_located((By.ID, "main-content-landing-react")))
            self.logger.info("Successful registration!")
            return True
        except TimeoutException:
            self.logger.exception("Failed to register!")
            return False

    def create_new_token(self, email: str | None = None) -> None:
        if not self._register(email):
            self.logger.info("Failed to register!")
            return

        # try:
        #     response = self.client.create_token(self.token)
        #     self.logger.info(f"Token successfully created! {response.content}")
        #     self._close_driver()
        # except Exception as e:
        #     self.logger.exception(f"Failed to create a new token: {str(e)}")
        #     self._close_driver()
