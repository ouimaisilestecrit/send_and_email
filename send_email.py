"""Send an email."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from os import environ
from string import Template

import pdb

# altarea credential
ALTA_LOGIN = environ['ALTAREA_LOGIN']
ALTA_PASSW = environ['ALTAREA_PASSWORD']
# email credential
MAIL_LOGIN = environ['EDN_LOGIN']
MAIL_PASSW = environ['EDN_PASSWORD']

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
    """Read template

    Function to read the template from a given template file
    and return it.
    """
    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)


def open_smtp_session():
    """Create SMTPsession."""
    # use hotmail with port
    s = smtplib.SMTP(host='smtp.office365.com', port=587)
    
    # enable security
    s.starttls()
    
    # login with email credential
    s.login(MAIL_LOGIN, MAIL_PASSW)
    return s


def main():

    # read contacts
    names, emails = get_contacts('contact.txt')
    message_template = read_template('message.txt')

    # for each contact, send the email:
    for name, email in zip(names, emails):
        msg = MIMEMultipart()  # create a message

        # add in the actual person name to the message template
        message = message_template.substitute(PERSON_NAME=name.title())

        # set up the parameters of the message (MIME)
        msg['From']=MAIL_LOGIN
        msg['To']=email
        msg['Subject']="Envoi de mail avec fichier"

        # add in the message body
        msg.attach(MIMEText(message, 'plain'))
        
        # add file to attach
        attach_filename = "vignette1.jpeg"
        
        # open the file as binary mode
        attach_file = open(attach_filename, 'rb')
        
        # set up the payload
        payload = MIMEBase('application', 'octate-stream')
        payload.set_payload((attach_file).read())
        
        # encode the attachment
        encoders.encode_base64(payload)
        
        # add payload header with filename
        payload.add_header('Content-Decomposition',
                           'attachment', filename=attach_filename)
        msg.attach(payload)
        
        # send the message via the server set up earlier
        s = open_smtp_session()
        # s.sendmail(msg)
        s.send_message(msg)

        del msg

    # Terminate the SMTP session and close the connection
    s.quit()
    print('Mail Sent')

# driver.get_screenshot_as_file('shot.png')
if __name__ == '__main__':
    main()
