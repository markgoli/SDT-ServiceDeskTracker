"""
Seeds the database with realistic demo Ticket rows (spread across several
months) so the dashboard has meaningful history to visualize without
needing a live ServiceDesk Plus connection.

Usage:
    python manage.py generate_sample_data
    python manage.py generate_sample_data --count 150 --clear
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from TickectTracker.models import Ticket

SYSTEMS = [
    "Core Banking Platform", "Payroll System", "Customer CRM", "HR Portal",
    "Email Gateway", "Inventory Management", "Field Service App",
    "Enterprise Data Warehouse", "VPN Gateway", "Identity Provider",
    "IT Service Desk Portal", "Procurement Portal", "Billing Engine",
    "Mobile Banking App", "Web Application Firewall", "SharePoint Intranet",
    "ERP System", "Business Intelligence Suite", "API Gateway",
    "Document Management System", "Point of Sale System", "Fraud Detection Engine",
    "Card Management System", "Treasury Management System", "Loan Origination System",
]

TECHNICIANS = [
    "Amina Yusuf", "Brian Otieno", "Cynthia Wanjiru", "David Mwangi",
    "Grace Achieng", "Kevin Kiptoo", "Linda Njeri", "Peter Kamau",
]

REQUESTERS = [
    "Faith Muthoni", "James Njoroge", "Mercy Adhiambo", "Samuel Ochieng",
    "Ruth Wambui", "Tom Odhiambo", "Winnie Chebet", "Daniel Karanja",
]

TEMPLATES = [
    "Request for Initial (New) Security Assessment",
    "Request for Security Assessment Revalidation",
]

# (status name, status color, weight) — mirrors ServiceDesk Plus's own
# status vocabulary/colors rather than an invented one.
STATUS_WEIGHTS = [
    ("Open", "#0066ff", 18),
    ("On Hold", "#f5a623", 8),
    ("Resolved", "#1fae5e", 47),
    ("Closed", "#1fae5e", 47),
    ("Cancelled", "", 12),
]

SLA_WINDOW_DAYS = [5, 10, 15, 20, 30]

SLA_POLICIES = [
    "Information Security Assurance_P2",
    "Information Security Assurance_P3",
    "Information Security Assurance_P4",
]


class Command(BaseCommand):
    help = "Seed the database with sample Ticket rows for local dashboard testing."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=120, help="Number of tickets to generate.")
        parser.add_argument("--clear", action="store_true", help="Delete existing tickets first.")

    def handle(self, *args, **options):
        count = options["count"]

        if options["clear"]:
            deleted, _ = Ticket.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} existing ticket(s)."))

        now = timezone.now()
        tickets = []

        status_pool = []
        for name, color, weight in STATUS_WEIGHTS:
            status_pool.extend([(name, color)] * weight)

        for i in range(1, count + 1):
            ref = str(1020000 + i)
            system_name = f"Request for Security Assessment — {random.choice(SYSTEMS)}"
            technician = random.choice(TECHNICIANS)
            requester = random.choice(REQUESTERS)
            template_name = random.choice(TEMPLATES)
            status_name, status_color = random.choice(status_pool)
            sla_window = random.choice(SLA_WINDOW_DAYS)

            created_at = now - timedelta(days=random.randint(1, 210))
            sla_due_at = created_at + timedelta(days=sla_window)

            is_terminal = status_name in ("Resolved", "Closed", "Cancelled")
            is_cancelled = status_name == "Cancelled"

            closed_at = None
            elapsed_days = None
            sla_met = None
            is_overdue = False

            if is_terminal:
                if is_cancelled:
                    closed_at = created_at + timedelta(days=random.randint(0, 3))
                else:
                    within_sla = random.random() < 0.7
                    elapsed = (
                        random.randint(1, sla_window)
                        if within_sla
                        else sla_window + random.randint(1, 15)
                    )
                    closed_at = created_at + timedelta(days=elapsed)
                    elapsed_days = elapsed
                    sla_met = elapsed <= sla_window
            else:
                is_overdue = timezone.now() > sla_due_at

            approval_status = ""
            approved_at = None
            if is_cancelled:
                approval_status = random.choice(["Denied", ""])
            elif status_name in ("Resolved", "Closed"):
                approval_status = "Approved"
                approved_at = created_at + timedelta(days=random.randint(1, 3))
            else:  # Open / On Hold
                if random.random() < 0.6:
                    approval_status = "Approved"
                    approved_at = created_at + timedelta(days=random.randint(1, 3))

            tickets.append(Ticket(
                reference_id=ref,
                system_name=system_name,
                technician=technician,
                responsible_person=requester,
                template_name=template_name,
                sla_policy_name=random.choice(SLA_POLICIES),
                status=status_name,
                status_color=status_color,
                created_at=created_at,
                sla_due_at=sla_due_at,
                is_overdue=is_overdue,
                closed_at=closed_at,
                elapsed_days=elapsed_days,
                sla_met=sla_met,
                approval_status=approval_status,
                approved_at=approved_at,
            ))

        Ticket.objects.bulk_create(tickets, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(tickets)} sample Ticket row(s) in the database."
        ))
