
from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.utils import timezone

from ..models import SyncLog, Ticket, business_days_between
from .exceptions import DataSourceError
from .sdp_client import fetch_all_requests, fetch_request_by_id


def _parse_epoch_ms(value):
    if value in (None, ""):
        return None
    try:
        ms = int(value)
    except (TypeError, ValueError):
        return None
    return datetime.fromtimestamp(ms / 1000, tz=dt_timezone.utc)


def _compute_is_overdue(ticket):
    """Live overdue flag for open tickets — our own rule, not the API's."""
    if ticket.is_terminal or not ticket.assigned_at:
        return False
    threshold = settings.SDP_TEMPLATE_SLA_DAYS.get(ticket.template_id)
    if threshold is None:
        return False
    return business_days_between(ticket.assigned_at, timezone.now()) > threshold


def _apply_sla(ticket, raw):
    """assigned_at -> closed_at duration vs. the template's fixed SLA window."""
    resolved_at = (
        _parse_epoch_ms((raw.get("resolved_time") or {}).get("value"))
        or _parse_epoch_ms((raw.get("completed_time") or {}).get("value"))
    )

    if ticket.is_terminal:
        if resolved_at:
            ticket.closed_at = resolved_at
        elif ticket.closed_at is None:
            # No real resolution timestamp (typical for a cancelled request)
            # — fall back to when we first observed the terminal transition.
            ticket.closed_at = timezone.now()

        if ticket.is_cancelled or not resolved_at or not ticket.assigned_at:
            ticket.elapsed_days = None
            ticket.sla_met = None
        else:
            elapsed = business_days_between(ticket.assigned_at, resolved_at)
            ticket.elapsed_days = elapsed
            threshold = settings.SDP_TEMPLATE_SLA_DAYS.get(ticket.template_id)
            ticket.sla_met = elapsed <= threshold if threshold is not None else None
    else:
        # Covers the rare case of a ticket reopening after being closed.
        ticket.closed_at = None
        ticket.elapsed_days = None
        ticket.sla_met = None


def _apply_list_fields(ticket, raw):
    """Everything the enriched bulk list call gives us — cheap, every sync."""
    status_obj = raw.get("status") or {}
    technician_obj = raw.get("technician") or {}
    requester_obj = raw.get("requester") or {}
    template_obj = raw.get("template") or {}
    approval_obj = raw.get("approval_status") or {}
    sla_obj = raw.get("sla") or {}

    ticket.system_name = raw.get("subject") or "(no subject)"
    ticket.technician = technician_obj.get("name") or ""
    ticket.responsible_person = requester_obj.get("name") or ""
    ticket.template_name = template_obj.get("name") or ""
    ticket.template_id = str(template_obj.get("id") or "")
    ticket.status = (status_obj.get("name") or "").strip() or "Unknown"
    ticket.status_color = (status_obj.get("color") or "").strip()

    created_at = _parse_epoch_ms((raw.get("created_time") or {}).get("value"))
    if created_at:
        ticket.created_at = created_at
    ticket.assigned_at = _parse_epoch_ms((raw.get("assigned_time") or {}).get("value"))
    ticket.sla_due_at = _parse_epoch_ms((raw.get("due_by_time") or {}).get("value"))

    sla_policy_name = sla_obj.get("name") or ""
    if sla_policy_name:
        ticket.sla_policy_name = sla_policy_name

    new_approval_status = (approval_obj.get("name") or "").strip()
    if new_approval_status:
        if new_approval_status.lower() == "approved" and ticket.approval_status.lower() != "approved":
            ticket.approved_at = ticket.approved_at or timezone.now()
        ticket.approval_status = new_approval_status

    _apply_sla(ticket, raw)
    ticket.is_overdue = _compute_is_overdue(ticket)


def _apply_detail_fields(ticket, detail):
    """Only available via the per-request detail call: the approver UDF fields."""
    udf_fields = detail.get("udf_fields") or {}
    ticket.approver_1 = udf_fields.get("udf_sline_2401") or ticket.approver_1
    ticket.approver_2 = udf_fields.get("udf_sline_2402") or ticket.approver_2
    ticket.approval_team = udf_fields.get("udf_sline_13201") or ticket.approval_team


def sync_tickets(triggered_by: str = "manual") -> SyncLog:
    log = SyncLog.objects.create(triggered_by=triggered_by)

    try:
        raw_requests = fetch_all_requests()
    except DataSourceError as exc:
        log.success = False
        log.message = str(exc)
        log.finished_at = timezone.now()
        log.save()
        return log

    created = updated = 0
    detail_errors = []

    for raw in raw_requests:
        ref = str(raw.get("id") or "").strip()
        if not ref:
            continue

        ticket = Ticket.objects.filter(reference_id=ref).first()
        is_new = ticket is None
        if is_new:
            ticket = Ticket(reference_id=ref)

        needs_detail = is_new or not ticket.detail_synced

        _apply_list_fields(ticket, raw)

        if needs_detail:
            try:
                detail = fetch_request_by_id(ref) or {}
                ticket.detail_synced = True
            except DataSourceError as exc:
                detail = {}
                detail_errors.append(f"{ref}: {exc}")

            if detail:
                _apply_detail_fields(ticket, detail)

        ticket.save()
        if is_new:
            created += 1
        else:
            updated += 1

    log.rows_read = len(raw_requests)
    log.tickets_created = created
    log.tickets_updated = updated
    log.success = True
    log.message = "OK" if not detail_errors else "; ".join(detail_errors[:5])
    log.finished_at = timezone.now()
    log.save()
    return log
