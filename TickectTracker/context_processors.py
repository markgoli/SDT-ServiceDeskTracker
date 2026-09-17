from django.conf import settings


def tracker_settings(request):
    return {
        "auto_refresh_minutes": settings.AUTO_REFRESH_MINUTES,
        "data_source_label": "IT Service Desk",
    }
