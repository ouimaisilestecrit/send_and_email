"""Grab pictures."""

import logging
import os
import sys
import time

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

LOGIN = os.environ["ALTAREA_LOGIN"]
PASSWORD = os.environ["ALTAREA_PASSWORD"]
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
    try:
        # set up the driver
        driver = chrome_driver(EXECUTABLE_PATH)

        # go to website of concern
        driver.get(ALTAREA_URL)
        time.sleep(5)
        LOGGER.info("Chargement de la page d'accueil : %s", driver.title)

        # open your session
        if not connect(driver):
            LOGGER.warning("Plusieurs causes peuvent être à l'origine de l'interruption de ce processus")
            return None

        # handle the modal element
        locator = r"//*[@id='first_sign-in_modal']/div/div/div[1]/button"
        handle_modal(driver, locator)
        
        # search by region of concern
        LOGGER.info("Lancement de la recherche par critères")
        select_by_region(driver, IDF_REGION)

        # collect data
        get_program_data(driver)

    except:
        raise

    finally:
        driver.quit()


def get_by_id(driver, locator):
    """Return an element from its id locator."""
    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, locator)))
        if not isinstance(element, WebElement):
            return None
        return element
    except:
        LOGGER.error("An error occurred when selecting from: %s", locator)
        return None


def get_by_xpath(driver, locator):
    """Return an element from its xpath locator."""
    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, locator)))
        if not isinstance(element, WebElement):
            return None
        return element
    except:
        LOGGER.error("An error occurred when selecting from: %s", locator)
        return None


def get_by_tag_name(driver, locator):
    """Return an element from its tag name locator."""
    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, locator)))
        if not isinstance(element, WebElement):
            return None
        return element
    except:
        LOGGER.error("An error occurred when selecting from: %s", locator)
        return None


def chrome_driver(executable_path, t=10):
    """Return chrome driver."""
    driver = webdriver.Chrome(executable_path)
    driver.implicitly_wait(int(t))
    driver.maximize_window()
    return driver


def connect(driver):
    """Connect to a session."""
    try:
        login_modal = get_by_xpath(driver,
            r"/html/body/header/div/div/div[2]/div/button")
        if login_modal.get_attribute("data-target") == "#login-modal":
            login_modal.click()
            LOGGER.info("Lancement de l'authentification")

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
        get_by_id(driver, 'login-email').send_keys(LOGIN)
        LOGGER.info("Saisie du mot de passe")
        get_by_id(driver, 'login-password').send_keys(PASSWORD)
        get_by_xpath(driver,
            r"//*[@id='dashboardContent']/form/div[2]/div/button").click()
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
        LOG_MSG = r"https://altarea-partenaires.com/wp-login.php"
        ERR_MSG = r"Une erreur critique est survenue sur votre site"
        HOME_URL = r"https://altarea-partenaires.com/accueil/"
        LOGGER.info("En attente de chargement de la page...")
        while True:
            if driver.current_url == LOG_MSG:
                LOGGER.warning("%s", ERR_MSG)
                return False
            if driver.current_url == HOME_URL:
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


def handle_modal(driver, locator):
    """Handle the modal element if present."""
    try:
        first_modal = driver.find_element_by_xpath(locator)
        first_modal.is_displayed()
    except:
        LOGGER.warning("Il n'y a pas de fenêtre publicitaire")
    else:
        LOGGER.info("Fermeture de la fenêtre publicitaire")
        first_modal.click()


def select_by_region(driver, region):
    """Select a region."""
    LOGGER.info("Chargement des informations pour la région Ile-de-France")
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
    time.sleep(3)


def get_program_data(driver):
    """ Get prgramm data."""
    xpath_tmpl = r"//*[@id='results-prog']/div[{}]"
    programs = driver.find_elements_by_xpath("//*[@id='results-prog']/div")
    data_count = int(driver.find_element_by_id('results-prog').get_attribute('data-count'))
    LOGGER.info("Data count: %d", data_count)

    # pdb.set_trace()
    for i, a_program in enumerate(programs):
        commune_name = a_program.find_element_by_class_name('font-bold').text
        LOGGER.info("Commune: %s", commune_name)

        nb_lgt_dispo = a_program.find_element_by_class_name('highlight-keys').text
        long_nb_lgt_dispo = ' '.join(nb_lgt_dispo.split('\n'))
        LOGGER.info("Nb logement dispo: %s", long_nb_lgt_dispo)

        action = ActionChains(driver)
        ele = a_program.find_element_by_xpath(xpath_tmpl.format(i+1))
        LOGGER.info("Program xpath: %s", xpath_tmpl.format(i+1))
        action.move_to_element(ele).perform()
        time.sleep(2)

        # save screenshot
        filename = "images/shot_{}_{}.png".format(
            '_'.join(commune_name.split()),
            '_'.join(str(nb_lgt_dispo.split('\n')[0]).split()))
        LOGGER.info("Shot filename: %s", filename)
        driver.get_screenshot_as_file(filename)
        time.sleep(2)
        LOGGER.info("end Program \n")
        # pdb.set_trace()

    # next_button = driver.find_element_by_class_name('next')
    # prev_button = driver.find_element_by_class_name('prev')

def main():
    """Process the capture of pictures."""
    try:
        LOGGER.info("\n")
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
