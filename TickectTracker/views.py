from datetime import timedelta

from django.db.models import Avg, Count, F, Max, Min, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView

from .models import CANCELLED_Q, DEFAULT_STATUS_COLOR, OPEN_Q, TERMINAL_Q, SyncLog, Ticket, is_terminal_status
from .services.exceptions import DataSourceError
from .services.sdp_client import build_lookup_sections, fetch_request_by_id
from .services.sync import sync_tickets


def _latest_sync():
    return SyncLog.objects.first()


class DashboardView(TemplateView):
    template_name = "landing.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        tickets = Ticket.objects.all()
        total = tickets.count()

        open_qs = tickets.filter(OPEN_Q)
        closed_qs = tickets.filter(TERMINAL_Q).exclude(CANCELLED_Q)
        cancelled_count = tickets.filter(CANCELLED_Q).count()
        overdue_count = open_qs.filter(is_overdue=True).count()
        on_track_count = open_qs.filter(is_overdue=False).count()
        closed_count = closed_qs.count()

        closed_sla = closed_qs.aggregate(
            within=Count("id", filter=Q(sla_met=True)),
            outside=Count("id", filter=Q(sla_met=False)),
            unknown=Count("id", filter=Q(sla_met__isnull=True)),
        )
        compliance_rate = (
            round(closed_sla["within"] / (closed_sla["within"] + closed_sla["outside"]) * 100, 1)
            if (closed_sla["within"] + closed_sla["outside"]) > 0
            else None
        )

        technician_load = (
            open_qs.values("technician")
            .annotate(count=Count("id"))
            .order_by("-count")[:8]
        )

        status_rows = (
            tickets.values("status", "status_color")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        six_months_ago = timezone.now() - timezone.timedelta(days=180)
        monthly_trend = (
            closed_qs.filter(closed_at__gte=six_months_ago)
            .annotate(month=TruncMonth("closed_at"))
            .values("month")
            .annotate(
                within=Count("id", filter=Q(sla_met=True)),
                outside=Count("id", filter=Q(sla_met=False)),
            )
            .order_by("month")
        )

        # Closed/Resolved and On Hold statuses use our own house colors
        # (matching the green/red used on the SLA charts) instead of
        # ServiceDesk Plus's raw status.color, so they read as the same
        # color everywhere on the dashboard rather than whatever shade
        # this SDP instance happens to be configured with.
        def _status_color(status_name):
            name = status_name.lower()
            if is_terminal_status(status_name) and "cancel" not in name:
                return "#1fae5e"
            if "hold" in name:
                return "#f0453a"
            return None

        status_chart = {
            "labels": [row["status"] for row in status_rows],
            "data": [row["count"] for row in status_rows],
            "colors": [
                _status_color(row["status"]) or row["status_color"] or DEFAULT_STATUS_COLOR
                for row in status_rows
            ],
        }

        sla_chart = {
            "labels": ["Within SLA", "Outside SLA"] + (["Unknown"] if closed_sla["unknown"] else []),
            "data": [closed_sla["within"], closed_sla["outside"]] + (
                [closed_sla["unknown"]] if closed_sla["unknown"] else []
            ),
            "colors": ["#1fae5e", "#f0453a", "#8a93a6"],
        }

        monthly_chart = {
            "labels": [row["month"].strftime("%b %Y") for row in monthly_trend],
            "within": [row["within"] for row in monthly_trend],
            "outside": [row["outside"] for row in monthly_trend],
        }

        workload_tickets = []
        for row in technician_load:
            tech_tickets = list(
                open_qs.filter(technician=row["technician"])
                .values("reference_id", "system_name")
                .order_by("-last_synced_at")[:25]
            )
            workload_tickets.append([
                {"ref": t["reference_id"], "system": t["system_name"]} for t in tech_tickets
            ])

        workload_chart = {
            "labels": [row["technician"] or "Unassigned" for row in technician_load],
            "data": [row["count"] for row in technician_load],
            "tickets": workload_tickets,
        }

        sla_turnaround = closed_qs.aggregate(
            best=Min("elapsed_days"), worst=Max("elapsed_days"), avg=Avg("elapsed_days")
        )
        if sla_turnaround["avg"] is not None:
            sla_turnaround["avg"] = round(sla_turnaround["avg"], 1)

        now = timezone.now()
        start_of_week = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        week_days = [start_of_week + timedelta(days=i) for i in range(7)]
        weekly_rows = (
            closed_qs.filter(closed_at__gte=start_of_week, closed_at__lt=start_of_week + timedelta(days=7))
            .annotate(day=TruncDate("closed_at"))
            .values("day")
            .annotate(within=Count("id", filter=Q(sla_met=True)), outside=Count("id", filter=Q(sla_met=False)))
        )
        weekly_by_day = {row["day"]: row for row in weekly_rows}
        weekly_chart = {
            "labels": [d.strftime("%a %d") for d in week_days],
            "within": [weekly_by_day.get(d.date(), {}).get("within", 0) for d in week_days],
            "outside": [weekly_by_day.get(d.date(), {}).get("outside", 0) for d in week_days],
        }

        technician_sla_rows = (
            closed_qs.exclude(technician="")
            .values("technician")
            .annotate(within=Count("id", filter=Q(sla_met=True)), outside=Count("id", filter=Q(sla_met=False)))
            .annotate(total_known=F("within") + F("outside"))
            .exclude(total_known=0)
            .order_by("-total_known")[:12]
        )
        technician_sla_chart = {
            "labels": [row["technician"] for row in technician_sla_rows],
            "within": [row["within"] for row in technician_sla_rows],
            "outside": [row["outside"] for row in technician_sla_rows],
        }

        open_tickets_table = [
            {
                "technician": row["technician"] or "Unassigned",
                "ref": row["reference_id"],
                "system": row["system_name"],
            }
            for row in open_qs.values("technician", "reference_id", "system_name").order_by("technician", "reference_id")
        ]

        # Only open tickets that have actually been assigned have a running
        # SLA clock (calculated_due_at is None otherwise) — these three
        # views only make sense for those.
        today_local = timezone.localdate()
        sla_lifetime_rows = []
        due_dates_rows = []
        due_today_rows = []

        for t in open_qs.filter(assigned_at__isnull=False):
            due_at = t.calculated_due_at
            if due_at is None:
                continue

            elapsed = (now - t.assigned_at).days
            threshold = t.sla_target_days
            within = min(elapsed, threshold)
            over = max(0, elapsed - threshold)
            sla_lifetime_rows.append({"ref": t.reference_id, "within": within, "over": over})

            due_local_date = timezone.localtime(due_at).date()
            days_until = (due_local_date - today_local).days
            due_dates_rows.append({
                "ref": t.reference_id,
                "days_until": days_until,
                "due_label": due_local_date.strftime("%b %d"),
            })

            if due_local_date == today_local:
                due_today_rows.append({
                    "ref": t.reference_id,
                    "technician": t.technician or "Unassigned",
                    "system": t.system_name,
                    "template_type": "Revalidation" if "revalidation" in t.template_name.lower() else "New Assessment",
                })

        sla_lifetime_rows.sort(key=lambda r: (r["over"], r["within"]), reverse=True)
        sla_lifetime_rows = sla_lifetime_rows[:30]
        sla_lifetime_chart = {
            "labels": [r["ref"] for r in sla_lifetime_rows],
            "within": [r["within"] for r in sla_lifetime_rows],
            "over": [r["over"] for r in sla_lifetime_rows],
        }

        due_dates_rows.sort(key=lambda r: r["days_until"])
        due_dates_rows = due_dates_rows[:30]
        due_dates_chart = {
            "labels": [r["ref"] for r in due_dates_rows],
            "data": [r["days_until"] for r in due_dates_rows],
            "due_labels": [r["due_label"] for r in due_dates_rows],
        }

        due_today_rows.sort(key=lambda r: r["technician"])

        technician_performance = (
            tickets.exclude(technician="")
            .values("technician")
            .annotate(
                open=Count("id", filter=OPEN_Q),
                closed=Count("id", filter=TERMINAL_Q & ~CANCELLED_Q),
                cancelled=Count("id", filter=CANCELLED_Q),
                total=Count("id"),
                avg_days=Avg("elapsed_days"),
                within=Count("id", filter=Q(sla_met=True)),
                outside=Count("id", filter=Q(sla_met=False)),
            )
            .order_by("-total")
        )
        technician_rows = []
        for row in technician_performance:
            closed_with_sla = row["within"] + row["outside"]
            technician_rows.append({
                **row,
                "avg_days": round(row["avg_days"], 1) if row["avg_days"] is not None else None,
                "compliance_rate": round(row["within"] / closed_with_sla * 100, 1) if closed_with_sla else None,
            })

        ctx.update({
            "total": total,
            "open_count": open_qs.count(),
            "overdue_count": overdue_count,
            "on_track_count": on_track_count,
            "closed_count": closed_count,
            "cancelled_count": cancelled_count,
            "closed_within_sla": closed_sla["within"],
            "closed_outside_sla": closed_sla["outside"],
            "closed_unknown_sla": closed_sla["unknown"],
            "compliance_rate": compliance_rate,
            "status_chart": status_chart,
            "sla_chart": sla_chart,
            "monthly_chart": monthly_chart,
            "weekly_chart": weekly_chart,
            "workload_chart": workload_chart,
            "technician_sla_chart": technician_sla_chart,
            "sla_lifetime_chart": sla_lifetime_chart,
            "due_dates_chart": due_dates_chart,
            "due_today_rows": due_today_rows,
            "sla_turnaround": sla_turnaround,
            "technician_rows": technician_rows,
            "open_tickets_table": open_tickets_table,
            "latest_sync": _latest_sync(),
        })
        return ctx


class TicketListView(ListView):
    model = Ticket
    template_name = "ticket_list.html"
    context_object_name = "tickets"
    paginate_by = 10

    def get_queryset(self):
        qs = Ticket.objects.all().order_by("-created_at")
        status = self.request.GET.get("status", "").strip()
        technician = self.request.GET.get("technician", "").strip()
        search = self.request.GET.get("q", "").strip()

        if status:
            qs = qs.filter(status=status)
        if technician:
            qs = qs.filter(technician=technician)
        if search:
            qs = qs.filter(
                Q(reference_id__icontains=search)
                | Q(system_name__icontains=search)
                | Q(technician__icontains=search)
                | Q(responsible_person__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "status_choices": Ticket.objects.values_list("status", flat=True).distinct().order_by("status"),
            "technicians": Ticket.objects.values_list("technician", flat=True).distinct().order_by("technician"),
            "current_status": self.request.GET.get("status", ""),
            "current_technician": self.request.GET.get("technician", ""),
            "current_search": self.request.GET.get("q", ""),
            "latest_sync": _latest_sync(),
        })
        return ctx


class RefreshDataView(View):
    """Manual/auto-refresh trigger: re-pulls from ServiceDesk Plus and re-syncs."""

    def post(self, request, *args, **kwargs):
        log = sync_tickets(triggered_by="manual")
        return JsonResponse({
            "success": log.success,
            "message": log.message,
            "rows_read": log.rows_read,
            "created": log.tickets_created,
            "updated": log.tickets_updated,
            "finished_at": log.finished_at.isoformat() if log.finished_at else None,
        }, status=200 if log.success else 502)


class RequestLookupView(View):
    """Live lookup of a single ServiceDesk Plus request by ID, straight from the API."""

    def get(self, request, *args, **kwargs):
        request_id = request.GET.get("id", "").strip()
        if not request_id:
            return JsonResponse({"success": False, "message": "Enter a request ID."}, status=400)

        try:
            data = fetch_request_by_id(request_id)
        except DataSourceError as exc:
            return JsonResponse({"success": False, "message": str(exc)}, status=502)

        if data is None:
            return JsonResponse(
                {"success": False, "message": f"No request found with ID {request_id}."},
                status=404,
            )

        return JsonResponse({
            "success": True,
            "request_id": request_id,
            "subject": data.get("subject") or "",
            "sections": build_lookup_sections(data),
        })
