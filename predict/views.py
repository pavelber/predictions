from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView

from predict.forms import NewPredictionForm, ConfirmPredictionForm
from predict.models import Prediction
import re

# class ListMyPredictions(LoginRequiredMixin, APIView):
#     def get(self, request, format=None):
#         current_user = self.request.user
#         predictions = filter(
#             lambda p: p.creator == current_user or p.witness == current_user or p.opponent == current_user,
#             Prediction.objects.all())
#         serializer = PredictionSerializer(predictions, many=True)
#         return Response(serializer.data)


class MyPredictionList(LoginRequiredMixin, ListView):
    model = Prediction
    template_name = "predict/my_prediction_list.html"

    def get_queryset(self):
        current_user = self.request.user
        print(str(current_user))
        predictions = Prediction.objects.filter(
            Q(creator=current_user) | Q(witness=current_user) | Q(opponent=current_user)).order_by('-date')
        return predictions


class PredictionList(LoginRequiredMixin, ListView):
    model = Prediction

    def get_queryset(self):
        current_user = self.request.user
        print(str(current_user))
        predictions = Prediction.objects.all().order_by('-date')
        return predictions


class PredictionUpdate(LoginRequiredMixin, UpdateView):
    model = Prediction
    success_url = reverse_lazy('prediction_list')
    fields = ['text', 'date', 'creator', 'opponent', 'witness']


class PredictionDelete(LoginRequiredMixin, DeleteView):
    model = Prediction
    success_url = reverse_lazy('prediction_list')


class PredictionNew(LoginRequiredMixin, FormView):
    template_name = 'new.html'
    form_class = NewPredictionForm
    success_url = '/'

    def form_valid(self, form):
        current_user = self.request.user
        form.create_prediction(current_user)
        return super(PredictionNew, self).form_valid(form)


class PredictionConfirm(LoginRequiredMixin, FormView):
    template_name = 'confirm.html'
    form_class = ConfirmPredictionForm
    success_url = '/'

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Use this to add extra context."""
        context = super(PredictionConfirm, self).get_context_data(**kwargs)
        current_user = self.request.user
        prediction_id = self.kwargs['pk']
        prediction = Prediction.objects.get(pk=prediction_id)
        context['text'] = prediction.text
        context['date'] = prediction.date
        context['role'] = prediction.get_role(current_user)
        return context

    def form_valid(self, form):
        current_user = self.request.user
        return super(PredictionNew, self).form_valid(form)
