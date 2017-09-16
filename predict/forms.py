from datetime import date, timedelta

from django import forms
from django.forms import HiddenInput

from predict.models import Prediction, Predictor

CHOICES_YES_NO = (
    (True, 'Yes'),
    (False, 'No')
)

CHOICES_THINKING_YES_NO = (
    (None, '---'),
    (True, 'Yes'),
    (False, 'No')
)


class ConfirmPredictionForm(forms.Form):
    agree = forms.TypedChoiceField(
        choices=CHOICES_YES_NO,
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
    prediction_title = forms.CharField(label='Prediction Title')
    prediction_text = forms.CharField(widget=forms.Textarea, label='Your Prediction')
    prediction_date = forms.DateField(widget=forms.SelectDateWidget, label='Date of predicted event')
    witness_email = forms.EmailField(label='Witness email', required=True)
    opponent_email = forms.EmailField(label='Opponent email', required=True)

    def clean_prediction_date(self):
        prediction_date = self.cleaned_data['prediction_date']
        print(type(prediction_date))
        if prediction_date < date.today() + timedelta(days=7):
            raise forms.ValidationError("Date should be in a week or more from now!")
        return prediction_date

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

        prediction = Prediction(text=self.cleaned_data['prediction_text'], title=self.cleaned_data['prediction_title'],
                                date=self.cleaned_data['prediction_date'],
                                opponent=opponent, witness=witness, witness_confirmed=False, opponent_confirmed=False,
                                creator=creator)
        prediction.save()
        witness.send_invitation_email(creator, "witness", is_new_witness)
        opponent.send_invitation_email(creator, "opponent", is_new_opponent)
        prediction.send_creator_email()


class PredictionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        details_editable = kwargs.pop('details_editable')
        show_witness_confirmation = kwargs.pop('show_witness_confirmation')
        show_opponent_confirmation = kwargs.pop('show_opponent_confirmation')
        show_prediction_confirmation = kwargs.pop('show_prediction_confirmation')
        show_names = kwargs.pop('show_names')
        show_subscribe = kwargs.pop('show_subscribe')
        show_delete = kwargs.pop('show_delete')
        pid = kwargs.pop('pid')
        super(PredictionForm, self).__init__(*args, **kwargs)
        self.fields['prediction_title'].widget.attrs['readonly'] = not details_editable
        self.fields['prediction_text'].widget.attrs['readonly'] = not details_editable
        self.fields['prediction_date'].widget.attrs['readonly'] = not details_editable
        self.fields['creator_name'].widget.attrs['readonly'] = True
        self.fields['witness_email'].widget.attrs['readonly'] = not details_editable
        self.fields['opponent_email'].widget.attrs['readonly'] = not details_editable
        self.fields['witness_confirmed'].widget.attrs['readonly'] = show_witness_confirmation
        self.fields['opponent_confirmed'].widget.attrs['readonly'] = show_opponent_confirmation
        self.fields['prediction_occurred'].widget.attrs['readonly'] = show_prediction_confirmation
        self.fields['pid'].widget.attrs['readonly'] = pid

    prediction_title = forms.CharField()
    prediction_text = forms.CharField(widget=forms.Textarea)
    prediction_date = forms.DateField(widget=forms.SelectDateWidget)
    creator_name = forms.CharField()
    witness_email = forms.EmailField()
    opponent_email = forms.EmailField()
    witness_confirmed = forms.TypedChoiceField(choices=CHOICES_YES_NO)
    opponent_confirmed = forms.TypedChoiceField(choices=CHOICES_YES_NO)
    prediction_occurred = forms.TypedChoiceField(choices=CHOICES_THINKING_YES_NO)
    subscribed = forms.TypedChoiceField(choices=CHOICES_YES_NO)
    pid = forms.IntegerField(widget=forms.HiddenInput())
