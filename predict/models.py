from django.contrib.auth.models import User
from django.db import models


class Prediction(models.Model):
    text = models.TextField()
    date = models.DateTimeField()
    creator = models.ForeignKey(User, related_name="creator")
    opponent = models.ForeignKey(User, related_name="opponent")
    witness = models.ForeignKey(User, related_name="witness")
    witness_confirmed = models.BooleanField(default=False)
    opponent_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.text
