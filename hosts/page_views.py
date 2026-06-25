from django.views.generic import TemplateView


class HostManagerPageView(TemplateView):
    template_name = "hosts/index.html"
