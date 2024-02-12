import time
from random import randrange

import names
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select

from api import APIClient
from .Bot import Bot
from configs.logger import get_logger
from models import Source
from models import twitter_token


class TwitterBot(Bot):
    def __init__(self, client: APIClient, token: dict = twitter_token, proxy: str | None = None):
        super().__init__(client, token, proxy)

        self.login_link = ''
        self.registration_link = 'https://twitter.com/i/flow/signup'
        self.source = Source.Twitter

        self.logger = get_logger(__name__)

    def _login(self) -> bool:
        pass

    def _register(self, email: str | None = None) -> bool:
        try:
            self.driver.get(self.registration_link)
            self.logger.info(
                f"Start registration to Twitter account with email: {email} and proxy: {self.proxy}")
            self.driver.maximize_window()
        except Exception as e:
            self.logger.exception(f"Failed to open the link with Exception: {str(e)}")

        self.wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role=button]")))[2].click()

        self.wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role=button]")))[1].click()

        self.wait.until(ec.element_to_be_clickable((By.NAME, "name"))).send_keys(names.get_first_name())
        self.wait.until(ec.element_to_be_clickable((By.NAME, "email"))).send_keys(email)

        month_select_element = self.wait.until(ec.element_to_be_clickable((By.ID, "SELECTOR_1")))
        month_select = Select(month_select_element)
        month_select.select_by_value(str(randrange(1, 12)))

        day_select_element = self.wait.until(ec.element_to_be_clickable((By.ID, "SELECTOR_2")))
        day_select = Select(day_select_element)
        day_select.select_by_value(str(randrange(1, 28)))

        year_select_element = self.wait.until(ec.element_to_be_clickable((By.ID, "SELECTOR_3")))
        year_select = Select(year_select_element)
        year_select.select_by_value(str(randrange(1990, 2002)))

        time.sleep(5)

        self.wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role=button]")))[2].click()

        self.wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role=button]")))[1].click()

        self.wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role=button]"))).pop().click()

        try:
            verification_code_input = self.wait.until(ec.element_to_be_clickable((By.NAME, "verfication_code")))

            time.sleep(30)

            onesecmail_params = {
                'action': 'getMessages',
                'login': email.split('@')[0],
                'domain': '1secmail.com'
            }

            verification_code = self.client.get_verification_code(onesecmail_params, self.source, True)

            verification_code_input.send_keys(verification_code)
        except TimeoutException:
            self.logger.info("Can not find verification input!")

        self.wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role=button]"))).pop().click()

        self.wait.until(ec.element_to_be_clickable((By.NAME, "password"))).send_keys("strongPASS")

        time.sleep(3)

        self.wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role=button]")))[1].click()

        self.wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role=button]"))).pop().click()

        username = self.wait.until(ec.element_to_be_clickable((By.NAME, "username"))).get_attribute("value")

        self.logger.info(f"Username: {username}")

        self.token["username"] = username
        self.token["email"] = email
        self.token["proxy"] = self.proxy

        self.wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-testid='ocfEnterUsernameSkipButton']")))[0].click()

        self.wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role=button]")))[1].click()
        self.wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role=button]"))).pop().click()

        self.wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-testid=cellInnerDiv]")))[2].find_elements(By.CSS_SELECTOR, "div[role=button]")[0].click()
        time.sleep(3)

        self.wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role=button]"))).pop().click()

        try:
            self.wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "div[role=button]")))
            self.logger.info("Successful registration!")
            return True
        except TimeoutException:
            self.logger.exception("Failed to register!")
            return False

    def create_new_token(self, email: str | None = None) -> None:
        if not self._register(email):
            self.logger.info("Failed to register!")
            return

        try:
            response = self.client.create_token(self.token)
            self.logger.info(f"Token successfully created! {response.content}")
            self._close_driver()
        except Exception as e:
            self.logger.exception(f"Failed to create a new token: {str(e)}")
            self._close_driver()
