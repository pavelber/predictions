import django
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'^$', views.PredictionList.as_view(), name='prediction_list'),
    url(r'^new$', views.PredictionCreate.as_view(), name='prediction_new'),
    url(r'^edit/(?P<pk>\d+)$', views.PredictionUpdate.as_view(), name='prediction_edit'),
    url(r'^delete/(?P<pk>\d+)$', views.PredictionDelete.as_view(), name='prediction_delete'),
    url(r'^accounts/login/$', auth_views.login, name='login'),
    url(r'^accounts/profile/$', views.PredictionList.as_view(), name='prediction_list'),
    url(r'^accounts/profile.json$', views.ListMyPredictions.as_view()),
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^accounts/logout/$', auth_views.logout, name='logout'),
    url(r'^oauth/', include('social_django.urls', namespace='social')),  # <--
    url(r'^admin/', django.contrib.admin.site.urls),
]

LOGIN_URL = 'accounts/login'
LOGOUT_URL = 'logout'
LOGIN_REDIRECT_URL = 'home'
