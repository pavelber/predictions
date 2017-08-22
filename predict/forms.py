from django import forms
from django.core.mail import send_mail

class NewPredictionForm(forms.Form):
    prediction_text = forms.CharField(widget=forms.Textarea, label='Your Prediction')
    prediction_date = forms.DateField(label='Date of predicted event')
    witness_email = forms.CharField(label='Witness email')
    opponent_email = forms.CharField(label='Opponent email')

    def sendEmail(self):
        send_mail(
            'Subject here',
            'Here is the message.',
            'from@example.com',
            [self.cleaned_data['witness_email']],
            fail_silently=False,
        )
