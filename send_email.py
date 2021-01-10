"""Send an email."""

import smtplib
import pdb
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import environ
from string import Template


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


def main():
    # set up thhhe SMTP server
    # Gmail SMTP setup settings:
    # SMTP username: Your Gmail address.
    # SMTP password: Your Gmail password.
    # SMTP server address: smtp.gmail.com.
    # Gmail SMTP port (TLS): 587.
    # SMTP port (SSL): 465.
    # SMTP TLS/SSL required: yes.

    # pdb.set_trace()

    # s = smtplib.SMTP(host='smtp.gmail.com', port=587)
    # s = smtplib.SMTP(host='pop.mail.yahoo.com', port=995)
    # s = smtplib.SMTP(host='smtp-mail.outlook.com', port=587)
    s = smtplib.SMTP(host='smtp.office365.com', port=587)
    # s = smtplib.SMTP(host='smtp-mail.outlook.com', port=587)
    s.starttls()
    # s.login(environ['YOUTUBE_LOGIN'], environ['YOUTUBE_PASSWORD'])  # gmail
    # s.login('mike_kabika@yahoo.com', 'sbmhyh5s@JC777')  # yahoo
    # s.login('mikestyl75@hotmail.com', 'sbmhyh5s@JC777')
    # s.login('davidnabais7@outlook.com', '29061984David!')
    # s.login('davidnabais7@hotmail.com', '29061984David!')
    s.login('expertduneuf@hotmail.com', '29061984David!')

    # read contacts
    names, emails = get_contacts('contact.txt')
    message_template = read_template('message.txt')

    # for each contact, send the email:
    for name, email in zip(names, emails):
        msg = MIMEMultipart()  # create a message

        # add in  the actual person name to the message template*
        message = message_template.substitute(PERSON_NAME=name.title())

        # set up the parameters of the message
        msg['From']='expertduneuf@hotmail.com'
        msg['To']=email
        msg['Subject']="This is a test"

        # add in the messge body
        msg.attach(MIMEText(message, 'plain'))

        # send the message via the server set up earlier
        s.send_message(msg)

        del msg

    # Terminate the SMTP session and close the connection
    s.quit()


if __name__ == '__main__':
    main()
