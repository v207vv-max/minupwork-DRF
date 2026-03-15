from decimal import Decimal, InvalidOperation
from datetime import datetime

from django.db.models import Q

from .models import Project, ProjectStatus


PROJECT_ORDERING_CHOICES = {
    "newest": "-created_at",
    "oldest": "created_at",
    "budget_asc": "budget",
    "budget_desc": "-budget",
    "deadline_asc": "deadline",
    "deadline_desc": "-deadline",
}


def get_project_list_queryset():

    return Project.objects.select_related("client").filter(is_active=True)


def filter_projects(queryset, params):


    q = (params.get("q") or "").strip()
    status = (params.get("status") or "").strip()
    min_budget = (params.get("min_budget") or "").strip()
    max_budget = (params.get("max_budget") or "").strip()
    deadline_from = (params.get("deadline_from") or "").strip()
    deadline_to = (params.get("deadline_to") or "").strip()
    ordering = (params.get("ordering") or "").strip()
    is_active = (params.get("is_active") or "").strip().lower()

    if q:
        queryset = queryset.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(skills_required__icontains=q)
            | Q(client__username__icontains=q)
        )

    valid_statuses = {choice[0] for choice in ProjectStatus.choices}
    if status in valid_statuses:
        queryset = queryset.filter(status=status)

    if is_active in {"true", "false"}:
        queryset = queryset.filter(is_active=(is_active == "true"))

    if min_budget:
        try:
            queryset = queryset.filter(budget__gte=Decimal(min_budget))
        except (InvalidOperation, ValueError):
            pass

    if max_budget:
        try:
            queryset = queryset.filter(budget__lte=Decimal(max_budget))
        except (InvalidOperation, ValueError):
            pass

    if deadline_from:
        try:
            parsed_deadline_from = datetime.strptime(deadline_from, "%Y-%m-%d").date()
            queryset = queryset.filter(deadline__gte=parsed_deadline_from)
        except ValueError:
            pass

    if deadline_to:
        try:
            parsed_deadline_to = datetime.strptime(deadline_to, "%Y-%m-%d").date()
            queryset = queryset.filter(deadline__lte=parsed_deadline_to)
        except ValueError:
            pass

    queryset = queryset.order_by(PROJECT_ORDERING_CHOICES.get(ordering, "-created_at"))

    return queryset
