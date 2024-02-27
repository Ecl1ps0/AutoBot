import os.path
import time
import openpyxl

import names
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException, TimeoutException

import configs
from api import APIClient
from .Bot import Bot
from models import Source
from configs.logger import get_logger
from models import linkedin_token


class LinkedInBot(Bot):
    def __init__(self, client: APIClient, token: dict = linkedin_token, proxy: str | None = None):
        super().__init__(client, token, proxy)

        self.login_link = 'https://www.linkedin.com/'
        self.registration_link = 'https://www.linkedin.com/signup'
        self.source = Source.LinkedIn

        self.report_path = "login_report.xlsx"

        self.logger = get_logger(__name__)

    def _login(self) -> bool:
        try:
            self.driver.get(self.login_link)
            self.logger.info(
                F"Start login to LinkedIn account with id: {self.token['id']} and email: {self.token['email']}, on proxy: {self.proxy}")
            self.driver.maximize_window()
        except Exception as e:
            self.logger.exception(f"Failed to open the link with Exception: {str(e)}")

        if self.driver.current_url == 'https://www.linkedin.cn/':
            self.logger.info("Chinese proxy, skip!")
            return False

        self.wait.until(ec.element_to_be_clickable((By.ID, "session_key"))).send_keys(self.token["email"])
        self.wait.until(ec.element_to_be_clickable((By.ID, "session_password"))).send_keys(self.token["password"])

        self.wait.until(ec.element_to_be_clickable(
            (By.XPATH, "//*[@id='main-content']/section[1]/div/div/form/div[2]/button"))).click()

        try:
            WebDriverWait(self.driver, 10).until(
                ec.presence_of_element_located((By.CLASS_NAME, "scaffold-layout__sidebar")))
            self.logger.info("The token is active no need in the verification code!")
            return True
        except TimeoutException:
            self.logger.info("Token is not active need verification code!")

        try:
            WebDriverWait(self.driver, 20).until(ec.presence_of_element_located((By.ID, "captcha-internal")))
            self.logger.info("Need to pass CAPTCHA!")
            input('Continue?\n')
        except TimeoutException:
            self.logger.info("No need pass CAPTCHA!")

        try:
            verification_input = WebDriverWait(self.driver, 30).until(
                ec.element_to_be_clickable((By.ID, "input__email_verification_pin")))
            submit_verification_code_button = self.wait.until(
                ec.element_to_be_clickable((By.ID, "email-pin-submit-button")))

            time.sleep(20)

            onesecmail_params = {
                'action': 'getMessages',
                'login': self.token["email"].split('@')[0],
                'domain': '1secmail.com'
            }

            verification_code = self.client.get_verification_code(onesecmail_params, self.source)
            self.logger.info(f"Verification code is {verification_code}")

            verification_input.send_keys(verification_code)
            submit_verification_code_button.click()
        except TimeoutException:
            self.logger.info("No need in verification code!")

        try:
            WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.ID, "register-phone-challenge")))
            self.logger.info("Need phone number!")
            self.is_banned = True

            return False
        except TimeoutException:
            self.logger.info("No need phone number!")

        try:
            WebDriverWait(self.driver, 5).until(
                ec.element_to_be_clickable((By.ID, "content__button--secondary--muted")))
            self.is_banned = True
            return False
        except TimeoutException:
            self.logger.info("Token is not blocked, continue!")

        try:
            WebDriverWait(self.driver, 5).until(
                ec.presence_of_all_elements_located((By.CLASS_NAME, "id__verify-btn__primary--large")))
            self.logger.info("Need id verifying! Skip!")
            self.is_banned = True
            return False
        except TimeoutException:
            self.logger.info("No need id verifying continue!")

        try:
            self.wait.until(ec.presence_of_element_located((By.CLASS_NAME, "scaffold-layout__sidebar")))
            self.logger.info(f"Succeed Log In to the token with id: {self.token['id']}!")
            self._close_driver()
            return True
        except TimeoutException as e:
            self.logger.exception(f"Failed to login with this exception: {str(e)}")
            self._close_driver()
            return False

    def update_token_to_active(self) -> None:
        if not self.token:
            self.logger.info("Email field is empty!")
            self._close_driver()
            raise Exception("The token email is empty!")

        if self._login() is False:
            self.logger.exception("Failed to log in!")

            if self.is_banned:
                self.token["status"] = 0
                self.client.update_token(self.token)
                self.logger.info("Token has been banned!")

            return

        self.token["status"] = 1
        self.token["proxy"] = self.proxy
        self.token["session"] = '{}'

        try:
            self.client.update_token(self.token)
            self.logger.info("Token successfully updated!")
        except Exception as e:
            self.logger.info(F"Fail to update token: {e}")

    def _register(self, email: str | None = None) -> bool:
        try:
            self.driver.get(self.registration_link)
            self.logger.info(
                f"Start registration to LinkedIn account with email: {email} and dynamic proxy: {self.proxy}")
            self.driver.maximize_window()
        except Exception as e:
            self.logger.exception(f"Failed to open the link with Exception: {str(e)}")

        try:
            WebDriverWait(self.driver, 10).until(ec.element_to_be_clickable((By.ID, "email-address"))).send_keys(email)
            self.driver.find_element(By.ID, "password").send_keys("strongPASS")
        except TimeoutException:
            self.logger.info("Can not find the email and password inputs!")
            return False

        time.sleep(3)

        try:
            self.driver.find_element(By.ID, "in-career-singup-info-transfer-policy").click()
        except NoSuchElementException:
            self.logger.info(f"No submission box")

        self.wait.until(ec.element_to_be_clickable((By.ID, "join-form-submit"))).click()

        self.wait.until(ec.element_to_be_clickable((By.ID, "first-name"))).send_keys(names.get_first_name())
        self.wait.until(ec.element_to_be_clickable((By.ID, "last-name"))).send_keys(names.get_last_name())

        self.driver.find_element(By.ID, "join-form-submit").click()

        time.sleep(5)

        try:
            frame = self.driver.find_element(By.CLASS_NAME, "challenge-dialog__iframe")
            self.driver.switch_to.frame(frame)

            self.driver.find_element(By.ID, "captcha-challenge")
            self.logger.info("Need to pass CAPTCHA!")
            val = input('Continue?\n')
            if val == "skip":
                return False
        except NoSuchElementException:
            self.logger.info("No need pass CAPTCHA!")
            self.driver.switch_to.default_content()

        try:
            frame = self.driver.find_element(By.CLASS_NAME, "challenge-dialog__iframe")
            self.driver.switch_to.frame(frame)

            self.driver.find_element(By.ID, "register-phone-challenge")
            self.logger.info("Phone number is required! Skip!")
            return False
        except NoSuchElementException:
            self.logger.info(f"Phone number is not required")
            self.driver.switch_to.default_content()

        try:
            city = WebDriverWait(self.driver, 10).until(
                ec.element_to_be_clickable((By.ID, "typeahead-input-for-city-district"))).get_attribute("value")

            if not city:
                input("Insert city, do not press continue button!\n")

            self.driver.find_element(By.ID, "ember10").click()

            self.wait.until(ec.element_to_be_clickable((By.ID, "ember16"))).click()
        except TimeoutException:
            self.logger.info("No need to insert city!")
            self.wait.until(ec.element_to_be_clickable((By.ID, "ember9"))).click()

        self.wait.until(ec.element_to_be_clickable((By.CLASS_NAME, "artdeco-button--tertiary"))).click()

        self.wait.until(ec.element_to_be_clickable((By.ID, "typeahead-input-for-school-name"))).send_keys(
            "University of Cambridge")

        start_year_select_element = self.wait.until(
            ec.element_to_be_clickable((By.ID, "onboarding-profile-edu-start-year")))
        start_year_select = Select(start_year_select_element)
        start_year_select.select_by_value("2024")

        graduation_year_select_element = self.wait.until(
            ec.element_to_be_clickable((By.ID, "onboarding-profile-edu-end-year")))
        graduation_year_select = Select(graduation_year_select_element)
        graduation_year_select.select_by_value("2028")

        self.wait.until(ec.element_to_be_clickable((By.ID, "ember20"))).click()

        time.sleep(20)

        onesecmail_params = {
            'action': 'getMessages',
            'login': email.split('@')[0],
            'domain': '1secmail.com'
        }

        verification_code = self.client.get_verification_code(onesecmail_params, self.source,
                                                              is_registration=True)

        self.wait.until(ec.element_to_be_clickable((By.ID, "email-confirmation-input"))).send_keys(verification_code)

        # time.sleep(5)
        # self.driver.find_element(By.CSS_SELECTOR, "label[for=onboarding-job-seeker-intent-radio-button-INACTIVE]").click()

        self.wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, "label[for=onboarding-job-seeker-intent-radio-button-INACTIVE]"))).click()

        self.wait.until(ec.element_to_be_clickable((By.ID, "ember26"))).click()

        self.wait.until(ec.element_to_be_clickable((By.CLASS_NAME, "onboarding-combo-bar__skip"))).click()
        self.wait.until(ec.element_to_be_clickable((By.CLASS_NAME, "artdeco-button.artdeco-button--muted.artdeco-button--4.artdeco-button--tertiary.ember-view.full-width.mv4"))).click()
        try:
            self.driver.find_element(By.CLASS_NAME, "onboarding-get-the-app__next").click()
        except NoSuchElementException:
            pass

        self.token["email"] = email
        self.token["proxy"] = next(self.client.get_proxies(configs.us_proxy_params), None)

        try:
            self.wait.until(ec.presence_of_element_located((By.CLASS_NAME, "scaffold-layout__sidebar")))
            self.logger.info(f"Token successfully registered!")
            self._close_driver()
            return True
        except TimeoutException as e:
            self.logger.exception(f"Failed to register with this exception: {str(e)}")
            self._close_driver()
            return False

    def create_new_token(self, email: str | None = None) -> None:
        if not self._register(email):
            self.logger.info("Failed to register!")
            self._close_driver()
            return

        try:
            response = self.client.create_token(self.token)
            self.logger.info(f"Token successfully created! {response.content}")
            self._close_driver()
        except Exception as e:
            self.logger.exception(f"Failed to create a new token: {str(e)}")
            self._close_driver()

    def __create_report(self) -> None:
        report = {
            'id': self.token['id'],
            'env': self.token['env'],
            'askedPhoneNumber': False,
            'askedIdentityVerification': False,
            'hasCAPTCHA': False,
            'hasVerificationCode': False,
            'isBlocked': False,
        }

        if not os.path.exists(self.report_path):
            workbook = openpyxl.Workbook()
            workbook.save(self.report_path)

        with openpyxl.load_workbook(self.report_path) as workbook:
            sheet = workbook.active

            sheet.append(report.values())

            workbook.save("login_report.xlsx")
