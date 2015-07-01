import smtplib

"""
Example code:

from django.core.mail import EmailMessage
subject = "Formularz kontaktowy - %s" % request.POST['reason']
message_template = loader.get_template('main/contact_form_email.txt')
message_context = Context({ 'content': request.POST['content'], 'reason' : request.POST['reason'] })
message = message_template.render(message_context)
				
sender = u'24gole - formularz kontaktowy<marek@24gole.pl>'
recipients = [u'Marek Mikuliszyn<marek@24gole.pl>']
EmailMessage(subject, message, sender, recipients).send()
"""


class Gmailer:
    """
    Send email through Gmail.

    use: Gmailer(user, password[, host])
    use: send(to_addrs, subject, message[, from_addrs])
    """
    host = 'smtp.gmail.com'

    def __init__(self, user, password, host=None):
        """
        Set Google username and passsword.

        use: Gmailer(user, password[, host])
        """
        self.user = user
        self.password = password
        if host: self.host = host

    def send(self, to_addrs, subject, message, from_addr=None):
        """
        Set username and passsword

        use: send(to_addrs, subject, message[, from_addrs])
        """
        if not from_addr: from_addr = self.user
        data = "From: %s\nTo: %s\nSubject: %s\n\n%s" \
               % (from_addr, to_addrs, subject, message)
        try:
            server = smtplib.SMTP(self.host)
            server.ehlo()
            server.starttls()
            server.ehlo()  # This must be done before and after starttls().
            server.login(self.user, self.password)
            server.sendmail(from_addr, to_addrs, data)
        except:
            raise
        try:
            server.quit()  # This always fails and can safely be ignored.
        except:
            pass
