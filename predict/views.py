from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.admin.widgets import AdminDateWidget

from predict.models import Prediction


class PredictionList(LoginRequiredMixin, ListView):
    model = Prediction

    def get_queryset(self):
        print(self.request.user)
        return super().get_queryset()


class PredictionCreate(LoginRequiredMixin, CreateView):
    model = Prediction
    success_url = reverse_lazy('prediction_list')
    fields = ['text', 'date', 'creator', 'opponent', 'witness']


class PredictionUpdate(LoginRequiredMixin, UpdateView):
    model = Prediction
    success_url = reverse_lazy('prediction_list')
    fields = ['text', 'date', 'creator', 'opponent', 'witness']



class PredictionDelete(LoginRequiredMixin, DeleteView):
    model = Prediction
    success_url = reverse_lazy('prediction_list')
