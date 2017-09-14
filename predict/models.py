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
        return self.first_name + " " + self.last_name

    def send_invitation_email(self, creator, role, is_new_user):
        send_email("You are invited participate in prediction",
                   config('DEFAULT_FROM_EMAIL'), self.email, 'email_invitation.html',
                   {'creator': self.fullname(),
                    'link': config('SITE_URL') + reverse('prediction_confirm', kwargs={'pk': self.id}),
                    'role': role,
                    'new_user': is_new_user
                    })

    def send_before_email(self):
        send_email("Prediction: one week to decision",
                   config('DEFAULT_FROM_EMAIL'), self.email, 'email_before.html',
                   {'link': config('SITE_URL') + reverse('prediction_edit', kwargs={'pk':  self.id})})

    def send_after_reminder_email(self):
        send_email("Prediction: decision was not made!",
                   config('DEFAULT_FROM_EMAIL'), self.email, 'email_after.html',
                   {'creator': self.fullname(),
                    'link': config('SITE_URL') + reverse('prediction_edit', kwargs={'pk':  self.id})
                    })


class Prediction(models.Model):
    title = models.TextField(default='No Title')
    text = models.TextField()
    date = models.DateTimeField()
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
                   {'link': config('SITE_URL') + reverse('my_prediction_list'),
                    'role': role,
                    'confirmed': confirmed})

    def __str__(self):
        return self.title

    def send_creator_email(self):
        send_email("Prediction created",
                   config('DEFAULT_FROM_EMAIL'), self.creator.email, 'email_creation.html',
                   {'link': config('SITE_URL') + reverse('my_prediction_list')})

    def send_witness_email(self):
        send_email("Prediction: It's time to decide",
                   config('DEFAULT_FROM_EMAIL'), self.witness.email, 'email_time_to_decide.html',
                   {'link': config('SITE_URL') + reverse('my_prediction_list')})


def send_email(subject, from_email, to, template, ctx):
    html_content = render_to_string(template, ctx)  # ...
    text_content = strip_tags(html_content)  # this strips the html, so people will have the text as well.

    # create the email, and attach the HTML version as well.
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
