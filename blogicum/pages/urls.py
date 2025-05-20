from django.urls import path
from .views import IndexPageView, AboutPageView, RulesPageView

app_name = 'pages'

urlpatterns = [
    path("", IndexPageView.as_view(), name='index'),
    path('about/', AboutPageView.as_view(), name='about'),
    path('rules/', RulesPageView.as_view(), name='rules'),
]
