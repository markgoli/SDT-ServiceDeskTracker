from django.conf import settings
from django.urls import reverse


def tracker_settings(request):
    return {
        "auto_refresh_minutes": settings.AUTO_REFRESH_MINUTES,
        "data_source_label": "IT Service Desk",
        "app_config": {
            "refreshUrl": reverse("tracker:refresh"),
            "requestLookupUrl": reverse("tracker:request_lookup"),
            "autoRefreshMinutes": settings.AUTO_REFRESH_MINUTES,
        },
    }
