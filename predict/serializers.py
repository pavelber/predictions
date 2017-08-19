from django.contrib.auth.models import User
from rest_framework import serializers

from predict.models import Prediction


class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = ('text', 'date', 'creator', 'opponent', 'witness', 'witness_confirmed', 'opponent_confirmed')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
