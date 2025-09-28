# Helper functions for better readability
from enum import Enum
from selenium.common import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from Utility.Logger import info, warning, error, debug

class JobStatus(Enum):
    Success = 0
    PageConnectionError = 1
    GenericError = 2

class PageUnreachable(BaseException):
    pass


def find_element_if_present(driver, by, value, timeout=1):
    """
    Finds an element, returns the element if found within the timeout, otherwise None.
    """
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    except TimeoutException:
        debug(f"Element not found within {timeout}s: {value}")
        return None


def click_element_if_clickable(driver, element, timeout=5, threadName="noname"):
    """
    Clicks an element if it becomes clickable within the timeout.
    Returns True if clicked, False otherwise.
    """
    if not element:
        debug(f"{threadName}: No element provided to click.")
        return False
    try:
        clickable_element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(element)
        )
        clickable_element.click()
        info(f"{threadName}: Element clicked successfully.")
        return True
    except TimeoutException:
        warning(f"{threadName}: Element found but not clickable within {timeout}s.")
        return False
    except Exception as e:
        error(f"{threadName}: Error during click: {e}")
        return False
