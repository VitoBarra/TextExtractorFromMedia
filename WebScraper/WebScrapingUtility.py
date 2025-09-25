# Helper functions for better readability
from enum import Enum

from selenium.common import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


class JobStatus(Enum):
    Success = 0
    PageConnectionError = 1
    GenericError = 2

class PageUnreachable(BaseException):
    pass




def find_element_if_present(driver, by, value, timeout=1):
    """ Finds an element, returns the element if found within the timeout, otherwise None. """
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    except TimeoutException:
        return None


def click_element_if_clickable(driver, element, timeout=5, threadName = "noname"):
    """ Clicks an element if it becomes clickable within the timeout. Returns True if clicked, False otherwise. """
    if not element:
        return False
    try:
        # Pass the element itself, not the locator tuple
        clickable_element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(element)
        )
        clickable_element.click()
        return True
    except TimeoutException:
        print(f"{threadName}: Element found but not clickable within {timeout}s.")
        return False
    except Exception as e:
        print(f"{threadName}: Error during click: {e}")
        return False
