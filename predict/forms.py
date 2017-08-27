from django import forms

from predict.models import Prediction, Predictor

CHOICES = (
    (0, 'Yes'),
    (1, 'No')
)


class ConfirmPredictionForm(forms.Form):
    agree = forms.TypedMultipleChoiceField(
        widget=forms.RadioSelect(),
        empty_value=None,
        choices=CHOICES,
        label="Agree to participate",
        required=True)



class NewPredictionForm(forms.Form):
    prediction_text = forms.CharField(widget=forms.Textarea, label='Your Prediction')
    prediction_date = forms.DateField(widget=forms.SelectDateWidget, label='Date of predicted event')
    witness_email = forms.EmailField(label='Witness email', required=True)
    opponent_email = forms.EmailField(label='Opponent email', required=True)

    def create_prediction(self, creator):
        witness_email = self.cleaned_data['witness_email']
        try:
            witness = Predictor.objects.get(email=witness_email)
        except Predictor.DoesNotExist:
            witness = Predictor(username=witness_email, email=witness_email)
            witness.save()
            witness.send_invite_email(creator)

        opponent_email = self.cleaned_data['opponent_email']
        try:
            opponent = Predictor.objects.get(email=opponent_email)
        except Predictor.DoesNotExist:
            opponent = Predictor(username=opponent_email, email=opponent_email)
            opponent.save()
            opponent.send_invite_email(creator)

        prediction = Prediction(text=self.cleaned_data['prediction_text'], date=self.cleaned_data['prediction_date'],
                                opponent=opponent, witness=witness, witness_confirmed=False, opponent_confirmed=False,
                                creator=creator)
        prediction.save()
        prediction.send_creator_email()
        prediction.send_witness_email()
        prediction.send_opponent_email()
