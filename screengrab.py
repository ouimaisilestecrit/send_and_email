"""Screengrab, grab pictures to send."""

import imghdr
import locale
import logging
import os
import smtplib
import sys
import tempfile
import time
import traceback
from collections import OrderedDict
from datetime import datetime as dt
from email.message import EmailMessage
from functools import reduce, wraps
from string import Template

from pdb import set_trace
from pprint import pprint

try:
    import pickle
    import schedule
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.remote.webelement import WebElement
    from selenium.webdriver.support import expected_conditions as EC
    from shutil import move, Error

except ModuleNotFoundError as e:
    print("Some Modules are missing: {}".format(e))

LOGGER = logging.getLogger(__name__)

# paths
DIRNAME = os.path.dirname(__file__)
BIN_DIR = os.path.normpath(os.path.join(DIRNAME, 'bin'))
CONF_DIR = os.path.normpath(os.path.join(DIRNAME, 'conf'))
RESOURCES_DIR = os.path.normpath(os.path.join(DIRNAME, 'resources'))

# filenames
CONFIG_FILENAME = "default_conf.inf"
PICKLE_FILENAME = "programs.pickle"
RECEIVERS_FILENAME = "users_info.inf"
MAIN_TEMPLATE_FILENAME = "template.html"
EXECUTION_TIME_FILENAME = "execution_time.inf"
NO_PICTURE_TEMPLATE_FILENAME = "template_no_picture.html"
NOT_AVAILABLE_TEMPLATE_FILENAME = "template_not_available.html"

# files
PICKLE_FILE = os.path.normpath(os.path.join(BIN_DIR, PICKLE_FILENAME))
CONFIG_FILE = os.path.normpath(os.path.join(CONF_DIR, CONFIG_FILENAME))
RECEIVERS_FILE = os.path.normpath(os.path.join(CONF_DIR, RECEIVERS_FILENAME))
EXECUTION_TIME_FILE = os.path.normpath(os.path.join(CONF_DIR, EXECUTION_TIME_FILENAME))
MAIN_TEMPLATE_FILE = os.path.normpath(
    os.path.join(RESOURCES_DIR, MAIN_TEMPLATE_FILENAME))
NO_PICTURE_TEMPLATE_FILE = os.path.normpath(
    os.path.join(RESOURCES_DIR, NO_PICTURE_TEMPLATE_FILENAME))
NOT_AVAILABLE_TEMPLATE_FILE = os.path.normpath(
    os.path.join(RESOURCES_DIR, NOT_AVAILABLE_TEMPLATE_FILENAME))

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
ALTAREA_URL = r"https://altarea-partenaires.com"
REGION_ILE_DE_FRANCE = r'Ile-de-France'
PROGRAMS_PER_PAGE = 12
ERR_URL = r"https://altarea-partenaires.com/wp-login.php"
ERR_MSG = r"Une erreur critique est survenue sur votre site"
HOME_URL = r"https://altarea-partenaires.com/accueil/"
IMG_FILE_EXTENSION = '.png'
MAX_FILE_SIZE = 157286400//15  # (157286400/15) / 1e6 = 10,48 Mo

# separators
MAIN_SEP = '='  # equal sign for main information
WORD_SEP = '_'  # underscore for word's separator
COMMA_SEP = ','  # comma sign
COLON_SEP = ':'  # colon sign
 
# template dictionary of file's message and subjects
TEMPLATE_DICT = OrderedDict([
    (0,
     [MAIN_TEMPLATE_FILE,
      [
          "un seul programme a bougé dans la corbeille d'Altarea Partenaires !",
          "venez découvrir ce qui a changé dans les deux programmes parmi les offres d'Altarea Partenaires !",
          "ça galope chez Altarea Partenaires ! Venez découvrir les {} mouvements parmi les offres !",
          "ça va déménager ! Venez découvrir les {} mouvements parmi les offres d'Altarea Partenaires !"]]),
    (1,
     [NO_PICTURE_TEMPLATE_FILE,
      r"pour le moment rien n'a bougé du côté des offres d'Altarea Partenaires !"]),
    (2,
     [NOT_AVAILABLE_TEMPLATE_FILE,
      r"Alerte ! Problème de connexion sur Altarea Partenaires !"])])


# days of week dictionary
DAYS_OF_WEEK_DICT = OrderedDict([
    ('dimanche', 'sunday'),
    ('lundi', 'monday'),
    ('mardi', 'tuesday'),
    ('mercredi', 'wednesday'),
    ('jeudi', 'thursday'),
    ('vendredi', 'friday'),
    ('samedi', 'saturday')])

LANG_DICT = OrderedDict([
    ('jour', 'day'),
    ('heure', 'hour')
])

# WEBDRIVER
EXECUTABLE_PATH = r"C:\Program Files (x86)\chromedriver.exe"

# create and configure logger."""
LOGGER.setLevel(logging.INFO)
log_path = os.path.normpath(os.path.join(DIRNAME, "log"))
formatter = logging.Formatter(
    '[%(asctime)s:%(module)s:%(lineno)s:%(levelname)s] %(message)s')
log_file = os.path.join(log_path, "{filenam}{log_ext}".format(
    **{'filenam': os.path.basename(sys.argv[0].split('.')[0]),
       'log_ext': '.log'}))
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
LOGGER.addHandler(file_handler)


def get_time(h=None, m='0'):
    """Return time."""
    ret = ''
    try:
        if isinstance(h, type(str())) and isinstance(m, type(str())):
            h = int(h)
            m = int(m)
            if (h >= 0 and h < 24) and (m >= 0 and m < 60):
                ret = '{0}:{1}'.format(
                    str(h).zfill(2),
                    str(m).zfill(2))
    except ValueError as ve:
        LOGGER.warning("Une valeur du temps d'exécution est ignorée car invalide : %s", ve)
    return ret 


def get_lang_val(lang=None):
    """Return lang name."""
    return LANG_DICT.get(lang, None)


def get_day(day=None):
    """Return book name from its ordinal number."""
    return DAYS_OF_WEEK_DICT.get(day, None)


def get_execution_time(filename):
    """Read execution time info.

    Function to read the execution time entries from a given file
    and return a lists of days and hours.
    """
    _dict = {}
    hours = []
    with open(filename, 'r', encoding='utf-8') as lines:
        for line in lines:
            line = line.strip()
            line = line.split(MAIN_SEP)
            _dict[get_lang_val(line[0])] = line[1].split(COMMA_SEP)
    days = [get_day(i) for i in _dict['day'] if get_day(i) != None]
    for i in _dict['hour']:
        val = get_time(*i.split(COLON_SEP))
        if val != '':
            hours.append(val)
    return days, hours


def scheduler():
    """
    schedule.every().monday.at("06:00").do(main)    
    """
    # days, hours = get_execution_time(EXECUTION_TIME_FILE)
    # for day in days:
        # for hour in hours:
            # set_trace()
            # sch = f"schedule.every().{day}.('{hour}').do(main)"
    exec("schedule.every().wednesday.at('02:47').do(main)")
    while True:
        schedule.run_pending()
        time.sleep(1)


def with_logging(func):
    """Generic logging to my scheduler."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("LOG: Running job %s" % func.__name__)
        result = func(*args, **kwargs)
        print("LOG: Job %s completed" % func.__name__)
        return result
    return wrapper


def grab(tmp, box):
    """Grab screenshots."""
    state = False
    # set up the driver
    driver = chrome_driver(EXECUTABLE_PATH)
    try:
        # go to website of concern
        driver.get(ALTAREA_URL)
        wait_loading(driver)
        level, message = get_status(driver)
        LOGGER.info("Niveau : %s", level)
        # check if there is a network issue
        if level == 'SEVERE':
            msg = ' '.join(message.rsplit(':', 1)[1].split()[:-1])
            LOGGER.info("%s", msg.capitalize())
            driver.quit()
            send_mail(*TEMPLATE_DICT[2], box)
            msg = "Alerte ! Problème de connexion sur Altarea Partenaires !"
            LOGGER.warning("%s", msg)
            print(msg)
            sys.exit(msg)
        LOGGER.info("Page d'accueil : %s", driver.title)

        # open your session
        if not connect(driver):
            msg = "Plusieurs causes peuvent occasionner cette interruption"
            LOGGER.warning("%s", msg)
            state = False
            return None

        # handle the modal element
        locator = r"//*[@id='first_sign-in_modal']/div/div/div[1]/button"
        handle_modal(driver, locator)

        # search by region of concern
        LOGGER.info("Lancement de la recherche par critères")
        select_idf_region(driver)

        # collect data
        programs_element = driver.find_element_by_id('results-prog')
        number_programs = int(programs_element.get_attribute('data-count'))
        get_program_data(driver, number_programs, tmp)
        num = len(os.listdir(tmp))  # nombre des photos sauvegardées
        if num == number_programs:
            LOGGER.info("Les %d photos sont sauvegardées", number_programs)
            state = True
        else:
            LOGGER.info("%d photos sur %d sauvegardées", num, number_programs)
            state = False

    except Exception:
        string = traceback.format_exc()
        LOGGER.error("Un problème est survenu : %s", string)
        state = False
        return None

    finally:
        driver.quit()

    return state


def chrome_driver(executable_path, t=10):
    """Return chrome driver."""
    LOGGER.info("Ouverture du navigateur automatisé : %s", executable_path)
    driver = webdriver.Chrome(executable_path)
    check_version(driver)
    driver.maximize_window()
    driver.implicitly_wait(int(t))
    return driver


def check_version(driver):
    """Check both Chrome browser and ChromeDriver version."""
    cap = driver.capabilities
    browser_n = cap['browserName']
    browser_v = cap['browserVersion']
    chrome_driver_v = cap[browser_n]['chromedriverVersion'].split()[0]
    if browser_v.split('.')[0] == chrome_driver_v.split('.')[0]:
        LOGGER.info("ChromeDriver est à jour")
    else:
        v_nav = "Version du navigateur"
        v_drv = "Version de ChromeDriver"
        err = "Interruption du processus, veuillez mettre à jour ChromeDriver"
        maj = "Veuillez consulter le fichier README.md pour la mise à jour"
        print("{} : {}".format(v_nav, browser_v))
        print("{} : {}".format(v_drv, chrome_driver_v))
        print(err)
        print(maj)
        LOGGER.error("%s : %s", v_nav, browser_v)
        LOGGER.error("%s : %s", v_drv, chrome_driver_v)
        LOGGER.error("%s", err)
        sys.exit(maj)


def wait_loading(drv):
    """Wait while new page is loading."""
    LOGGER.info("Attente de chargement de la page")
    wait_time = 0
    while drv.execute_script('return document.readyState;') != 'complete' \
            and wait_time < 10:
        # Scroll down to bottom to load contents, unnecessary for everyone
        drv.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        wait_time += 0.1
        time.sleep(0.1)
    LOGGER.info("Chargement de la page terminé")


def get_status(driver):
    """Get HTTP response."""
    level = ''
    message = ''
    resp = driver.get_log('browser')
    if resp:
        level = resp[0]['level']
        message = resp[0]['message']
        return level, message
    return level, message


def connect(driver, t=1):
    """Connect to a session."""
    try:
        login_modal = r"/html/body/header/div/div/div[2]/div/button"
        login_modal = get_by_xpath(driver, login_modal)
        if login_modal.get_attribute("data-target") == "#login-modal":
            login_modal.click()
            LOGGER.info("Lancement de l'authentification")

            if not sign_in(driver, t):
                return False

    except Exception:
        string = traceback.format_exc()
        LOGGER.error("Un problème est survenu : %s", string)
        return False
    else:
        return True


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


def sign_in(driver, t=1):
    """Fill in the login fields with your credentials."""
    try:
        LOGGER.info("time sleep: %d", t)
        LOGGER.info("Saisie de l'identifiant")
        time.sleep(int(t))
        get_by_id(driver, 'login-email').send_keys(LOGIN)
        LOGGER.info("Saisie du mot de passe")
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


def wait_signing_in(driver):
    """Wait while signing in."""
    try:
        i = 0
        LOGGER.info("En attente de chargement de la page...")
        while True:
            if driver.current_url == ERR_URL:
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


def select_idf_region(driver, region=REGION_ILE_DE_FRANCE):
    """Select the region."""
    region_dept_xpath = r"//*[@id='select2-departements-container']"
    LOGGER.info("Chargement des informations pour la région Ile-de-France")
    # go to region/department's combo box
    combo_box = driver.find_element_by_xpath(region_dept_xpath)
    combo_box.click()
    # set IDF region program in the combo-box
    results = driver.find_elements_by_xpath(
        "//*[@id='select2-departements-results']/li")
    for result in results:
        if result.text == region:
            result.click()
            time.sleep(1)
            break
    # validate the entry and  submit to the program
    selected = driver.find_element_by_xpath(region_dept_xpath)
    if selected.text == region:
        driver.find_element_by_xpath(
            "//*[@id='form-recherche']/div[4]/div/button[1]").click()
        time.sleep(3)


def get_program_data(driver, all_programs, folder):
    """Get program data."""
    LOGGER.info("Quantité des programmes immobiliers : %d\n", all_programs)
    pages = number_of_page(all_programs, PROGRAMS_PER_PAGE)

    # collect programs within a page
    for page in range(pages):
        programs = driver.find_elements_by_xpath("//*[@id='results-prog']/div")
        for i, a_program in enumerate(programs):
            LOGGER.info("Page %d sur %d", page+1, pages)
            fetch_main_data(driver, a_program, i+1, folder)
        LOGGER.info("Fin des programmes de la page : %d\n", page+1)

        # avoid to click next button on the last page
        if page != pages-1:
            LOGGER.info("Passage à la page %d sur %d", page+2, pages)
            driver.find_element_by_class_name('next').click()
            wait_next_page(driver, page+2)


def number_of_page(ele, per_page):
    """Return number of page."""
    num = ele // per_page
    mod = ele % per_page
    if mod != 0:
        return num + 1
    return num


def fetch_main_data(driver, program, index, folder):
    """Fetch main program data."""
    LOGGER.info("Programme %d", index)

    residence_name = get_text(program, r'font-regular')
    LOGGER.info("Résidence : %s", residence_name)

    commune_name = get_text(program, r'font-bold')
    LOGGER.info("Commune : %s", commune_name)

    nb_logement = get_text(program, r'highlight-keys')
    long_nb_logement = ' '.join(nb_logement.split('\n'))
    LOGGER.info("Nb logement dispo : %s", long_nb_logement)

    # move element to program to capture
    xpath_tmpl = r"//*[@id='results-prog']/div[{}]/div/div[2]"
    action = ActionChains(driver)
    ele = program.find_element_by_xpath(xpath_tmpl.format(index))
    action.move_to_element(ele).perform()
    time.sleep(2)

    # save screenshot with its appropiate filename
    filename = os.path.normpath(
        os.path.join(
            folder, "{name}{main}{city}{main}{size}.png".format(
                **{'name': WORD_SEP.join(residence_name.split()),
                   'main': MAIN_SEP,
                   'city': WORD_SEP.join(commune_name.split()),
                   'size': WORD_SEP.join(
                       str(nb_logement.split('\n')[0]).split())})))
    LOGGER.info("Nom du fichier : %s", os.path.basename(filename))
    driver.get_screenshot_as_file(filename)
    time.sleep(2)
    LOGGER.info("Fin du programme \n")


def get_text(driver, locator):
    """Return text if available."""
    try:
        return driver.find_element_by_class_name(locator).text
    except:
        return "Peut-être le dernier logement disponible"


def wait_next_page(driver, page, t=1):
    """Wait while next page is loading."""
    next_url = r"https://altarea-partenaires.com/recherche/page/{}/"
    LOGGER.info("Url : %s", next_url.format(page))
    while True:
        if driver.current_url == next_url.format(page):
            break
        time.sleep(int(t))


def save_config(folder):
    """Save configuration file."""
    LOGGER.info("Sauvegarde de la configuration")
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        for item in os.listdir(folder):
            f.write('{}\n'.format(item))


def dispatch(tmp, box):
    """Diagnose programs."""
    len_tmp = len(os.listdir(tmp))
    if not os.path.exists(PICKLE_FILE):
        # create a pickle file
        previous_set = read_config()
        dump_to_pickle(PICKLE_FILE, previous_set)

    # load programs from pickle file saved
    former = load_from_pickle(PICKLE_FILE)
    stream = get_streams(tmp)

    # comparison
    program = find_program(former, stream)
    if isinstance(program, type(None)):
        LOGGER.info("Pas d'envoi de courriel")
        # LOGGER.info("Aucun changement, envoi du courriel approprié")
        # send_mail(*TEMPLATE_DICT[1], box, len_tmp)

        # sync with the last update
        older = former - stream
        if older:
            LOGGER.info("Synchronisation avec la dernière mise à jour")
            dump_to_pickle(PICKLE_FILE, stream)
    else:
        LOGGER.info("Analyse de(s) programme(s) mis à jour")
        # step 1 - updated program
        updated = stream - former
        LOGGER.info("« %d » programme(s) mis à jour", len(updated))

        # step 2 - sync with the last update
        LOGGER.info("Synchronisation avec la dernière mise à jour")
        dump_to_pickle(PICKLE_FILE, stream)

        # step 3 - moving updated program from temp to mail directory
        LOGGER.info("Envoi de(s) programme(s) vers le répertoire mail")
        for an_update in updated:
            move_file(an_update, tmp, box)

        # step 4 - send email
        if box:
            LOGGER.info("Envoi de mail")
            len_mail = len(os.listdir(box))
            send_mail(*TEMPLATE_DICT[0], box, len_tmp, len_mail)
            LOGGER.info("Mail envoyé")
        else:
            LOGGER.info("Pas d'envoi de courriel")
            # LOGGER.info("Aucun changement, envoi du courriel approprié")
            # send_mail(*TEMPLATE_DICT[1], box, len_tmp)
    return True


def read_config():
    """Read configuration file."""
    ret = set()
    with open(CONFIG_FILE, 'r', encoding='utf-8') as lines:
        for line in lines:
            line = line.strip()
            ret.add(line)
    return ret


def dump_to_pickle(filename, content):
    """Dump to pickle file."""
    with open(filename, "wb") as pickle_f:
        return pickle.dump(content, pickle_f)


def load_from_pickle(filename):
    """Load from pickle file."""
    with open(filename, "rb") as pickle_f:
        return pickle.load(pickle_f)


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
        LOGGER.warning("Il n'y a aucun changement")
        return None
    else:
        LOGGER.info("Il y a « %d » changement(s)", len(val))
        return val


def send_mail(filename, sub, folder, length=None, size=None):
    """Send email with attachments."""
    # read receivers
    # receivers = 'mike.kabika@gmail.com, expertduneuf@hotmail.com'
    receivers = ', '.join(get_emails(RECEIVERS_FILE))
    LOGGER.info("Destinataires : %s", receivers)
    # read template
    a_template = read_template(filename)
    if isinstance(length, type(int())):
        a_template = Template(a_template.safe_substitute(TOTAL=str(length)))

    # set timecode on email's subject
    locale.setlocale(locale.LC_TIME, "fr_FR")
    subject = "{at} : {sub}".format(
        **{'at': dt.today().strftime('%A %d %b %y, %Hh%M').capitalize(),
           'sub': sub if size is None else switch_subject(size, sub)})

    # Create the container email message.
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = MAIL_LOGIN
    msg['To'] = receivers
    msg.preamble = 'You will not see this in a MIME-aware mail reader.\n'

    # detect kind of message to process allowing to size
    if not isinstance(size, type(None)):
        LOGGER.info("Traitement de message avec %d pièce(s) jointe(s)", size)
        path_ = os.path.abspath(folder)
        files = os.listdir(folder)

        # determine files' size
        current_size = get_list_size([os.path.join(path_, i) for i in files])
        LOGGER.info("Taille de fichier(s) d'envoi(s) : %s",
                    "{0:.2f} Mo".format(round(current_size/1000000, 2)))
        if current_size > MAX_FILE_SIZE:
            lots = share_by_lots(folder)
            LOGGER.info("Traitement de message par %d envois", len(lots))
            for i, a_lot in enumerate(lots):
                flag = add_flag(i+1, len(lots))
                msg.replace_header('Subject', "{} - {}".format(subject, flag))
                message_with_attachments(msg, path_, a_lot, a_template, flag)

                # refresh because we cannot add attachment on
                # multipart content-type or on non-empty payload
                msg.replace_header('Content-Type', 'text/plain')
                msg.set_payload(None)
        else:
            message_with_attachments(msg, path_, files, a_template)
    else:
        LOGGER.info("Traitement de message sans pièce jointe")
        message_without_attachment(msg, a_template)


def read_template(filename):
    """Read template.

    Function to read the template from a given template file
    and return it.
    """
    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)


def switch_subject(size, sub):
    """Return the appropiate subject's message."""
    if size == 1:
        return sub[0].format(size)
    if size == 2:
        return sub[1].format(size)
    if 2 < size <= 5:
        return sub[2].format(size)
    if size > 5:
        return sub[3].format(size)
    return "NaN"


def get_emails(filename):
    """Read emails adresses.

    Function to read the contacts from a given contact file
    and return a list of email adresses.
    """
    emails = set()
    with open(filename, 'r', encoding='utf-8') as emails_file:
        for an_email in emails_file:
            an_email = an_email.strip()
            an_email = an_email.split(MAIN_SEP)[1]
            emails.add(an_email)
    return emails


def get_list_size(lst):
    """Return the size of files in bytes."""
    list_of_length = [os.path.getsize(i) for i in lst]
    ret = reduce(lambda x, y: x + y, list_of_length)
    return ret


def share_by_lots(folder):
    """Share by lots."""
    ret = []
    tab = []
    path = os.path.abspath(folder)
    for item in os.listdir(folder):
        tab.append(item)
        length = get_list_size([os.path.join(path, i) for i in tab])
        while check_size_limit(length, MAX_FILE_SIZE):
            ret.append(tab[:-1])
            last = tab[-1]
            tab = []
            tab.append(last)
            break
    ret.append(tab)
    return ret


def check_size_limit(val1, val2, limit=100):
    """Compare result to the limit."""
    rate = round((val1/val2)*100)
    if rate < limit:
        return False
    return True


def add_flag(index, length):
    """Add current flag."""
    return "Envoi : {index} sur {length}".format(
        **{'index': index, 'length': length})


def message_with_attachments(msg, path_, files, a_template, lots=str()):
    """Prepare message with an attachment."""
    # feed the email with programs's main information
    html_table = stringify_main_info(files)

    # feature to add in plain text message in the body
    # msg.set_content(message)

    html_message = a_template.substitute(
        LOTS=lots,
        MAIN_INFO=html_table.title())
    msg.add_alternative(html_message, subtype='html')
    # attach files to message
    msg = add_attach(msg, [os.path.join(path_, i) for i in files])
    send(msg)


def stringify_main_info(lst):
    """Convert list of a program's main information as a string."""
    tab_html = []
    tab_div = '<div style="margin:0;padding:0;color:#5a6883;line-height:20px;text-align:left;">{}</div>'
    data = """\
    <div>
        <legend>
            {0} <strong><span style="color:#333;">{1}</span></strong>
        </legend>
        <img src="cid:{2}" style="width:100%;">
    </div>"""
    for i, item_filename in enumerate(sorted(lst)):
        f_name = rename(os.path.basename(item_filename))
        item = item_filename.split(IMG_FILE_EXTENSION)[0]
        item = [' '.join(i.split(WORD_SEP)) for i in item.split(MAIN_SEP)]
        tab_html.append(data.format(
            '<strong>{0}.</strong> {1} - {2} : '.format(
                str(i+1).rjust(2), item[0], item[1]), item[2], f_name))
    html_str = ''.join(['{}\n\n'.format(i) for i in tab_html])
    html_str = tab_div.format(html_str)
    return html_str


def rename(string):
    """Rename."""
    string = ' '.join(string.split(MAIN_SEP))
    string = ' '.join(string.split(WORD_SEP))
    return string


def add_attach(msg, filenames, main_type='image'):
    """Attach files in binary mode."""
    LOGGER.info("Ajout de « %d fichier(s) »", len(filenames))
    for filename in filenames:
        with open(filename, 'rb') as f:
            f_data = f.read()
            f_type = imghdr.what(f.name)
            f_name = rename(os.path.basename(f.name))
            msg.add_header('Content-ID', '{}'.format(f_name))
        msg.add_attachment(
            f_data,
            maintype=main_type,
            subtype=f_type,
            filename=f_name)
    return msg


def send(msg):
    """Send the email via our own SMTP server."""
    # Terminate the SMTP session and close the connection
    with smtplib.SMTP(host=MAILBOX_HOST, port=MAILBOX_PORT) as s:
        # enable security
        s.starttls()
        # login with email credential
        s.login(MAIL_LOGIN, MAIL_PASSW)
        s.send_message(msg)
    del msg


def message_without_attachment(msg, a_template):
    """Prepare message without any attachment."""
    # add in the email message
    html_message = a_template.safe_substitute()
    msg.add_alternative(html_message, subtype='html')
    # send the email
    send(msg)


def move_file(item, dirpath, dst_path):
    """Move the file to a directory."""
    try:
        src_path = str(
            os.path.normpath(os.path.join(dirpath,
                                          os.path.basename(item))))
        move(src_path, dst_path)
    except FileNotFoundError as fnfe:
        LOGGER.error("Le fichier n'existe pas ou a été déplacé : %s", fnfe)
    except Error as err:
        LOGGER.error("Ce titre existe déjà : %s", err)


def send_direct_email(tmp, box):
    """Send an email if site not available."""
    state = False
    # set up the driver
    driver = chrome_driver(EXECUTABLE_PATH)
    try:
        # go to website of concern
        driver.get(ALTAREA_URL)
        wait_loading(driver)
        LOGGER.info("Chargement de la page d'accueil : %s", driver.title)

        # open your session
        if not connect(driver, 3):
            if driver.current_url == ERR_URL:
                driver.quit()
                send_mail(*TEMPLATE_DICT[2], box)
                state = True
            else:
                # if acces to website then relaunch grab function
                grabbed = grab(tmp, box)
                if grabbed:
                    dispatch(tmp, box)
        else:
            LOGGER.info("La cause du problème n'est pas l'accès au site")

    except Exception:
        string = traceback.format_exc()
        LOGGER.error("Un problème est survenu : %s", string)
        return None

    finally:
        driver.quit()

    return state


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


def check_size():
    """Return the size limit of an email message."""
    smtp = smtplib.SMTP(MAILBOX_HOST)
    smtp.ehlo()
    max_limit_in_bytes = int(smtp.esmtp_features['size'])
    return max_limit_in_bytes


@with_logging
def main():
    """Process the capture of pictures."""
    start = time.time()
    # init_logger()
    try:
        LOGGER.info("Lancement du processus")
        # create temporary directory
        box_dir = tempfile.TemporaryDirectory(dir=RESOURCES_DIR)
        box = box_dir.name
        tmp_dir = tempfile.TemporaryDirectory(dir=RESOURCES_DIR)
        tmp = tmp_dir.name

        nb_retries = 4  # number of attempts allowed after any failures
        while nb_retries > 0:
            LOGGER.info("Nb retries allowed: %d", nb_retries)
            # launch grab & dispatch
            # condition to break while loop
            grabbed = grab(tmp, box)
            if grabbed:
                save_config(tmp)
                dispatched = dispatch(tmp, box)
                if dispatched:
                    break

            nb_retries -= 1

        else:
            # bad credential
            if send_direct_email(tmp, box):
                LOGGER.info("La notification d'échec de connexion est envoyée")

    except FileNotFoundError as err:
        LOGGER.error("Un problème est survenu : %s", err)

    except SystemExit as se:
        LOGGER.error("Un arrêt est demandé : %s", se)

    finally:
        print("\n> Fin du processus")
        LOGGER.info("Fin du processus")
        duration = elapsed_time(time.time() - start)
        LOGGER.info("Total time: %s\n", duration)
        print("\n>>> Total time:", duration)


if __name__ == '__main__':
    scheduler()
    # schedule.every(2).minutes.do(main)
    # # monday schedule
    # schedule.every().monday.at("06:00").do(main)
    # schedule.every().monday.at("10:00").do(main)
    # schedule.every().monday.at("14:00").do(main)
    # schedule.every().monday.at("20:00").do(main)

    # # tuesday schedule
    # schedule.every().tuesday.at("06:00").do(main)
    # schedule.every().tuesday.at("10:00").do(main)
    # schedule.every().tuesday.at("14:00").do(main)
    # schedule.every().tuesday.at("20:00").do(main)

    # # wednesday schedule
    # schedule.every().wednesday.at("06:00").do(main)
    # schedule.every().wednesday.at("10:00").do(main)
    # schedule.every().wednesday.at("14:00").do(main)
    # schedule.every().wednesday.at("20:00").do(main)

    # # thursday schedule
    # schedule.every().thursday.at("06:00").do(main)
    # schedule.every().thursday.at("10:00").do(main)
    # schedule.every().thursday.at("14:00").do(main)
    # schedule.every().thursday.at("20:00").do(main)

    # # friday schedule
    # schedule.every().friday.at("06:00").do(main)
    # schedule.every().friday.at("10:00").do(main)
    # schedule.every().friday.at("14:00").do(main)
    # schedule.every().friday.at("20:00").do(main)

    # # saturday schedule
    # schedule.every().saturday.at("06:00").do(main)
    # schedule.every().saturday.at("10:00").do(main)
    # schedule.every().saturday.at("14:00").do(main)
    # schedule.every().saturday.at("20:00").do(main)

    # while True:
        # schedule.run_pending()
        # time.sleep(1)
