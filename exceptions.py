""" All exceptions for our module
"""


class ClientError(Exception):
    """ The base client exception
    """
    message = u"An unknown error occurred when calling {url}. Response content: {content}"

    def __init__(self, url: str, status: int, service: str, content: str):
        """ Initialize the ClientError exception

        Params:
            - url: the URL that was called
            - status: the status code of the error response
            - service: the name of the Service used
            - content: content of the response
        """
        self.url = url
        self.status = status
        self.service = service
        self.content = content

    def __str__(self):
        return self.message.format(url=self.url, content=self.content)

    def __unicode__(self):
        return self.__str__()


class BadRequestError(ClientError):
    """
    HTTP Error Code: 400
    There was a bad request
    """
    message = u"Bad request for {url}. Possibly an incorrectly formatted JSON is provided, fields are missing " + \
              u"or badly formatted. Read the returned JSON validation error. Response content: {content}"


class UnAuthorizedError(ClientError):
    """
    HTTP Error Code: 401
    The session is unauthenticated
    """
    message = u"Expired/unauthenticated session for {url}. Response content: {content}"


class UserNotAuthorizedError(ClientError):
    """
    HTTP Error Code: 403
    The user is not authorized
    """
    message = u"The user is not authorized when calling {url}. Response content: {content}"


class RateLimitError(ClientError):
    """
    HTTP Error Code: 429
    The user hit his rate limit
    """
    message = u"You hit your rate limit when calling {url}. Response content: {content}"
