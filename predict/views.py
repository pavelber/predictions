from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView

from predict.forms import NewPredictionForm
from predict.models import Prediction


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


class PredictionNew(FormView):
    template_name = 'new.html'
    form_class = NewPredictionForm
    success_url = '/thanks.html'

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        print(form.cleaned_data['witness_email'])
        form.sendEmail()
        return super(PredictionNew, self).form_valid(form)