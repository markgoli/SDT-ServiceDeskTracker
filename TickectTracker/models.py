from django.db import models
from django.db.models import Q
from django.utils import timezone

DEFAULT_STATUS_COLOR = "#707070"

TERMINAL_KEYWORDS = ("closed", "resolved")
CANCEL_KEYWORDS = ("cancel",)


def is_cancelled_status(name):
    name = (name or "").lower()
    return any(k in name for k in CANCEL_KEYWORDS)


def is_terminal_status(name):
    return is_cancelled_status(name) or any(k in (name or "").lower() for k in TERMINAL_KEYWORDS)

TERMINAL_Q = Q(status__icontains="closed") | Q(status__icontains="resolved") | Q(status__icontains="cancel")
CANCELLED_Q = Q(status__icontains="cancel")
OPEN_Q = ~TERMINAL_Q
def is_business_day(dt):
    from django.conf import settings
    if dt.weekday() >= 5:
        return False
    return dt.date() not in settings.SDP_HOLIDAYS


def add_business_days(start, n):
    """Advance `start` by n business days, skipping weekends/holidays."""
    current = start
    remaining = n
    while remaining > 0:
        current += timezone.timedelta(days=1)
        if is_business_day(current):
            remaining -= 1
    return current


def business_days_between(start, end):
    """Count business days elapsed from start to end. 0 if end <= start."""
    if end <= start:
        return 0
    current = start
    count = 0
    while current < end:
        current += timezone.timedelta(days=1)
        if is_business_day(current):
            count += 1
    return count


class Ticket(models.Model):

    reference_id = models.CharField(max_length=100, unique=True, help_text="ServiceDesk Plus request ID.")
    system_name = models.CharField(max_length=500, help_text="Request subject.")
    technician = models.CharField(max_length=255, blank=True)
    responsible_person = models.CharField(max_length=255, blank=True, help_text="Requester name.")
    template_name = models.CharField(max_length=255, blank=True)
    template_id = models.CharField(max_length=50, blank=True, help_text="Used to look up the SLA day-window.")

    status = models.CharField(max_length=100, help_text="Raw status.name from ServiceDesk Plus.")
    status_color = models.CharField(max_length=20, blank=True, help_text="Raw status.color from ServiceDesk Plus.")
    sla_policy_name = models.CharField(max_length=255, blank=True, help_text="Applied SLA policy name.")

    created_at = models.DateTimeField(null=True, blank=True, help_text="ServiceDesk Plus created_time.")
    assigned_at = models.DateTimeField(null=True, blank=True, help_text="ServiceDesk Plus assigned_time — the SLA clock start.")
    sla_due_at = models.DateTimeField(null=True, blank=True, help_text="ServiceDesk Plus due_by_time — display only, not used for compliance.")
    is_overdue = models.BooleanField(default=False, help_text="Computed from assigned_at + the template's SLA window, refreshed each sync.")

    closed_at = models.DateTimeField(null=True, blank=True)

    approval_status = models.CharField(max_length=50, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    approver_1 = models.CharField(max_length=255, blank=True, help_text="udf_sline_2401.")
    approver_2 = models.CharField(max_length=255, blank=True, help_text="udf_sline_2402.")
    approval_team = models.CharField(max_length=255, blank=True, help_text="udf_sline_13201 — meaning inferred.")

    detail_synced = models.BooleanField(default=False)

    elapsed_days = models.IntegerField(null=True, blank=True)
    sla_met = models.BooleanField(null=True, blank=True)

    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_synced_at"]

    def __str__(self):
        return f"{self.reference_id} — {self.system_name} ({self.status})"

    SLA_STATE_LABELS = {
        "not_applicable": "Not Applicable",
        "unknown": "Unknown",
        "within_sla": "Within SLA",
        "breached": "Breached",
        "overdue": "Overdue",
        "on_track": "On Track",
    }

    @property
    def is_cancelled(self):
        return is_cancelled_status(self.status)

    @property
    def is_terminal(self):
        return is_terminal_status(self.status)

    @property
    def status_hex(self):
        return self.status_color or DEFAULT_STATUS_COLOR

    @property
    def status_badge_bg(self):
        """A soft, ~14%-alpha tint of the ticket's own status color for badge backgrounds."""
        hex_color = self.status_hex.lstrip("#")
        if len(hex_color) != 6:
            return "rgba(102, 112, 133, 0.14)"
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, 0.14)"

    @property
    def sla_state(self):
        """A single label the UI can key colors/badges off of."""
        if self.is_cancelled:
            return "not_applicable"
        if self.is_terminal:
            if self.sla_met is None:
                return "unknown"
            return "within_sla" if self.sla_met else "breached"
        return "overdue" if self.is_overdue else "on_track"

    @property
    def sla_state_display(self):
        return self.SLA_STATE_LABELS.get(self.sla_state, self.sla_state)

    @property
    def days_open(self):
        """Business days elapsed since assignment, live for open tickets, persisted once closed. None if not yet assigned — the SLA clock hasn't started."""
        if not self.is_terminal and self.assigned_at:
            return business_days_between(self.assigned_at, timezone.now())
        return self.elapsed_days

    @property
    def is_approved(self):
        return (self.approval_status or "").lower() == "approved"

    @property
    def is_denied(self):
        return (self.approval_status or "").lower() == "denied"

    @property
    def days_to_approval(self):
        if self.approved_at and self.created_at:
            return (self.approved_at - self.created_at).days
        return None

    @property
    def sla_target_days(self):
        """The fixed SLA day-window for this request's template (settings.SDP_TEMPLATE_SLA_DAYS)."""
        from django.conf import settings
        return settings.SDP_TEMPLATE_SLA_DAYS.get(self.template_id)

    @property
    def calculated_due_at(self):
        """Our own SLA deadline: assigned_at + the template's fixed business-day window. None until assigned."""
        if self.assigned_at and self.sla_target_days is not None:
            return add_business_days(self.assigned_at, self.sla_target_days)
        return None


class SyncLog(models.Model):
    """History of attempts to pull requests from ServiceDesk Plus."""

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    success = models.BooleanField(default=False)
    message = models.CharField(max_length=500, blank=True)
    rows_read = models.PositiveIntegerField(default=0)
    tickets_created = models.PositiveIntegerField(default=0)
    tickets_updated = models.PositiveIntegerField(default=0)
    triggered_by = models.CharField(
        max_length=20,
        choices=[("manual", "Manual"), ("scheduled", "Scheduled"), ("startup", "Startup")],
        default="manual",
    )

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        status = "OK" if self.success else "FAILED"
        return f"Sync {self.started_at:%Y-%m-%d %H:%M} [{status}]"
