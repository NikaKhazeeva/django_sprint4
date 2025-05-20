from django.views.generic import TemplateView
from django.shortcuts import render


class IndexPageView(TemplateView):
    """Главная."""

    template_name = "blog/index.html"


class AboutPageView(TemplateView):
    """Страница о проекте."""

    template_name = "pages/about.html"


class RulesPageView(TemplateView):
    """Правила."""

    template_name = "pages/rules.html"


def page_not_found(request, exception):
    """404 ошибка."""
    return render(request, 'pages/404.html', status=404)


def server_error(request):
    """500 ошибка."""
    return render(request, 'pages/500.html', status=500)


def csrf_failure(request, reason=''):
    """403 ошибка."""
    return render(request, 'pages/403csrf.html', status=403)
