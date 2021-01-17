"""Send images by email."""

import imghdr
import locale
import os
import smtplib

from datetime import datetime
from email.message import EmailMessage
from string import Template

# email credentials
MAIL_LOGIN = os.environ['EDN_LOGIN']
MAIL_PASSW = os.environ['EDN_PASSWORD']

# email gateway parameters
MAILBOX_HOST = 'smtp.office365.com'
MAILBOX_PORT = 587

# image's path
DIRNAME = os.path.dirname(__file__)
IMG_MAIL = os.path.normpath(os.path.join(DIRNAME, 'images/mail'))
IMG_LIST = os.listdir(IMG_MAIL)


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


def main():
    """Send email with attachments."""
    # read contacts
    names, emails = get_users('users.txt')

	# set timecode on email's subject
	locale.setlocale(locale.LC_TIME, "fr_FR")
	subject = "{at} : {pic} ventes d'Altarea Partenaires !".format(
		**{
			'at': datetime.today().strftime('%A %d %b %y, %Hh%M').capitalize(),
			'pic': "des nouvelles de" if IMG_LIST else "aucune nouveauté sur les"
		})

    # for each contact, send the email:
    for name, email in zip(names, emails):
        # add in the actual person name to a message template
        if IMG_LIST:
            # message content template
            msg_template = read_template('template.txt')
            message = msg_template.substitute(PERSON_NAME=name.title())
        else:
            # message template for no picture
            msg_template = read_template('template_no_picture.txt')
            message = msg_template.substitute(PERSON_NAME=name.title())

        # Create the container email message.
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = MAIL_LOGIN
        msg['To'] = email
        msg.preamble = 'You will not see this in a MIME-aware mail reader.\n'

        # add in the message body
        msg.set_content(message)

        # Open the files in binary mode.  Use imghdr to figure out the
        # MIME subtype for each specific image.
        if IMG_LIST:
            for file_ in IMG_LIST:
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
    print('Mail Sent')


if __name__ == '__main__':
    main()
