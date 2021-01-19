"""Grab pictures."""

import imghdr
import locale
import logging
import os
import pickle
import smtplib
import sys
import time

from collections import OrderedDict
from datetime import datetime as dt
from email.message import EmailMessage
from string import Template

import pdb

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.remote.webelement import WebElement
    from selenium.webdriver.support import expected_conditions as EC

    from shutil import move, Error
    
except ModuleNotFoundError as e:
    print("Some Modules are missing: {}".format(e))

DIRNAME = os.path.dirname(__file__)
IMG_BASE = os.path.normpath(os.path.join(DIRNAME, 'images/base'))
IMG_MAIL = os.path.normpath(os.path.join(DIRNAME, 'images/mail'))
IMG_TEMP = os.path.normpath(os.path.join(DIRNAME, 'images/temp'))
IMG_BASE_LIST = os.listdir(IMG_BASE)
IMG_MAIL_LIST = os.listdir(IMG_MAIL)
IMG_TEMP_LIST = os.listdir(IMG_TEMP)

# email credentials
MAIL_LOGIN = os.environ['EDN_LOGIN']
MAIL_PASSW = os.environ['EDN_PASSWORD']

# email gateway parameters
MAILBOX_HOST = 'smtp.office365.com'
MAILBOX_PORT = 587

# website credentials
LOGIN = os.environ["ALTAREA_LOGIN"]
PASSWORD = os.environ["ALTAREA_PASSWORD"]

# constants
ALTAREA_URL = "https://altarea-partenaires.com"
IDF_REGION = "Ile-de-France"
PROGRAMS_PER_PAGE = 12
ERR_URL = r"https://altarea-partenaires.com/wp-login.php"
ERR_MSG = r"Une erreur critique est survenue sur votre site"
HOME_URL = r"https://altarea-partenaires.com/accueil/"

# template dictionary of file's message and subjects
TEMPLATE_DICT = OrderedDict([
    (0,
        ['template.txt',
         "des nouvelles de ventes d'Altarea Partenaires !"]),
    (1,
        ['template_no_picture.txt',
         "aucune nouveauté sur les ventes d'Altarea Partenaires !"]),
    (2,
        ['template_not_available.txt',
         "Alerte ! Problème de connexion sur Altarea Partenaires !"])])

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

logger = logging.getLogger()


def get_users(filename):
    """Read contacts.

    Function to read the contacts from a given contact file
    and return a list of names and email adresses.
    """
    names = []
    emails = []
    with open(filename, 'r', encoding='utf-8') as contacts_file:
        for a_contact in contacts_file:
            names.append(a_contact.split()[0])
            emails.append(a_contact.split()[1])
    return names, emails


def read_template(filename):
    """Read template.

    Function to read the template from a given template file
    and return it.
    """
    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)


def send_mail(filename, sub, folder=IMG_MAIL_LIST):
    """Send email with attachments."""
    # read contacts
    names, emails = get_users('users.txt')

    # set timecode on email's subject
    locale.setlocale(locale.LC_TIME, "fr_FR")
    subject = "{at} : {sub}".format(
        **{'at': dt.today().strftime('%A %d %b %y, %Hh%M').capitalize(),
           'sub': sub})

    # for each contact, send the email:
    for name, email in zip(names, emails):
        # add in the actual person name to template
        msg_template = read_template(filename)
        message = msg_template.substitute(PERSON_NAME=name.title())

        # Create the container email message.
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = MAIL_LOGIN
        msg['To'] = email
        msg.preamble = 'You will not see this in a MIME-aware mail reader.\n'

        # add in the message body
        msg.set_content(message)

        # Open the files in binary mode.
        # Use imghdr to figure out the
        # MIME subtype for each specific image.
        if folder:
            for file_ in folder:
                file_ = os.path.normpath(os.path.join(IMG_MAIL, file_))
                with open(file_, 'rb') as fp:
                    img_data = fp.read()
                msg.add_attachment(img_data, maintype='image',
                                   subtype=imghdr.what(None, img_data))

        # Send the email via our own SMTP server.
        # Terminate the SMTP session and close the connection
        with smtplib.SMTP(host=MAILBOX_HOST, port=MAILBOX_PORT) as s:
            # enable security
            s.starttls()
            # login with email credential
            s.login(MAIL_LOGIN, MAIL_PASSW)
            s.send_message(msg)

        del msg


def grab():
    """Grab screenshots."""
    state = False
    # set up the driver
    driver = chrome_driver(EXECUTABLE_PATH)
    try:
        # go to website of concern
        driver.get(ALTAREA_URL)
        time.sleep(10)
        logger.info("Chargement de la page d'accueil : %s", driver.title)

        # open your session
        if not connect(driver):
            logger.warning("Plusieurs causes peuvent être à l'origine de l'interruption de ce processus")
            state = False
            return None

        # handle the modal element
        locator = r"//*[@id='first_sign-in_modal']/div/div/div[1]/button"
        handle_modal(driver, locator)
        
        # search by region of concern
        logger.info("Lancement de la recherche par critères")
        select_by_region(driver, IDF_REGION)

        # collect data
        programs_element = driver.find_element_by_id('results-prog')
        number_programs = int(programs_element.get_attribute('data-count'))
        get_program_data(driver, number_programs)
        num = len(os.listdir(IMG_TEMP))  # nombre des photos sauvegardées
        if num == number_programs:
            logger.info("Toutes les photos des programmes sont sauvegardées")
            state = True
        else:
            logger.info("%d photos sur %d sauvegardées", num, number_programs)
            state = False

    except Exception as ex:
        logger.error("Un problème est survenu : %s", ex)
        state = False
        return None

    finally:
        driver.quit()

    return state


def get_by_id(driver, locator):
    """Return an element from its id locator."""
    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, locator)))
        if not isinstance(element, WebElement):
            return None
        return element
    except:
        logger.error("An error occurred when selecting from: %s", locator)
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
        logger.error("An error occurred when selecting from: %s", locator)
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
        logger.error("An error occurred when selecting from: %s", locator)
        return None


def chrome_driver(executable_path, t=10):
    """Return chrome driver."""
    driver = webdriver.Chrome(executable_path)
    driver.implicitly_wait(int(t))
    driver.maximize_window()
    return driver


def connect(driver, t=1):
    """Connect to a session."""
    try:
        login_modal = get_by_xpath(driver, r"/html/body/header/div/div/div[2]/div/button")
        if login_modal.get_attribute("data-target") == "#login-modal":
            login_modal.click()
            logger.info("Lancement de l'authentification")

            if not sign_in(driver, t):
                return False

    except Exception as ex:
        logger.error("Un problème est survenu : %s", ex)
        return False
    else:
        return True


def sign_in(driver, t=1):
    """Fill in the login fields with your credentials."""
    try:
        logger.info("time sleep: %d", t)
        logger.info("Saisie de l'identifiant")
        time.sleep(int(t))
        get_by_id(driver, 'login-email').send_keys(LOGIN)
        logger.info("Saisie du mot de passe")
        time.sleep(int(t))
        get_by_id(driver, 'login-password').send_keys(PASSWORD)
        time.sleep(int(t))
        get_by_xpath(driver, r"//*[@id='dashboardContent']/form/div[2]/div/button").click()

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
        logger.info("En attente de chargement de la page...")
        while True:
            if driver.current_url == ERR_URL:
                logger.warning("%s", ERR_MSG)
                return False
            if driver.current_url == HOME_URL:
                logger.info("Connexion réussie")
                break
            if i == 30:
                logger.info("Échec de la connexion")
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
        logger.warning("Il n'y a pas de fenêtre publicitaire")
    else:
        logger.info("Fermeture de la fenêtre publicitaire")
        first_modal.click()


def select_by_region(driver, region):
    """Select a region."""
    logger.info("Chargement des informations pour la région Ile-de-France")
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


def get_program_data(driver, all_programs):
    """ Get program data."""
    logger.info("Quantité des programmes immobiliers : %d", all_programs)
    pages = number_of_page(all_programs, PROGRAMS_PER_PAGE)
    logger.info("Number of page : %d", pages)

    # collect programs within a page
    for page in range(pages):
        programs = driver.find_elements_by_xpath("//*[@id='results-prog']/div")
        for i, a_program in enumerate(programs):
            fetch_main_data(driver, a_program, i+1, page+1)
        logger.info("Fin des programmes de la page : %d\n", page+1)

        # avoid to click next button on the last page
        if page != pages-1:
            logger.info("Go to next page")
            driver.find_element_by_class_name('next').click()
            wait_next_page(driver, page+2)


def wait_next_page(driver, page, t=1):
    """Wait while next page is loading."""
    next_url = r"https://altarea-partenaires.com/recherche/page/{}/"
    logger.info("next_url.format(page): %s", next_url.format(page))
    while True:
        if driver.current_url == next_url.format(page):
            break
        time.sleep(int(t))


def get_text(driver, locator):
    """Return text if available."""
    try:
        return driver.find_element_by_class_name(locator).text
    except:
        return "No value"


def number_of_page(all, per_page):
    """Return number of page."""
    num = all // per_page
    mod = all % per_page
    if mod != 0:
        return num + 1
    return num


def fetch_main_data(driver, program, i, page):
    """Fetch main program data."""
    logger.info("Début du programme\n")
    residence_name = get_text(program, r'font-regular')
    logger.info("Résidence : %s", residence_name)

    commune_name = get_text(program, r'font-bold')
    logger.info("Commune : %s", commune_name)

    nb_lgt_dispo = get_text(program, r'highlight-keys')
    long_nb_lgt_dispo = ' '.join(nb_lgt_dispo.split('\n'))
    logger.info("Nb logement dispo : %s", long_nb_lgt_dispo)

    # move element to program to capture
    xpath_tmpl = r"//*[@id='results-prog']/div[{}]/div/div[2]"
    action = ActionChains(driver)
    ele = program.find_element_by_xpath(xpath_tmpl.format(i))
    action.move_to_element(ele).perform()
    time.sleep(2)

    # save screenshot
    filename = os.path.normpath(os.path.join(IMG_TEMP,
        "{page}_{rang}_{name}_{city}_{size}.png".format(
            **{'page': page,
               'rang': str(i).zfill(2),
               'name': '_'.join(residence_name.split()),
               'city': '_'.join(commune_name.split()),
               'size': '_'.join(str(nb_lgt_dispo.split('\n')[0]).split())})))
    logger.info("Chemin : %s", os.path.basename(filename))
    driver.get_screenshot_as_file(filename)
    time.sleep(2)
    logger.info("Fin du programme \n")


def clear_files(*folders):
    """Clear files."""
    for folder in folders:
        for ele in os.listdir(folder):
            try:
                os.remove(os.path.normpath(os.path.join(folder, ele)))
            except FileNotFoundError:
                pass


def send_direct_email():
    """Send an email if site not available."""
    # set up the driver
    driver = chrome_driver(EXECUTABLE_PATH)
    try:
        # go to website of concern
        driver.get(ALTAREA_URL)
        time.sleep(10)
        logger.info("Chargement de la page d'accueil : %s", driver.title)

        # open your session
        if not connect(driver, 3):         
            if driver.current_url == ERR_URL and len(os.listdir(IMG_TEMP)) == 0:
                send_mail(*TEMPLATE_DICT[2], IMG_TEMP_LIST)
                return True
        # if acces to website then relaunch grab function
        grab()

    except Exception as ex:
        logger.error("Un problème est survenu : %s", ex)
        return None

    finally:
        driver.quit()


def move_file(filename, dir=IMG_TEMP, dst_path=IMG_MAIL):
    """Move the file to a directory."""
    try:
        src_path = str(os.path.normpath(
                       os.path.join(dir, os.path.basename(filename))))
        move(src_path, dst_path)
    except FileNotFoundError as fnfe:
        logger.error("%s", fnfe)
    except Error as err:
        logger.error("%s", err)


def main():
    """Process the capture of pictures."""
    try:
        logger.info("Lancement du processus\n")

        # initialise folder
        logger.info("Nettoyage des répertoires")
        clear_files(IMG_TEMP, IMG_MAIL)

        nb_retries = 3  # number of attempts allowed after any failures
        while nb_retries > 0:
            logger.info("Nb retries allowed: %d", nb_retries)

            # launch grabbing
            state = grab()

            # condition to break while loop
            if state:
                break

            nb_retries -= 1

        else:
            if send_direct_email():
                logger.info('Notification envoyée')

    except FileNotFoundError as err:
        logger.error("Un problème est survenu : %s", err)

    finally:
        print("\n> Fin du processus")
        logger.info("Fin du processus")


if __name__ == '__main__':
    main()
