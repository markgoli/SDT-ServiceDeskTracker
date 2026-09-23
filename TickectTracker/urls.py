from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("tickets/", views.TicketListView.as_view(), name="ticket_list"),
    path("technicians/", views.TechnicianPerformanceView.as_view(), name="technician_performance"),
    path("refresh/", views.RefreshDataView.as_view(), name="refresh"),
    path("lookup/", views.RequestLookupView.as_view(), name="request_lookup"),
]
