import json
import re
import time

import requests

from typing import Generator

from configs.logger import get_logger
from models.Source import Source


class APIClient:
    def __init__(self, access_token_payload: dict):
        self.access_token_url = 'https://auth.argus360.kz/auth/realms/argus360api/protocol/openid-connect/token'
        self.create_token_url = 'https://avatarbackend.argus360.kz/tokens'
        self.onesecmail_url = 'https://www.1secmail.com/api/v1/'
        self.avatar_tokens_url = 'https://avatarbackend.argus360.kz/tokens/'
        self.tokens_url = 'https://avatarbackend.argus360.kz/filter'
        self.proxy_url = 'https://proxys.argus360.kz/proxy/formatted'

        self.access_token = self.get_access_token(access_token_payload)
        self.auth_header = {
            'Authorization': f"Bearer {self.access_token}"
        }

        self.logger = get_logger(__name__)

    def get_tokens(self, params: dict) -> Generator[dict, None, None]:
        for token in requests.get(self.tokens_url, params=params, headers=self.auth_header).json()[::-1]:
            yield token

    def create_token(self, token: dict) -> requests.models.Response:
        self.auth_header['Content-Type'] = 'application/json'
        return requests.post(self.create_token_url, json.dumps(token), headers=self.auth_header)

    def get_access_token(self, payload: dict) -> str:
        header = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(self.access_token_url, data=payload, headers=header)

        return response.json()["access_token"]

    def get_proxies(self, params: dict) -> Generator[str, None, None]:
        for proxy in requests.get(self.proxy_url, params=params).json():
            yield proxy

    def get_verification_code(self, params: dict, source: Source, is_registration: bool = False) -> str:
        match source:
            case Source.LinkedIn:
                response = requests.get(self.onesecmail_url, params=params).json()

                if not is_registration:
                    try:
                        verification_code = response[0]["subject"][-6:]
                        return verification_code.strip()
                    except IndexError:
                        time.sleep(10)
                        self.logger.info("Fail to fetch verification code! Repeat fetching!")
                        self.get_verification_code(params, source, is_registration)

                regex_pattern = r'(\d{6})'
                try:
                    verification_code = re.search(regex_pattern, response[0]["subject"]).group(1)
                    return verification_code.strip()
                except (IndexError, None):
                    time.sleep(10)
                    self.logger.info("Fail to fetch verification code! Repeat fetching!")
                    self.get_verification_code(params, source, is_registration)

            case Source.Twitter:
                response = requests.post(self.onesecmail_url, params=params).json()

                if not is_registration:
                    return ""

                regex_pattern = r'(\d{6})'

                try:
                    verification_code = re.search(regex_pattern, response[0]["subject"]).group(1)

                    return verification_code.strip()
                except IndexError:
                    time.sleep(10)
                    self.logger.info("Fail to fetch verification code! Repeat fetching!")
                    self.get_verification_code(params, source, is_registration)
                    
            case Source.Outlook:
                response = requests.post(self.onesecmail_url, params=params).json()
                try:
                    mail_id = response[0]["id"]

                    params['action'] = "readMessage"
                    params['id'] = mail_id
                except Exception as e:
                    time.sleep(10)
                    self.logger.info(f"Fail to fetch verification code! Repeat fetching! {e}")
                    self.get_verification_code(params, source, is_registration)

                response = requests.post(self.onesecmail_url, params=params).json()

                if not is_registration:
                    return ""

                regex_pattern = r'(\d{6})'

                verification_code = re.search(regex_pattern, response["textBody"]).group(1)

                return verification_code.strip()

            case _:
                return "Unknown Source"

    def update_token(self, updated_token: dict) -> None:
        full_url = self.avatar_tokens_url + updated_token["id"]

        requests.put(full_url, data=json.dumps(updated_token), headers=self.auth_header)
