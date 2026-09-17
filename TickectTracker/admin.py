from django.contrib import admin

from .models import SyncLog, Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "reference_id", "system_name", "technician", "responsible_person",
        "status", "is_overdue", "sla_due_at", "elapsed_days", "sla_met", "last_synced_at",
    )
    list_filter = ("status", "sla_met", "is_overdue", "technician")
    search_fields = ("reference_id", "system_name", "technician", "responsible_person")


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ("started_at", "success", "triggered_by", "rows_read", "tickets_created", "tickets_updated")
    list_filter = ("success", "triggered_by")
