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


class PredictionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        method = kwargs.pop('request_method')

        if method == "GET":
            details_editable = kwargs.pop('details_editable',  True)
            show_witness_confirmation = kwargs.pop('show_witness_confirmation', False)
            show_opponent_confirmation = kwargs.pop('show_opponent_confirmation',False)
            show_prediction_confirmation = kwargs.pop('show_prediction_confirmation', False)
            show_names = kwargs.pop('show_names',True)
            show_subscribe = kwargs.pop('show_subscribe', False)
            show_delete = kwargs.pop('show_delete', False)
            pid = kwargs.pop('pid',None)
        super(PredictionForm, self).__init__(*args, **kwargs)
        if method == "GET":
            self.fields['prediction_title'].widget.attrs['readonly'] = not details_editable
            self.fields['prediction_text'].widget.attrs['readonly'] = not details_editable
            self.fields['prediction_date'].widget.attrs['readonly'] = not details_editable
            self.fields['creator_name'].widget.attrs['readonly'] = True
            self.fields['witness_email'].widget.attrs['readonly'] = not details_editable
            self.fields['opponent_email'].widget.attrs['readonly'] = not details_editable
            self.fields['witness_confirmed'].widget.attrs['readonly'] = show_witness_confirmation
            self.fields['opponent_confirmed'].widget.attrs['readonly'] = show_opponent_confirmation
            self.fields['prediction_occurred'].widget.attrs['readonly'] = show_prediction_confirmation
            self.fields['pid'].widget.attrs['readonly'] = True

    prediction_title = forms.CharField()
    prediction_text = forms.CharField(widget=forms.Textarea)
    prediction_date = forms.DateField(widget=forms.SelectDateWidget)
    creator_name = forms.CharField(required=False)
    witness_email = forms.EmailField(required=False)
    opponent_email = forms.EmailField(required=False)
    witness_confirmed = forms.TypedChoiceField(choices=CHOICES_YES_NO,required=False)
    opponent_confirmed = forms.TypedChoiceField(choices=CHOICES_YES_NO,required=False)
    prediction_occurred = forms.TypedChoiceField(choices=CHOICES_THINKING_YES_NO,required=False)
    subscribed = forms.TypedChoiceField(choices=CHOICES_YES_NO,required=False)
    pid = forms.IntegerField(widget=forms.HiddenInput(),required=False)

    def clean_prediction_date(self):
        prediction_date = self.cleaned_data['prediction_date']
        print(type(prediction_date))
        if prediction_date < date.today() + timedelta(days=7):
            raise forms.ValidationError("Date should be in a week or more from now!")
        return prediction_date

    def create_prediction(self, creator):
        witness_email = self.cleaned_data['witness_email']
        opponent_email = self.cleaned_data['opponent_email']

        witness, is_new_witness = get_or_create_user(witness_email)
        opponent, is_new_opponent = get_or_create_user(opponent_email)

        prediction = Prediction(text=self.cleaned_data['prediction_text'], title=self.cleaned_data['prediction_title'],
                                date=self.cleaned_data['prediction_date'],
                                opponent=opponent, witness=witness, witness_confirmed=False, opponent_confirmed=False,
                                creator=creator)
        prediction.save()
        witness.send_invitation_email(prediction, "witness", is_new_witness)
        opponent.send_invitation_email(prediction,  "opponent", is_new_opponent)
        prediction.send_creator_email()

    def update_prediction(self, current_user):
        prediction = Prediction.objects.get(id=self.cleaned_data['pid'])
        if current_user == prediction.creator:
            prediction_title = self.cleaned_data['prediction_title']
            prediction_text = self.cleaned_data['prediction_text']
            prediction_date = self.cleaned_data['prediction_date']
            witness_email = self.cleaned_data['witness_email']
            opponent_email = self.cleaned_data['opponent_email']
            if witness_email != prediction.witness.email:
                prediction.witness.send_you_removed_as_email('witness')
                witness, is_new_witness = get_or_create_user(witness_email)
                prediction.witness = witness
                prediction.save()
                prediction.opponent.send_other_changed_email("witness", prediction)
                prediction.witness.send_invitation_email(prediction, "witness", is_new_witness)

            if opponent_email != prediction.opponent.email:
                prediction.opponent.send_you_removed_as_email('opponent')
                opponent, is_new_opponent = get_or_create_user(opponent_email)
                prediction.opponent = opponent
                prediction.save()
                prediction.witness.send_other_changed_email("opponent", prediction)
                prediction.opponent.send_invitation_email(prediction, "opponent", is_new_opponent)

            if prediction_title != prediction.title or \
                            prediction_text != prediction.text or \
                            prediction_date != prediction.date:
                prediction.title = prediction_title
                prediction.text = prediction_text
                prediction.date = prediction_date
                prediction.witness_confirmed = False
                prediction.opponent_confirmed = False
                prediction.save()
                prediction.send_email_details_updated()

        elif current_user == prediction.witness:
            witness_confirmed = self.cleaned_data['witness_confirmed']
            if witness_confirmed != prediction.witness_confirmed:
                prediction.witness_confirmed = witness_confirmed
                prediction.save()
                prediction.send_witness_changed_decision_email(witness_confirmed)
        elif current_user == prediction.opponent:
            opponent_confirmed = self.cleaned_data['opponent_confirmed']
            if opponent_confirmed != prediction.opponent_confirmed:
                prediction.opponent_confirmed = opponent_confirmed
                prediction.save()
                prediction.send_opponent_changed_decision_email(opponent_confirmed)
        else:
            subscribed = self.cleaned_data['subscribed']
            if not subscribed:
                prediction.observers.remove(current_user)
            else:
                prediction.observers.add(current_user)
            prediction.save()
            current_user.send_observer_email(prediction, subscribed)


def get_or_create_user(email):
    try:
        user = Predictor.objects.get(email=email)
        is_new = False
    except Predictor.DoesNotExist:
        user = Predictor(username=email, email=email)
        user.save()
        is_new = True
    return user, is_new
