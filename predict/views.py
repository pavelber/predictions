import datetime
from django.contrib.auth import logout as auth_logout

from decouple import config
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, render_to_response
from django.template import RequestContext
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.base import View
from django.views.generic.edit import FormView

from predict.forms import PredictionForm
from predict.models import Prediction, PredictionWithRole, send_email, link_to_prediction, OPPONENT_ROLE, WITNESS_ROLE, \
    direct_link_to_prediction
from .forms import ContactForm


class BaseTemplateView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name,
                      {"logged_in": self.request.user.is_authenticated})


class JsonStatisticsView(View):
    def get(self, request, *args, **kwargs):
        current_user = self.request.user
        if current_user.is_authenticated:
            predictions = self.get_predictions()
            pending_confirmation = len(list(filter(
                lambda p:
                (p.witness == current_user and p.witness_confirmed is False) or
                (p.opponent == current_user and p.opponent_confirmed is False), predictions)))
            pending_resolution = len(list(filter(
                lambda p:
                p.witness == current_user and p.witness_confirmed is True and p.prediction_occurred is None,
                predictions)))
        else:
            pending_resolution = 0
            pending_confirmation = 0
        return JsonResponse({"pending_confirmation": pending_confirmation, "pending_resolution": pending_resolution})

    def get_predictions(self):
        current_user = self.request.user
        role_filter = create_filter_from_role("my", current_user)
        predictions = Prediction.objects.filter(role_filter)
        return list(predictions)


class JsonPredictionList(View):
    def get(self, request, *args, **kwargs):
        predictions = self.get_predictions()
        json = list(
            map(lambda p: serialize(p), predictions)
        )
        return JsonResponse({"predictions": json})

    def get_predictions(self):
        current_user = self.request.user
        role = self.request.GET.get('role')
        status = self.request.GET.get('status')
        date = self.request.GET.get('date')
        role_filter = create_filter_from_role(role, current_user)
        status_filter = create_filter_from_status(status)
        date_filter = create_filter_from_date(date)
        all_filter = create_filter_from([role_filter, status_filter, date_filter])

        predictions = all_filter.order_by('-date')
        role_predictions = map(lambda p: PredictionWithRole(p, get_role(p, current_user)), predictions)
        return list(role_predictions)


class PredictionList(TemplateView):
    template_name = "prediction_list.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name,
                      {'predictions': self.get_predictions(),
                       "logged_in": self.request.user.is_authenticated})

    def get_predictions(self):
        current_user = self.request.user
        predictions = Prediction.objects.all().order_by('-date')
        role_predictions = map(lambda p: PredictionWithRole(p, get_role(p, current_user)), predictions)
        return list(role_predictions)


class PredictionBase(FormView):
    template_name = 'prediction.html'
    form_class = PredictionForm
    success_url = reverse_lazy('prediction_list')

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
        context.update({'logged_in': self.request.user.is_authenticated})
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
            initial['logged_in'] = current_user.is_authenticated
        return initial

    def form_valid(self, form):
        current_user = self.request.user
        form.create_prediction(current_user)
        return super(PredictionNew, self).form_valid(form)


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
        logged_in = current_user.is_authenticated.value
        prediction = self.get_prediction()
        is_creator = current_user == prediction.creator
        is_witness = current_user == prediction.witness
        is_opponent = current_user == prediction.opponent
        is_subscriber = not (is_witness or is_opponent or is_creator)

        details_editable = is_creator and not (prediction.witness_confirmed or prediction.opponent_confirmed)
        show_subscribe = is_subscriber and prediction.prediction_occurred is None

        show_submit = (is_witness and not prediction.witness_confirmed) \
                      or (is_opponent and not prediction.opponent_confirmed) \
                      or (is_creator and details_editable) or (
                              is_witness and not prediction.prediction_occurred) or show_subscribe

        show_witness_confirmation = is_witness and not prediction.witness_confirmed
        show_opponent_confirmation = is_opponent and not prediction.opponent_confirmed
        show_prediction_confirmation = is_witness and prediction.witness_confirmed
        show_names = is_witness or is_opponent or is_creator
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'site': config('SITE_URL')})
        return context

    def form_valid(self, form):
        current_user = self.request.user
        pid = form.cleaned_data['pid']
        prediction = Prediction.objects.get(pk=pid)
        if 'Delete' in form.data:
            if prediction.creator == current_user:
                prediction.delete()
                send_email("Prediction deleted",
                           config('DEFAULT_FROM_EMAIL'), prediction.creator.email, 'email_delete.html',
                           {'link': config('SITE_URL') + reverse('prediction_list'), 'title': prediction.title})
        else:
            form.update_prediction(current_user)
        return super(PredictionView, self).form_valid(form)


def get_role(p, current_user):
    if p.creator == current_user:
        return "creator"
    elif p.opponent == current_user:
        return "opponent"
    elif p.witness == current_user:
        return "referee"
    elif current_user in p.observers.all():
        return "observer"
    else:
        return ""


class FAQView(BaseTemplateView):
    template_name = "faq.html"


class AboutView(BaseTemplateView):
    template_name = "about.html"


class SuccessView(BaseTemplateView):
    template_name = "success.html"


def send_contact_mail(subject, message, from_email):
    msg = EmailMultiAlternatives(subject, message, from_email, [config('ADMIN_EMAIL')])
    msg.attach_alternative(message, "text/plain")
    msg.send()


def email(request):
    if request.method == 'GET':
        form = ContactForm()
    else:
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            from_email = form.cleaned_data['from_email']
            message = form.cleaned_data['message']
            try:
                send_contact_mail(subject, message, from_email)
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('success')
    return render(request, "email.html", {'form': form, "logged_in": request.user.is_authenticated})


def create_filter_from_role(role, current_user):
    if role == 'my':
        role_filter = Q(creator=current_user) | Q(witness=current_user) | Q(opponent=current_user) | Q(
            observers__email=current_user.email)
    elif role == 'pending':
        role_filter = (Q(witness=current_user) & Q(witness_confirmed=False)) | (
                Q(opponent=current_user) & Q(opponent_confirmed=False))
    elif role == 'notresolved':
        role_filter = Q(witness=current_user) & Q(witness_confirmed=True) & Q(prediction_occurred=None)
    else:
        role_filter = None

    return role_filter


def create_filter_from_status(status):
    if status == 'open':
        status_filter = Q(prediction_occurred=None)
    elif status == 'closed':
        status_filter = ~Q(prediction_occurred=None)
    else:
        status_filter = None
    return status_filter


def create_filter_from_date(date):
    if date == 'future':
        date_filter = Q(date__gte=datetime.date.today())
    elif date == 'past':
        date_filter = Q(date__lte=datetime.date.today())
    else:
        date_filter = None
    return date_filter


def create_filter_from(filters):
    filters = list(filter(lambda f: f is not None, filters))
    if len(filters) == 0:
        return Prediction.objects.all()
    else:
        all_filter = filters[0]
        for i in range(1, len(filters)):
            all_filter = all_filter & filters[i]
    return Prediction.objects.filter(all_filter)


def create_comment(p):
    if (p.role == OPPONENT_ROLE and not p.prediction.opponent_confirmed) or (
            p.role == WITNESS_ROLE and not p.prediction.witness_confirmed):
        return "Confirm your participation!"
    elif p.role == WITNESS_ROLE and p.prediction.prediction_occurred and datetime.date.today() > p.prediction.date:
        return "Decide the wager fate!"
    else:
        return ""


def serialize(p):
    return {
        "title": p.prediction.title,
        "date": p.prediction.date,
        "text": p.prediction.text,
        "prediction_occurred": p.prediction.prediction_occurred_as_string(),
        "opponent_confirmed": p.prediction.opponent_confirmed,
        "witness_confirmed": p.prediction.witness_confirmed,
        "pid": p.prediction.id,
        "role": p.role,
        "link": direct_link_to_prediction(p.prediction.id),
        "comment": create_comment(p)
    }


def logout(request):
    """Logs out user"""
    auth_logout(request)
    return render_to_response('prediction_list.html', {}, RequestContext(request))