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

    def name(self):
        Predictor.fullname(self)

    @staticmethod
    def fullname(user):
        return user.first_name + " " + user.last_name

    def send_email(self, creator, role, is_new_user, prediction_id):
        send_email("You are invited participate in prediction",
                   config('DEFAULT_FROM_EMAIL'), self.email, 'email_invitation.html',
                   {'creator': Predictor.fullname(creator),
                    'link': config('SITE_URL') + reverse('prediction_confirm', kwargs={'pk': prediction_id}),
                    'role': role,
                    'new_user': is_new_user
                    })


class Prediction(models.Model):
    text = models.TextField()
    date = models.DateTimeField()
    creator = models.ForeignKey(Predictor, related_name="creator")
    opponent = models.ForeignKey(Predictor, related_name="opponent")
    witness = models.ForeignKey(Predictor, related_name="witness")
    witness_confirmed = models.BooleanField(default=False)
    opponent_confirmed = models.BooleanField(default=False)

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
        return self.text

    def send_creator_email(self):
        send_email("Prediction created",
                   config('DEFAULT_FROM_EMAIL'), self.creator.email, 'email_creation.html',
                   {'link': config('SITE_URL') + reverse('my_prediction_list')})


def send_email(subject, from_email, to, template, ctx):
    html_content = render_to_string(template, ctx)  # ...
    text_content = strip_tags(html_content)  # this strips the html, so people will have the text as well.

    # create the email, and attach the HTML version as well.
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
