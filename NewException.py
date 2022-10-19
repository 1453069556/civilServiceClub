from selenium.common import WebDriverException


class AcceptableException(WebDriverException):
    """
    Thrown when frame or window target to be switched doesn't exist.
    """
    pass