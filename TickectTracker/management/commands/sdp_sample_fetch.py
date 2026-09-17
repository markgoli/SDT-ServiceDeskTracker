"""
One-off inspection tool: fetches a small, unpaginated sample of requests
from ServiceDesk Plus and saves the raw JSON locally, so we can see this
instance's actual field names (including custom template fields) before
wiring up the real Ticket sync.

Your SDP_AUTH_TOKEN stays in .env — this never prints it or sends it
anywhere else.

Usage:
    python manage.py sdp_sample_fetch
    python manage.py sdp_sample_fetch --count 3 --out sample_data/sdp_sample.json
"""
import json

from django.core.management.base import BaseCommand

from TickectTracker.services.exceptions import DataSourceError
from TickectTracker.services.sdp_client import fetch_sample


class Command(BaseCommand):
    help = "Fetch a small sample of ServiceDesk Plus requests for field-mapping inspection."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=3, help="Number of requests to fetch.")
        parser.add_argument(
            "--out", type=str, default="sample_data/sdp_sample_response.json",
            help="Where to save the raw JSON response.",
        )

    def handle(self, *args, **options):
        try:
            payload = fetch_sample(row_count=options["count"])
        except DataSourceError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return

        out_path = options["out"]
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        total = payload.get("list_info", {}).get("total_count")
        fetched = len(payload.get("requests", []))
        self.stdout.write(self.style.SUCCESS(
            f"Fetched {fetched} request(s) (total matching: {total}).\n"
            f"Saved to {out_path} — share that file's contents so we can map its fields."
        ))
