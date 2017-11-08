from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.views.generic.edit import DeleteView, FormView

from predict.forms import PredictionForm
from predict.models import Prediction, PredictionWithRole


class MyPredictionList(TemplateView):
    template_name = "predict/prediction_list.html"

    def get(self, request, *args, **kwargs):
        current_user = request.user
        if not current_user.is_authenticated:
            return redirect('/all')

        return render(request, self.template_name,
                      {'predictions': self.get_predictions(),
                       "title": "My Predictions"})

    def get_predictions(self):
        current_user = self.request.user
        predictions = Prediction.objects.filter(
            Q(creator=current_user) | Q(witness=current_user) | Q(opponent=current_user) |
            Q(observers__email=current_user.email)).order_by('-date')
        role_predictions = map(lambda p: PredictionWithRole(p, get_role(p, current_user)), predictions)
        return list(role_predictions)


class PredictionList(TemplateView):
    template_name = "predict/prediction_list.html"

    def get(self, request, *args, **kwargs):
        # <view logic>
        return render(request, self.template_name,
                      {'predictions': self.get_predictions(),
                       "title": "All Predictions"})

    def get_predictions(self):
        current_user = self.request.user
        predictions = Prediction.objects.all().order_by('-date')
        role_predictions = map(lambda p: PredictionWithRole(p, get_role(p, current_user)), predictions)
        return list(role_predictions)


class PredictionDelete(LoginRequiredMixin, DeleteView):
    model = Prediction
    success_url = reverse_lazy('prediction_list')


class PredictionBase(FormView):
    template_name = 'prediction.html'
    form_class = PredictionForm
    success_url = reverse_lazy('my_prediction_list')

    def get_form_kwargs(self):
        kw = super(PredictionBase, self).get_form_kwargs()
        kw['request_method'] = self.request.method
        kw.update(self.get_details_dict())
        return kw

    def get_context_data(self, **kwargs):
        """Use this to add extra context."""
        context = super(PredictionBase, self).get_context_data(**kwargs)
        if self.request.method == "GET":
            details = self.get_details_dict()
            context.update(details)
        elif self.request.method == "POST":
            details = self.get_details_dict()
            context.update(details)
            context.update({'show_names': True})
        return context


class PredictionNew(LoginRequiredMixin, PredictionBase):
    def get_details_dict(self):
        details = {'show_names': True, 'new_form': True, 'details_editable': True,
                   "show_submit": True, "show_delete": False}
        return details

    def get_initial(self):
        initial = super(PredictionNew, self).get_initial()
        current_user = self.request.user
        if self.request.method == "GET":
            initial['creator_name'] = current_user.email
        return initial


class PredictionView(PredictionBase):
    def get_initial(self):
        initial = super(PredictionView, self).get_initial()
        current_user = self.request.user
        if self.request.method == "GET":
            prediction = self.get_prediction()
            initial['prediction_title'] = prediction.title
            initial['prediction_text'] = prediction.text
            initial['prediction_date'] = prediction.date
            initial['witness_email'] = prediction.witness.email
            initial['opponent_email'] = prediction.opponent.email
            initial['witness_confirmed'] = prediction.witness_confirmed
            initial['opponent_confirmed'] = prediction.opponent_confirmed
            initial['prediction_occurred'] = prediction.prediction_occurred
            initial['creator_name'] = prediction.creator.email
            initial['subscribed'] = current_user in prediction.observers.all()
            initial['logged_in'] = current_user.is_authenticated
            initial['pid'] = prediction.id
        return initial

    def get_details_dict(self):
        current_user = self.request.user
        logged_in = current_user.is_authenticated
        prediction = self.get_prediction()
        is_creator = current_user == prediction.creator
        is_witness = current_user == prediction.witness
        is_opponent = current_user == prediction.opponent

        details_editable = False
        show_submit = is_witness or is_opponent
        show_witness_confirmation = is_witness
        show_opponent_confirmation = is_opponent
        show_prediction_confirmation = is_witness
        show_names = is_witness or is_opponent or is_creator
        show_subscribe = not (is_witness or is_opponent or is_creator)
        show_delete = is_creator

        witness_confirmed = prediction.witness_confirmed
        opponent_confirmed = prediction.opponent_confirmed
        prediction_occurred = prediction.prediction_occurred
        details = {'details_editable': details_editable, 'show_witness_confirmation': show_witness_confirmation,
                   'show_opponent_confirmation': show_opponent_confirmation,
                   'show_prediction_confirmation': show_prediction_confirmation, 'show_names': show_names,
                   'show_subscribe': show_subscribe, 'show_delete': show_delete, 'pid': prediction.id,
                   'show_submit': show_submit, 'opponent_confirmed': opponent_confirmed,
                   'prediction_occurred': prediction_occurred, 'witness_confirmed': witness_confirmed,
                   "logged_in": logged_in}

        return details

    def get_prediction(self):
        return Prediction.objects.get(id=self.kwargs['pk'])

    def get_success_url(self):
        return super().get_success_url()

    def form_valid(self, form):
        current_user = self.request.user
        if form.cleaned_data['pid']:
            form.update_prediction(current_user)
        else:
            form.create_prediction(current_user)
        return super(PredictionView, self).form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


def get_role(p, current_user):
    if p.creator == current_user:
        return "creator"
    elif p.opponent == current_user:
        return "opponent"
    elif p.witness == current_user:
        return "witness"
    elif current_user in p.observers.all():
        return "observer"
    else:
        return ""
