from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from predict.cron import check_one_week_before, check_exact_date, check_one_week_after, run_tasks_hourly
from . import views

urlpatterns = [
    url(r'^all$', views.PredictionList.as_view(), name='prediction_list'),
    url(r'^new$', views.PredictionNew.as_view(), name='prediction_new'),
    url(r'^prediction/(?P<pk>\d+)$', views.PredictionView.as_view(), name='prediction'),
    url(r'^prediction/$', views.PredictionNew.as_view(), name='prediction'),
    url(r'^accounts/login/$', auth_views.login, name='login'),
    url(r'^accounts/profile/$', views.PredictionList.as_view(), name='prediction_list'),
    url(r'^list/$', views.PredictionList.as_view(), name='prediction_list'),
    url(r'^predictions$', views.JsonPredictionList.as_view(), name='filtered_prediction_list'),
    # url(r'^accounts/profile.json$', views.ListMyPredictions.as_view()),
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^accounts/logout/$', auth_views.logout, name='logout'),
    url(r'^oauth/', include('social_django.urls', namespace='social')),  # <--
    url(r'^admin/', admin.site.urls),
    url(r'^email/$', views.email, name='email'),
    url(r'^success/$', views.SuccessView.as_view(), name='success'),
    url('faq.html', views.FAQView.as_view(), name='faq'),
    url('about.html', views.AboutView.as_view(), name='about'),
]



LOGIN_URL = 'accounts/login'
LOGOUT_URL = 'logout'
LOGIN_REDIRECT_URL = 'home'

run_tasks_hourly((check_one_week_after, check_one_week_before,check_exact_date))
