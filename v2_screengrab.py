"""Screengrab, capture, grab pictures but send."""

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
from functools import reduce

from pprint import pprint
from pdb import set_trace


try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.remote.webelement import WebElement
    from selenium.webdriver.support import expected_conditions as EC

    from shutil import move, Error

except ModuleNotFoundError as e:
    print("Some Modules are missing: {}".format(e))

DIRNAME = os.path.dirname(__file__)
BIN_DIR = os.path.normpath(os.path.join(DIRNAME, 'bin'))
RESOURCES_DIR = os.path.normpath(os.path.join(DIRNAME, 'resources'))
CONF_DIR = os.path.normpath(os.path.join(DIRNAME, 'conf'))
TEMPLATES_DIR = os.path.normpath(os.path.join(RESOURCES_DIR, 'templates'))
IMAGES_DIR = os.path.normpath(os.path.join(RESOURCES_DIR, 'images'))
MAIL_DIR = os.path.normpath(os.path.join(IMAGES_DIR, 'mail'))
TEMP_DIR = os.path.normpath(os.path.join(IMAGES_DIR, 'temp'))
# filenames
RESOURCES_FILENAME = 'resources.inf'
PICKLE_FILENAME = "programs.pickle"
RECEIVERS_FILENAME = 'destinataires1.txt'
MAIN_TEMPLATE_FILENAME = 'template.txt'
NO_PICTURE_TEMPLATE_FILENAME = 'template_no_picture.txt'
NOT_AVAILABLE_TEMPLATE_FILENAME = 'template_not_available.txt'
# files
PICKLE_FILE = os.path.normpath(os.path.join(BIN_DIR, PICKLE_FILENAME))
RESOURCES_FILE = os.path.normpath(os.path.join(BIN_DIR, RESOURCES_FILENAME))
RECEIVERS_FILE = os.path.normpath(os.path.join(CONF_DIR, RECEIVERS_FILENAME))
MAIN_TEMPLATE_FILE = os.path.normpath(
    os.path.join(TEMPLATES_DIR, MAIN_TEMPLATE_FILENAME))
NO_PICTURE_TEMPLATE_FILE = os.path.normpath(
    os.path.join(TEMPLATES_DIR, NO_PICTURE_TEMPLATE_FILENAME))
NOT_AVAILABLE_TEMPLATE_FILE = os.path.normpath(
    os.path.join(TEMPLATES_DIR, NOT_AVAILABLE_TEMPLATE_FILENAME))

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
PROGRAMS_PER_PAGE = 12
ERR_URL = r"https://altarea-partenaires.com/wp-login.php"
ERR_MSG = r"Une erreur critique est survenue sur votre site"
HOME_URL = r"https://altarea-partenaires.com/accueil/"
IMG_FILE_EXTENSION = '.png'
MAX_FILE_SIZE = 1965052
# MAX_FILE_SIZE = 157286400
# separators
MAIN_SEP = '='  #  equal sign for main information
WORD_SEP = '_'  #  underscore for word's separator

# template dictionary of file's message and subjects
TEMPLATE_DICT = OrderedDict([
    (0,
     [MAIN_TEMPLATE_FILE,
      [
          "un seul programme a bougé dans la corbeille d'Altarea Partenaires !",
          "venez découvrir ce qui a changé dans les deux programmes parmi les offres d'Altarea Partenaires !",
          "ça galope du côté d'Altarea Partenaires ! Venez découvrir les {} mouvements parmi les offres !",
          "ça va déménager ! Venez découvrir les {} mouvements parmi les offres d'Altarea Partenaires !"]]),
    (1,
     [NO_PICTURE_TEMPLATE_FILE,
      r"pour le moment rien n'a bougé du côté des offres d'Altarea Partenaires !"]),
    (2,
     [NOT_AVAILABLE_TEMPLATE_FILE,
      r"Alerte ! Problème de connexion sur Altarea Partenaires !"])])

# WEBDRIVER
EXECUTABLE_PATH = r"C:\Program Files (x86)\chromedriver.exe"

# LOGGING
LOG_PATH = os.path.normpath(os.path.join(DIRNAME, "log"))
LOG_FORMAT = "[%(asctime)s - %(name)s] - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
LOG_EXT = ".log"
LOG_FILE = os.path.join(
    LOG_PATH, "{script}_ALTAREA{ext}".format(
        **{'script': os.path.basename(sys.argv[0].split('.')[0]),
           'ext': LOG_EXT}))
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format=LOG_FORMAT)
logger = logging.getLogger()


def sub_format(size, sub):
    """Return the appropiate subject's message."""
    if size == 1:
        return sub[0].format(size)
    if size == 2:
        return sub[1].format(size)
    if 2 < size <= 5:
        return sub[2].format(size)
    if size > 5:
        return sub[3].format(size)
    return "Au-dessus c'est le soleil..."


def elapsed_time(duration):
    """Return the human readable elapsed time."""
    duration = int(duration)
    minutes, seconds = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)

    hours = str(hours).zfill(2)
    minutes = str(minutes).zfill(2)
    seconds = str(seconds).zfill(2)

    if hours != "00":
        ret = "{}:{}:{}".format(hours, minutes, seconds)
    else:
        ret = "{}:{}".format(minutes, seconds)

    return ret


def get_contacts(filename):
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


def stringify_main_info(lst):
    """Convert list of a program's main information as a string."""
    tab = []
    for i, item_filename in enumerate(sorted(lst)):
        item = item_filename.split(IMG_FILE_EXTENSION)[0]
        item = [' '.join(i.split(WORD_SEP)) for i in item.split(MAIN_SEP)]
        tab.append('{line}. {name} - {city} : {size}'.format(
            **{'line': str(i+1).rjust(2),
               'name': item[0],
               'city': item[1],
               'size': item[2]}))
    return ''.join(['{}\n\n'.format(i) for i in tab])


def check_size():
    """Return the size limit of an email message."""
    smtp = smtplib.SMTP(MAILBOX_HOST)    
    smtp.ehlo()    
    max_limit_in_bytes = int( smtp.esmtp_features['size'] )
    return max_limit_in_bytes


def get_list_size(lst):
    """Return the size of files in a folder."""
    list_of_length = [os.path.getsize(i) for i in lst]
    ret = reduce(lambda x, y: x + y, list_of_length)
    return ret


def share_by_size():
    """Share by email's limit size."""
    ret = []
    tab = []
    path = os.path.abspath(MAIL_DIR)
    for item in os.listdir(MAIL_DIR):
        tab.append(item)
        length = get_list_size([os.path.join(path, i) for i in tab])
        while length > MAX_FILE_SIZE:  # 157 286 400 bytes
            ret.append(tab)
            tab = []
            break
    ret.append(tab)
    return ret


def send_mail(filename, sub, size=None, folder=MAIL_DIR):
    """Send email with attachments."""
    path = os.path.abspath(folder)
    list_of_files = [os.path.join(path, i) for i in os.listdir(folder)]
    
    set_trace()
    
    mail_folder = os.listdir(folder)
    if get_list_size(list_of_files) > MAX_FILE_SIZE:
        mail_folder = share_by_size()
    # read contacts
    names, emails = get_contacts(RECEIVERS_FILE)

    # feed the email with programs's main information when size is available
    a_template = read_template(filename)
    if size is not None:
        items = [os.path.basename(i) for i in os.listdir(folder)]
        string = stringify_main_info(items)
        set_trace()
        a_template = Template(a_template.safe_substitute(MAIN_INFO=string))

    # set timecode on email's subject
    locale.setlocale(locale.LC_TIME, "fr_FR")
    subject = "{at} : {sub}".format(
        **{'at': dt.today().strftime('%A %d %b %y, %Hh%M').capitalize(),
           'sub': sub if size is None else sub_format(size, sub)})

    # for each contact, send the email:
    for name, email in zip(names, emails):
        # add in the actual person name to template
        message = a_template.substitute(PERSON_NAME=name.title())

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
        if size is not None:
            logger.info("Envoi de « %d fichier(s) »", size)
            for file_ in mail_folder:
                file_ = os.path.normpath(os.path.join(folder, file_))
                with open(file_, 'rb') as fp:
                    # logger.info("Fichier : %s", file_)
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
            # ack = s.set_debuglevel(2)
            logger.info("sent=========")
            # set_trace()
            # logger.info("s.set_debuglevel(2): %s", s.set_debuglevel(2))

        del msg


def grab():
    """Grab screenshots."""
    state = False
    # set up the driver
    driver = chrome_driver(EXECUTABLE_PATH)
    try:
        # go to website of concern
        driver.get(ALTAREA_URL)
        time.sleep(6)
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
        select_idf_region(driver)

        # collect data
        programs_element = driver.find_element_by_id('results-prog')
        number_programs = int(programs_element.get_attribute('data-count'))
        get_program_data(driver, number_programs)
        num = len(os.listdir(TEMP_DIR))  # nombre des photos sauvegardées
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
        login_modal = r"/html/body/header/div/div/div[2]/div/button"
        login_modal = get_by_xpath(driver, login_modal)
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
        button = r"//*[@id='dashboardContent']/form/div[2]/div/button"
        get_by_xpath(driver, button).click()

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


def select_idf_region(driver):
    """Select the region."""
    logger.info("Chargement des informations pour la région Ile-de-France")
    # go to region/department's combo box
    combo_box = driver.find_element_by_xpath(
        "//*[@id='select2-departements-container']")
    combo_box.click()
    time.sleep(1)
    # select IDF region in the combo-box
    combo_box.find_element_by_xpath(
        "//*[@id='select2-departements-results']/li[13]").click()
    time.sleep(1)
    # submit the program
    driver.find_element_by_xpath(
        "//*[@id='form-recherche']/div[4]/div/button[1]").click()
    time.sleep(3)


def get_program_data(driver, all_programs):
    """Get program data."""
    logger.info("Quantité des programmes immobiliers : %d\n", all_programs)
    pages = number_of_page(all_programs, PROGRAMS_PER_PAGE)

    # collect programs within a page
    for page in range(pages):
        programs = driver.find_elements_by_xpath("//*[@id='results-prog']/div")
        for i, a_program in enumerate(programs):
            fetch_main_data(driver, a_program, i+1, page+1, pages)
        logger.info("Fin des programmes de la page : %d\n", page+1)

        # avoid to click next button on the last page
        if page != pages-1:
            logger.info("Aller à la page suivante")
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
        return "Peut-être le dernier logement disponible"


def number_of_page(ele, per_page):
    """Return number of page."""
    num = ele // per_page
    mod = ele % per_page
    if mod != 0:
        return num + 1
    return num


def fetch_main_data(driver, program, index, page, pages):
    """Fetch main program data."""
    logger.info("Page %d sur %d", page, pages)
    logger.info("Programme %d", index)

    # residence
    residence_name = get_text(program, r'font-regular')
    logger.info("Résidence : %s", residence_name)

    # city
    commune_name = get_text(program, r'font-bold')
    logger.info("Commune : %s", commune_name)

    # available home
    nb_logement = get_text(program, r'highlight-keys')
    long_nb_logement = ' '.join(nb_logement.split('\n'))
    logger.info("Nb logement dispo : %s", long_nb_logement)

    # move element to program to capture
    xpath_tmpl = r"//*[@id='results-prog']/div[{}]/div/div[2]"
    action = ActionChains(driver)
    ele = program.find_element_by_xpath(xpath_tmpl.format(index))
    action.move_to_element(ele).perform()
    time.sleep(2)

    # save screenshot with its appropiate filename
    filename = os.path.normpath(
        os.path.join(
            TEMP_DIR, "{name}{main}{city}{main}{size}.png".format(
                **{'name': WORD_SEP.join(residence_name.split()),
                   'main': MAIN_SEP,
                   'city': WORD_SEP.join(commune_name.split()),
                   'size': WORD_SEP.join(
                       str(nb_logement.split('\n')[0]).split())})))
    logger.info("Nom du fichier : %s", os.path.basename(filename))
    driver.get_screenshot_as_file(filename)
    time.sleep(2)
    logger.info("Fin du programme \n")


def clear_files(folder=MAIL_DIR):
    """Clear files."""
    for ele in os.listdir(folder):
        try:
            os.remove(os.path.normpath(os.path.join(folder, ele)))
        except FileNotFoundError:
            pass


def send_direct_email():
    """Send an email if site not available."""
    state = False
    # set up the driver
    driver = chrome_driver(EXECUTABLE_PATH)
    try:
        # go to website of concern
        driver.get(ALTAREA_URL)
        time.sleep(10)
        logger.info("Chargement de la page d'accueil : %s", driver.title)

        # open your session
        if not connect(driver, 3):
            if driver.current_url == ERR_URL:
                driver.quit()
                send_mail(*TEMPLATE_DICT[2])
                state = True
            else:
                # if acces to website then relaunch grab function
                grabbed = grab()
                if grabbed:
                    dispatch()

    except Exception as ex:
        logger.error("Un problème est survenu : %s", ex)
        return None

    finally:
        driver.quit()

    return state


def move_file(filename, dirpath=TEMP_DIR, dst_path=MAIL_DIR):
    """Move the file to a directory."""
    try:
        src_path = str(
            os.path.normpath(os.path.join(dirpath,
                                          os.path.basename(filename))))
        move(src_path, dst_path)
    except FileNotFoundError as fnfe:
        logger.error("Le fichier n'existe pas ou a été déplacé : %s", fnfe)
    except Error as err:
        logger.error("Ce titre existe déjà : %s", err)


def dump_to_pickle(filename, content):
    """Dump to pickle file."""
    with open(filename, "wb") as pickle_f:
        return pickle.dump(content, pickle_f)


def load_from_pickle(filename):
    """Load from pickle file."""
    with open(filename, "rb") as pickle_f:
        return pickle.load(pickle_f)


def read_fileconfig():
    """Read configuration file."""
    ret = set()
    with open(RESOURCES_FILE, 'r', encoding='utf-8') as lines:
        for line in lines:
            line = line.strip()
            ret.add(line)
    return ret


def save_fileconfig():
    """Save configuration file."""
    with open(RESOURCES_FILE, 'w', encoding='utf-8') as f:
        for item in os.listdir(TEMP_DIR):
            f.write('{}\n'.format(item))


def get_streams(folder):
    """Load program filenames."""
    files = set()
    items = os.listdir(folder)
    for an_item in sorted(items):
        files.add(an_item)
    return files


def find_program(former, stream):
    """Find programs."""
    try:
        val = stream - former
        assert len(val) != 0
    except AssertionError:
        logger.warning("Il n'y a aucun changement")
        return None
    else:
        logger.info("Il y a « %d » changement(s)", len(val))
        return val


def dispatch():
    """Diagnose programs."""
    if not os.path.exists(PICKLE_FILE):
        # create a pickle file
        previous_set = read_fileconfig()
        dump_to_pickle(PICKLE_FILE, previous_set)

    # load programs from pickle file saved
    former = load_from_pickle(PICKLE_FILE)
    stream = get_streams(TEMP_DIR)

    # comparison
    program = find_program(former, stream)
    if program is None:
        logger.info("Aucun changement, envoi du courriel approprié")
        clear_files()
        send_mail(*TEMPLATE_DICT[1])

        # sync with the last update
        older = former - stream
        if older:
            logger.info("Synchronisation avec la dernière mise à jour")
            dump_to_pickle(PICKLE_FILE, stream)
    else:
        logger.info("Analyse de(s) programme(s) mis à jour")
        # step 1 - updated program
        updated = stream - former
        logger.info("« %d » programme(s) mis à jour", len(updated))

        # step 2 - sync with the last update
        logger.info("Synchronisation avec la dernière mise à jour")
        dump_to_pickle(PICKLE_FILE, stream)

        # step 3 - Deleting files from the mail directory
        logger.info("Suppression des fichiers du répertoire mail")
        clear_files()

        # step 4 - moving updated program from temp to mail directory
        logger.info("Envoi de(s) programme(s) vers le répertoire mail")
        for an_update in updated:
            move_file(an_update)

        # step 5 - send email
        if MAIL_DIR:
            logger.info("Envoi de mail")
            len_img_mail = len(os.listdir(MAIL_DIR))
            send_mail(*TEMPLATE_DICT[0], len_img_mail)
            logger.info("Mail envoyé")
        else:
            logger.info("Aucun changement, envoi du courriel approprié")
            send_mail(*TEMPLATE_DICT[1])
    return True


def main():
    """Process the capture of pictures."""
    try:
        start = time.time()
        logger.info("Lancement du processus")

        # initialise folder
        logger.info("Suppression des fichiers du répertoire : %s",
                    os.path.basename(TEMP_DIR))
        clear_files(TEMP_DIR)

        nb_retries = 3  # number of attempts allowed after any failures
        while nb_retries > 0:
            logger.info("Nb retries allowed: %d", nb_retries)
            # launch grab & dispatch
            # condition to break while loop
            grabbed = grab()
            if grabbed:
                save_fileconfig()
                dispatched = dispatch()
                if dispatched:
                    break

            nb_retries -= 1

        else:
            # bad network or bad credential
            if send_direct_email():
                logger.info('Notification envoyée')

    except FileNotFoundError as err:
        logger.error("Un problème est survenu : %s", err)

    finally:
        print("\n> Fin du processus")
        logger.info("Fin du processus")
        duration = elapsed_time(time.time() - start)
        logger.info("Total time: %s\n", duration)
        print("\n>>> Total time:", duration)


if __name__ == '__main__':
    send_mail(*TEMPLATE_DICT[0], 45)
    # share_by_size()
    # main()
