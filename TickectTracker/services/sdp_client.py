"""
Client for ManageEngine ServiceDesk Plus's REST API (v3): pulls requests
matching our configured templates, and looks a single request up live by ID.

Adapted from the working sdp_spool_by_template.py script — same pagination
approach (list_info + search_criteria on template.id, passed as a URL query
param named input_data), just reading its configuration from settings/.env
instead of module-level constants.
"""
import json
import re
from html import unescape
from html.parser import HTMLParser

import requests
from django.conf import settings

from .exceptions import DataSourceError

ROW_COUNT = 100  # max allowed per page by the API

# fields_required REPLACES the list endpoint's default field set rather than
# adding to it, so every field the sync needs from the bulk call has to be
# listed explicitly. Confirmed by testing against the live API: this gets us
# approval_status, sla, assigned_time and resolved_time all in bulk — only
# udf_fields (where the approver emails live) stays empty here regardless;
# that only ever populates on the single-record detail endpoint (see
# fetch_request_by_id). is_overdue is deliberately not requested — the sync
# computes its own overdue flag from assigned_time + the template's SLA
# window rather than trusting ServiceDesk Plus's due_by_time-based one.
LIST_FIELDS_REQUIRED = [
    "id", "subject", "status", "technician", "requester", "template",
    "created_time", "due_by_time", "assigned_time", "resolved_time",
    "completed_time", "approval_status", "sla",
]


def _headers():
    return {
        "Accept": "application/vnd.manageengine.sdp.v3+json",
        "authtoken": settings.SDP_AUTH_TOKEN,
    }


def _require_config():
    if not settings.SDP_BASE_URL or not settings.SDP_AUTH_TOKEN:
        raise DataSourceError(
            "SDP_BASE_URL and SDP_AUTH_TOKEN must be set in .env to query ServiceDesk Plus."
        )


def _resolve_template_ids(template_ids):
    template_ids = template_ids if template_ids is not None else settings.SDP_TEMPLATE_IDS
    if not template_ids:
        raise DataSourceError("SDP_TEMPLATE_IDS is empty — set it in .env.")
    return template_ids


def _fetch_page(template_ids, row_count, start_index):
    input_data = {
        "list_info": {
            "row_count": row_count,
            "start_index": start_index,
            "get_total_count": True,
            "search_criteria": [
                {
                    "field": "template.id",
                    "condition": "is",
                    "values": template_ids,
                }
            ],
        },
        "fields_required": LIST_FIELDS_REQUIRED,
    }
    params = {"input_data": json.dumps(input_data)}

    try:
        response = requests.get(settings.SDP_BASE_URL, headers=_headers(), params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DataSourceError(f"ServiceDesk Plus request fetch failed: {exc}") from exc

    return response.json()


def fetch_sample(row_count=3, template_ids=None):
    """Fetch a single page, unpaginated — for a quick sanity/field-mapping check."""
    _require_config()
    template_ids = _resolve_template_ids(template_ids)
    return _fetch_page(template_ids, row_count, start_index=1)


def fetch_all_requests(template_ids=None, row_count=ROW_COUNT):
    """Page through /api/v3/requests filtered by template.id and return
    the full combined list of request records."""
    _require_config()
    template_ids = _resolve_template_ids(template_ids)

    all_requests = []
    start_index = 1
    has_more_rows = True

    while has_more_rows:
        payload = _fetch_page(template_ids, row_count, start_index)
        batch = payload.get("requests", [])
        all_requests.extend(batch)

        list_info = payload.get("list_info", {})
        has_more_rows = list_info.get("has_more_rows", False)
        start_index += row_count

    return all_requests


def fetch_request_by_id(request_id):
    """Live lookup of a single request by its ServiceDesk Plus ID."""
    _require_config()
    url = f"{settings.SDP_BASE_URL.rstrip('/')}/{request_id}"

    try:
        response = requests.get(url, headers=_headers(), timeout=30)
    except requests.RequestException as exc:
        raise DataSourceError(f"ServiceDesk Plus lookup failed: {exc}") from exc

    if response.status_code == 404:
        return None

    try:
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DataSourceError(f"ServiceDesk Plus lookup failed: {exc}") from exc

    payload = response.json()
    return payload.get("request", payload)


class _TextExtractor(HTMLParser):
    """Collects only the text content of an HTML fragment, tags dropped."""

    def __init__(self):
        super().__init__()
        self.chunks = []

    def handle_data(self, data):
        self.chunks.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in ("br", "p", "div", "tr", "li"):
            self.chunks.append("\n")


def _clean_html(value):
    """Strip tags/decode entities from an SDP rich-text field into plain text."""
    if not value:
        return ""
    parser = _TextExtractor()
    parser.feed(value)
    text = unescape("".join(parser.chunks))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def _get(data, *path):
    """Dig through nested dicts, returning None on any missing/None link."""
    current = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def build_lookup_sections(detail):
    """
    Curate a ServiceDesk Plus request detail into labeled sections for the
    live ID-lookup modal. Deliberately a whitelist, not a full dump — the
    raw object carries ~90 fields (image tokens, internal flags, etc.) most
    of which aren't meaningful to a viewer. Rich-text fields (description,
    resolution notes, closure comments) are HTML-stripped to plain text.

    approver_1/approver_2/approval_team read the same udf_sline_2401/2402/
    13201 fields as the sync — see models.py for the caveats on that
    mapping (user-identified, not API-documented).
    """
    udf = detail.get("udf_fields") or {}
    closure = detail.get("closure_info") or {}
    resolution = detail.get("resolution") or {}

    sections = [
        {
            "label": "Overview",
            "rows": [
                {"label": "Reference", "value": detail.get("id")},
                {"label": "Status", "value": _get(detail, "status", "name")},
                {"label": "Template", "value": _get(detail, "template", "name")},
                {"label": "Priority", "value": _get(detail, "priority", "name")},
                {"label": "Group", "value": _get(detail, "group", "name")},
                {"label": "Site", "value": _get(detail, "site", "name")},
            ],
        },
        {
            "label": "People",
            "rows": [
                {"label": "Requester", "value": _get(detail, "requester", "name")},
                {"label": "Requester Email", "value": _get(detail, "requester", "email_id")},
                {"label": "Technician", "value": _get(detail, "technician", "name")},
                {"label": "Technician Email", "value": _get(detail, "technician", "email_id")},
                {"label": "Approver 1", "value": udf.get("udf_sline_2401")},
                {"label": "Approver 2", "value": udf.get("udf_sline_2402")},
                {"label": "Team", "value": udf.get("udf_sline_13201")},
            ],
        },
        {
            "label": "SLA & Approval",
            "rows": [
                {"label": "SLA Policy", "value": _get(detail, "sla", "name") or _get(detail, "service_sla", "sla", "name")},
                {"label": "Approval Status", "value": _get(detail, "approval_status", "name")},
                {"label": "Created", "value": _get(detail, "created_time", "display_value")},
                {"label": "Due By", "value": _get(detail, "due_by_time", "display_value")},
                {"label": "Resolved", "value": _get(detail, "resolved_time", "display_value") or _get(detail, "completed_time", "display_value")},
                {"label": "Overdue", "value": "Yes" if detail.get("is_overdue") else "No"},
            ],
        },
        {
            "label": "Description",
            "rows": [
                {"label": "Subject", "value": detail.get("subject")},
                {"label": "Details", "value": _clean_html(detail.get("description") or detail.get("short_description")), "block": True},
            ],
        },
        {
            "label": "Resolution",
            "rows": [
                {"label": "Notes", "value": _clean_html(resolution.get("content")), "block": True},
                {"label": "Submitted By", "value": _get(resolution, "submitted_by", "name")},
                {"label": "Submitted On", "value": _get(resolution, "submitted_on", "display_value")},
            ],
        },
        {
            "label": "Closure",
            "rows": [
                {"label": "Closure Code", "value": _get(closure, "closure_code", "name")},
                {"label": "Closure Comments", "value": _clean_html(closure.get("closure_comments")), "block": True},
                {"label": "Requester Acknowledgement", "value": _clean_html(closure.get("requester_ack_comments")), "block": True},
            ],
        },
    ]

    for section in sections:
        section["rows"] = [row for row in section["rows"] if row.get("value")]

    return [section for section in sections if section["rows"]]
