from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.edit import DeleteView, FormView

from predict.forms import PredictionForm
from predict.models import Prediction, PredictionWithRole


class MyPredictionList(LoginRequiredMixin, TemplateView):
    template_name = "predict/prediction_list.html"

    def get(self, request, *args, **kwargs):
        # <view logic>
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


class PredictionList(LoginRequiredMixin, TemplateView):
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


class PredictionNew(LoginRequiredMixin, FormView):
    template_name = 'prediction.html'
    form_class = PredictionForm
    success_url = reverse_lazy('my_prediction_list')

    def get_form_kwargs(self):
        kw = super(PredictionNew, self).get_form_kwargs()
        kw['request_method'] = self.request.method
        return kw


class PredictionView(LoginRequiredMixin, FormView):
    template_name = 'prediction.html'
    form_class = PredictionForm
    success_url = reverse_lazy('my_prediction_list')

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
            initial['pid'] = prediction.id
        return initial

    def get_context_data(self, **kwargs):
        """Use this to add extra context."""
        context = super(PredictionView, self).get_context_data(**kwargs)
        if self.request.method == "GET":
            details = self.get_details_dict()
            context.update(details)
        return context

    def get_details_dict(self):
        current_user = self.request.user
        prediction = self.get_prediction()
        is_creator = current_user == prediction.creator
        is_witness = current_user == prediction.witness
        is_opponent = current_user == prediction.opponent

        details_editable = is_creator
        show_witness_confirmation = is_witness
        show_opponent_confirmation = is_opponent
        show_prediction_confirmation = is_witness
        show_names = is_witness or is_opponent or is_creator
        show_subscribe = not (is_witness or is_opponent or is_creator)
        show_delete = details_editable
        details = {'details_editable': details_editable, 'show_witness_confirmation': show_witness_confirmation,
                   'show_opponent_confirmation': show_opponent_confirmation,
                   'show_prediction_confirmation': show_prediction_confirmation, 'show_names': show_names,
                   'show_subscribe': show_subscribe, 'show_delete': show_delete, 'pid': prediction.id}
        return details

    def get_prediction(self):
        return Prediction.objects.get(id=self.kwargs['pk'])

    def get_form_kwargs(self):
        kw = super(PredictionView, self).get_form_kwargs()
        kw['request_method'] = self.request.method
        if self.request.method == "GET":
            kw.update(self.get_details_dict())
        return kw

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
