from django import forms
from django.forms import HiddenInput

from predict.models import Prediction, Predictor

CHOICES = (
    (True, 'Yes'),
    (False, 'No')
)


class ConfirmPredictionForm(forms.Form):
    agree = forms.TypedChoiceField(
        choices=CHOICES,
        label="Agree to participate",
        required=True)
    pk = forms.IntegerField(widget=HiddenInput)

    def save_confirmation(self, user):

        prediction_id = self.cleaned_data['pk']
        prediction = Prediction.objects.get(pk=prediction_id)

        confirmed = self.cleaned_data['agree']

        if prediction.witness == user:
            prediction.witness_confirmed = confirmed
            role = "witness"
        elif prediction.opponent == user:
            prediction.opponent_confirmed = confirmed
            role = "opponent"
        else:
            raise Exception('Unknown user in prediction confirmation')
        prediction.save()
        prediction.send_confirmation_email(role, confirmed)


class NewPredictionForm(forms.Form):
    prediction_text = forms.CharField(widget=forms.Textarea, label='Your Prediction')
    prediction_date = forms.DateField(widget=forms.SelectDateWidget, label='Date of predicted event')
    witness_email = forms.EmailField(label='Witness email', required=True)
    opponent_email = forms.EmailField(label='Opponent email', required=True)

    def create_prediction(self, creator):
        witness_email = self.cleaned_data['witness_email']
        try:
            witness = Predictor.objects.get(email=witness_email)
            is_new_witness = False
        except Predictor.DoesNotExist:
            witness = Predictor(username=witness_email, email=witness_email)
            witness.save()
            is_new_witness = True

        opponent_email = self.cleaned_data['opponent_email']
        try:
            opponent = Predictor.objects.get(email=opponent_email)
            is_new_opponent = False
        except Predictor.DoesNotExist:
            opponent = Predictor(username=opponent_email, email=opponent_email)
            opponent.save()
            is_new_opponent = True

        prediction = Prediction(text=self.cleaned_data['prediction_text'], date=self.cleaned_data['prediction_date'],
                                opponent=opponent, witness=witness, witness_confirmed=False, opponent_confirmed=False,
                                creator=creator)
        prediction.save()
        witness.send_email(creator, "witness", is_new_witness, prediction.id)
        opponent.send_email(creator, "opponent", is_new_opponent, prediction.id)
        prediction.send_creator_email()
