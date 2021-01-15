"""Grab pictures."""

import logging
import os
import sys
import time
from os import environ

import pdb

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.remote.webelement import WebElement
    from selenium.webdriver.support import expected_conditions as EC

except ModuleNotFoundError as e:
    print("Some Modules are missing: {}".format(e))

DIRNAME = os.path.dirname(__file__)
IMG_FOLDER = os.path.normpath(os.path.join(DIRNAME, 'images'))

LOGIN = environ["ALTAREA_LOGIN"]
PASSWORD = environ["ALTAREA_PASSWORD"]
ALTAREA_URL = "https://altarea-partenaires.com"
IDF_REGION = "Ile-de-France"

# WEBDRIVER
EXECUTABLE_PATH = "C:\Program Files (x86)\chromedriver.exe"

# LOGGING
LOG_PATH = os.path.normpath(os.path.join(DIRNAME, "logs"))
LOG_FORMAT = "[%(asctime)s - %(name)s] - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
LOG_EXT = ".log"
LOG_FILE = os.path.join(LOG_PATH,
    "{script}_ALTAREA{ext}".format(
        **{'script': os.path.basename(sys.argv[0].split('.')[0]),
           'ext':LOG_EXT}))
logging.basicConfig(
        filename = LOG_FILE, 
        level = logging.INFO,
        format= LOG_FORMAT)

LOGGER = logging.getLogger()


def grab():
    """Grab screenshots."""
    # set up the driver
    driver = chrome_driver(EXECUTABLE_PATH)
    try:
        # go to website of concern
        driver.get(ALTAREA_URL)
        LOGGER.info("Chargement de la page d'accueil : %s", driver.title)

        # enter your session
        if not connect(driver):
            LOGGER.info("Plusieurs causes peuvent être à l'origine de l'interruption de ce processus")
            return None

        # handle the modal element
        handle_modal(driver)
        
        # search by region of concern
        LOGGER.info("Lancement de la recherche par critères")
        select_by_region(driver, IDF_REGION)

    except:
        raise

    finally:
        driver.quit()


def chrome_driver(executable_path, options, t=10):
    """Return chrome driver."""
    driver = webdriver.Chrome(executable_path, options=options)
    driver.maximize_window()
    driver.implicitly_wait(int(t))
    return driver


def connect(driver):
    """Connect to a session."""
    try:
        login_modal = driver.find_element_by_xpath(
            '/html/body/header/div/div/div[2]/div/button')
        if login_modal.get_attribute("data-target") == "#login-modal":
            login_modal.click()
            LOGGER.info("Lancement de l'authentification")
            driver.get_screenshot_as_file('images/shot_login_modal.png')

            if not sign_in(driver):
                return False
    except Exception as ex:
        LOGGER.error("Un problème est survenu : %s", ex)
        return False
    else:
        return True

def sign_in(driver):
    """Fill in the login fields with your credentials."""
    try:
        LOGGER.info("Saisie de l'identifiant")
        driver.find_element_by_id('login-email').send_keys(LOGIN)
        LOGGER.info("Saisie du mot de passe")
        driver.find_element_by_id('login-password').send_keys(PASSWORD)
        driver.find_element_by_xpath("//*[@id='dashboardContent']/form/div[2]/div/button").click()
        if not wait_signing_in(driver):
            return False
    except:
        return False
    else:
        return True


def wait_signing_in(driver):
    """Wait while signing in."""
    try:
        i = 0
        LOGGER.info("En attente de chargement de la page...")
        while True:
            if driver.current_url == "https://altarea-partenaires.com/wp-login.php":
                LOGGER.warning("Une erreur critique est survenue sur votre site")
                driver.get_screenshot_as_file('images/shot_erreur.png')
                return False
            if driver.current_url == "https://altarea-partenaires.com/accueil/":
                LOGGER.info("Connexion réussie")
                break
            if i == 30:
                LOGGER.info("Échec de la connexion")
                return False
            time.sleep(1)
            i += 1
    except:
        return False
    else:
        return True


def handle_modal(driver):
    """Handle the modal element if present."""
    try:
        first_modal = driver.find_element_by_xpath(
            "//*[@id='first_sign-in_modal']/div/div/div[1]/button")
        first_modal.is_displayed()
    except:
        LOGGER.warning("Il n'y a pas de fenêtre publicitaire")
    else:
        LOGGER.info("Fermeture de la fenêtre publicitaire")
        first_modal.click()


def select_by_region(driver, region):
    """Select a region."""
    dept_combo_box = driver.find_element_by_xpath(
        "//*[@id='select2-departements-container']")
    submit_by_program = driver.find_element_by_xpath(
        "//*[@id='form-recherche']/div[4]/div/button[1]")
    action = ActionChains(driver)
    action.move_to_element(dept_combo_box).click()
    action.send_keys(region)
    action.send_keys(Keys.ENTER)
    action.move_to_element(submit_by_program).click()
    action.perform()
    LOGGER.info("Chargement des informations pour la région Ile-de-France")
    driver.get_screenshot_as_file('images/shot_idf.png')


def main():
    """Process the capture of pictures."""
    try:
        LOGGER.info("Lancement du programme")
        # launch grabbing
        grab()

    except FileNotFoundError as err:
        LOGGER.error("Un problème est survenu : %s", err)

    except AssertionError as ae:
        LOGGER.error("Il n'y a aucune donnée à traiter : %s", ae)

    except KeyboardInterrupt:
        print("\n> Processus arrêté par l'utilisateur\n")
        LOGGER.error("Processus arrêté par l'utilisateur")

    finally:
        print("\n> Fin du processus")
        LOGGER.info("Fin du processus")

if __name__ == '__main__':
    main()
