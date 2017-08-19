from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.admin.widgets import AdminDateWidget
from rest_framework.views import APIView
from rest_framework.response import Response

from predict.models import Prediction
from predict.serializers import PredictionSerializer


class ListMyPredictions(LoginRequiredMixin,APIView):

    def get(self, request, format=None):

        current_user = self.request.user
        predictions = filter(lambda p: p.creator == current_user,Prediction.objects.all())
        serializer = PredictionSerializer(predictions, many=True,context={'request':request})
        return Response(serializer.data)


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

