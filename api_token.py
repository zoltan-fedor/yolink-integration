import base64
import logging
import os
import requests
from time import sleep
from typing import Any, Dict, Optional

from exceptions import ClientError, BadRequestError, RateLimitError, UnAuthorizedError, UserNotAuthorizedError


logger = logging.getLogger(__name__)


class BaseService:
    """ Our base service which gets inherited by all our services
    """

    def __init__(self,
                 uaid: str,
                 secret_key: str,
                 access_token: Optional[str] = None,
                 proxies: Optional[Dict[str, str]] = None):
        self.uaid = uaid
        self.secret_key = secret_key

        self.service_definition = {
            'service_url': 'https://api.yosmart.com'
        }
        self.service_name = 'YoSmart'

        # the requests session which we will use to make calls
        # Session() in requests automatically does keep-alive, so this can speed up consecutive requests
        self.session = requests.Session()

        # allow adding proxy settings to the request, example:
        #   proxies = {
        #     'http': 'http://10.10.1.10:3128',
        #     'https': 'http://10.10.1.10:1080'
        #   }
        # You can stop the use of proxies (even if defined in the env variable)
        # if you call this object with empty proxies, like:
        #   proxies = {
        #     'http': '',
        #     'https': ''
        #   }
        if proxies is not None:
            self.session.proxies = proxies
        # also picking the proxies up from the env variables, if they are defined explicitely
        elif os.environ.get('http_proxy') is not None \
                or os.environ.get('https_proxy') is not None \
                or os.environ.get('HTTP_PROXY') is not None \
                or os.environ.get('HTTPS_PROXY') is not None:
            self.session.proxies = {  # type: ignore
                'http': os.environ.get('http_proxy') if os.environ.get('http_proxy') is not None  # type:ignore
                else os.environ.get('HTTP_PROXY'),
                'https': os.environ.get('https_proxy') if os.environ.get('https_proxy') is not None  # type:ignore
                else os.environ.get('HTTPS_PROXY')
            }

        # now that the object is initialized, get the access token
        self.access_token: 'AccessToken' = AccessToken(service=self,
                                                       token=access_token)

    @property
    def _request_headers(self) -> Dict[str, str]:
        """ The http request headers to attach to all requests
        """
        # we are making a call against a REST API, so the 'accept' header should always be there
        headers = {
            'accept': 'application/json'
        }
        if hasattr(self, 'access_token') and self.access_token.token:
            # create the Authorization header with the access header:
            if self.access_token.token.startswith("Bearer "):
                headers['Authorization'] = self.access_token.token
            else:
                headers['Authorization'] = f"Bearer {self.access_token.token}"

        return headers

    def call_service(self, path: str, method: str,
                     additional_headers: Optional[Dict[str, Any]]=None,
                     post_data: Optional[Dict[str, Any]]=None,
                     json: Optional[Dict[str, Any]]=None) -> 'requests.Response':
        """ This is the method which makes all calls to the service
        """
        _renewed_token = False
        _retry_counter = 0
        while True:
            # build the headers we will use in the call
            _headers = self._request_headers
            # add / update headers provided by the additional_headers
            _headers.update(additional_headers or dict())

            # build the url we will call
            _url = self.service_definition['service_url'] + path

            result = self.session.request(method, _url,
                                          headers=_headers,
                                          # the POST request payload:
                                          data=post_data,
                                          # the json request payload:
                                          # see https://stackoverflow.com/questions/9733638/post-json-using-python-requests  # NOPEP8
                                          json=json)

            # handle the different response codes
            if result.status_code >= 300:
                # for 401, unauthenticated, let's try to renew the token and try the call again
                # as it is possible, that simply the token has expired
                # but we only do it once, if we get an error the second time too, then
                # we go with the exception handler
                if result.status_code == 401 and not _renewed_token:
                    self.access_token.renew_token()
                    # mark the fact that we have just renewed the token:
                    _renewed_token = True
                elif result.status_code == 504 and _retry_counter < 5:
                    # for 504 - Gateway timeout, we try it again
                    _retry_counter += 1
                    # sleep 100ms if we have already tried more than twice
                    sleep(0.1 * (_retry_counter - 1))
                else:
                    # for all other error codes we call the error handler
                    self._exception_handler(result)
                    break
            else:
                # this is the happy route, no error code returned
                break

        return result

    def _exception_handler(self, result) -> None:
        """ Exception handler to route the errors to the right exception handler
        """
        try:
            response_content = result.json()
        except Exception:
            response_content = result.text

        # map the response codes to exception classes defined in exceptions.py:
        exceptions = {
            400: BadRequestError,
            403: UserNotAuthorizedError,
            401: UnAuthorizedError,
            429: RateLimitError
        }
        exception_class = exceptions.get(result.status_code, ClientError)

        raise exception_class(url=result.url,
                              status=result.status_code,
                              service=self.service_name,  # type: ignore
                              content=response_content)

    def renew_access_token(self) -> None:
        """ It renews the access token
        """
        self.access_token.renew_token()

    def get_access_token(self) -> str:
        """ It retrieves the currently used access token
        """
        return self.access_token.token

    def get_home_id(self) -> str:
        """Get the Home id which is required to subscribe to MQTT events"""
        r = self.call_service(path='/open/yolink/v2/api',
                              method='POST',
                              additional_headers={},
                              post_data={
                                  'method': 'Home.getGeneralInfo'
                              })
        return r.json()['data']['id']


class AccessToken:
    """ The access token used to access the service
    """

    def __init__(self,
                 service: 'BaseService',
                 token: Optional[str] = None):

        # the service against which access token is issued and used
        self.service: 'BaseService' = service

        # the current access token either provided or
        # requested from the service
        self.token: str = token if token else self.get_new_token()

    def get_new_token(self) -> str:
        """ Get a new access token from the service
        """

        # base64 encode the username and api key for HTTP Base authentication
        # _pass = self.service.username + ':' + self.service.api_key
        _headers = {
            # 'Authorization': f"Basic {base64.b64encode(_pass.encode('ascii')).decode('ascii')}"
        }

        r = self.service.call_service(path='/open/yolink/token',
                                      method='POST',
                                      additional_headers=_headers,
                                      post_data={
                                          'grant_type': 'client_credentials',
                                          'client_id': self.service.uaid,
                                          'client_secret': self.service.secret_key
                                      })

        return r.json()['access_token']

    def renew_token(self) -> None:
        """ It renews the token
        """
        self.token = self.get_new_token()
