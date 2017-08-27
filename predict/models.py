from decouple import config
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class Predictor(User):
    class Meta:
        proxy = True

    def name(self):
        Predictor.fullname(self)

    @staticmethod
    def fullname(user):
        return user.first_name + " " + user.last_name

    def send_email(self, creator, role, new_user):
        send_email("Welcome to Predictions Web site!",
                   config('DEFAULT_FROM_EMAIL'), self.email, 'email_invitation.html',
                   {'creator': Predictor.fullname(creator),
                    'link': config('SITE_URL'),
                    'role': role,
                    'new_user': new_user
                    })


class Prediction(models.Model):
    text = models.TextField()
    date = models.DateTimeField()
    creator = models.ForeignKey(Predictor, related_name="creator")
    opponent = models.ForeignKey(Predictor, related_name="opponent")
    witness = models.ForeignKey(Predictor, related_name="witness")
    witness_confirmed = models.BooleanField(default=False)
    opponent_confirmed = models.BooleanField(default=False)

    def get_role(self,user):
        if user.id == self.witness.id:
            return "witness"
        elif user.id == self.opponent.id:
            return "opponent"
        else:
            return None

    def send_email(self):
        send_mail(
            'Subject here',
            'Here is the message.',
            'from@example.com',
            [],
            fail_silently=False,
        )

    def __str__(self):
        return self.text

    def send_creator_email(self):
        pass

    def send_witness_email(self):
        pass

    def send_opponent_email(self):
        pass


def send_email(subject, from_email, to, template, ctx):
    html_content = render_to_string(template, ctx)  # ...
    text_content = strip_tags(html_content)  # this strips the html, so people will have the text as well.

    # create the email, and attach the HTML version as well.
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
