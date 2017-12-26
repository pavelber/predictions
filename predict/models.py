from decouple import config
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags


class Predictor(User):
    class Meta:
        proxy = True

    def fullname(self):
        if (self.first_name and self.first_name != "") or (self.last_name and self.last_name != ""):
            name = self.first_name + " " + self.last_name
        else:
            name = self.email
        return name

    def send_invitation_email(self, prediction, role, text, is_new_user):
        send_email("You are invited participate in prediction",
                   config('DEFAULT_FROM_EMAIL'), self.email, 'email_invitation.html',
                   {'creator': prediction.creator.email,
                    'link': config('SITE_URL') + reverse('prediction', kwargs={'pk': prediction.id}),
                    'role': role,
                    'new_user': is_new_user,
                    'title': prediction.title,
                    'text':text
                    })

    def send_before_email(self, prediction):
        send_email("Prediction: one week to decision",
                   config('DEFAULT_FROM_EMAIL'), self.email, 'email_before.html',
                   {'link': config('SITE_URL') + reverse('prediction', kwargs={'pk': prediction.id}),
                    'title': prediction.title})

    def send_after_reminder_email(self, prediction):
        send_email("Prediction: decision was not made!",
                   config('DEFAULT_FROM_EMAIL'), self.email, 'email_after.html',
                   {'creator': prediction.creator.email,
                    'link': config('SITE_URL') + reverse('prediction', kwargs={'pk': prediction.id}),
                    'title': prediction.title
                    })

    def send_observer_email(self, prediction, subscribed):
        send_email("Your subscription to a wager",
                   config('DEFAULT_FROM_EMAIL'), self.email, 'email_subscriber_subscribed.html',
                   {'subscribed': subscribed,
                    'link': config('SITE_URL') + reverse('prediction', kwargs={'pk': prediction.id}),
                    'title': prediction.title
                    })

    def send_other_changed_email(self, role, prediction):
        pass

    def send_you_removed_as_email(self, role):
        pass


class Prediction(models.Model):
    title = models.TextField(default='No Title')
    text = models.TextField()
    date = models.DateField()
    creator = models.ForeignKey(Predictor, related_name="creator")
    opponent = models.ForeignKey(Predictor, related_name="opponent")
    witness = models.ForeignKey(Predictor, related_name="witness")
    witness_confirmed = models.BooleanField(default=False)
    opponent_confirmed = models.BooleanField(default=False)
    prediction_occurred = models.NullBooleanField(default=None, null=True)
    before_mails_sent = models.BooleanField(default=False)
    date_mail_sent = models.BooleanField(default=False)
    after_mails_sent = models.BooleanField(default=False)

    observers = models.ManyToManyField(Predictor);

    # TODO: move roles names and text to one place
    def get_role(self, user):
        if user.id == self.witness.id:
            return "witness"
        elif user.id == self.opponent.id:
            return "opponent"
        else:
            return None

    def send_confirmation_email(self, role, confirmed):
        send_email("Participation confirmation",
                   config('DEFAULT_FROM_EMAIL'), self.creator.email, 'email_confirmation.html',
                   {'link': config('SITE_URL') + reverse('prediction', kwargs={'pk': self.id}),
                    'role': role,
                    'confirmed': confirmed,
                    'title': self.title})

    def __str__(self):
        return self.title

    def send_creator_email(self):
        send_email("Prediction created",
                   config('DEFAULT_FROM_EMAIL'), self.creator.email, 'email_creation.html',
                   {'link': config('SITE_URL') + reverse('prediction', kwargs={'pk': self.id}),
                    'title': self.title})

    def send_witness_email(self):
        send_email("Prediction: It's time to decide",
                   config('DEFAULT_FROM_EMAIL'), self.witness.email, 'email_time_to_decide.html',
                   {'link': config('SITE_URL') +  reverse('prediction', kwargs={'pk': self.id}),
                    'title': self.title})

    def send_opponent_changed_decision_email(self, opponent_confirmed):
        pass

    def send_witness_changed_decision_email(self, witness_confirmed):
        pass

    def send_email_details_updated(self):
        pass

    def decision_made(self, prediction_confirmed):
        pass


class PredictionWithRole:
    def __init__(self, prediction, role):
        self.prediction = prediction
        self.role = role


def send_email(subject, from_email, to, template, ctx):
    html_content = render_to_string(template, ctx)  # ...
    text_content = strip_tags(html_content)  # this strips the html, so people will have the text as well.

    # create the email, and attach the HTML version as well.
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
