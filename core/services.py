from django.db.models import Avg, Count
from datetime import date, timedelta
from bids.models import Bid, BidStatus
from contracts.models import Contract, ContractStatus
from projects.models import Project, ProjectStatus
from reviews.models import Review




from django.db.models.functions import TruncDate
from django.utils import timezone




def get_client_dashboard_data(user):


    projects = Project.objects.filter(client=user)
    contracts = Contract.objects.filter(client=user)
    written_reviews = Review.objects.filter(client=user)

    data = {
        "role": "client",
        "projects": {
            "total": projects.count(),
            "open": projects.filter(status=ProjectStatus.OPEN).count(),
            "in_progress": projects.filter(status=ProjectStatus.IN_PROGRESS).count(),
            "completed": projects.filter(status=ProjectStatus.COMPLETED).count(),
            "cancelled": projects.filter(status=ProjectStatus.CANCELLED).count(),
        },
        "contracts": {
            "total": contracts.count(),
            "active": contracts.filter(status=ContractStatus.ACTIVE).count(),
            "finished": contracts.filter(status=ContractStatus.FINISHED).count(),
            "cancelled": contracts.filter(status=ContractStatus.CANCELLED).count(),
        },
        "reviews": {
            "written": written_reviews.count(),
        },
        "recent_projects": projects.select_related("client")[:5],
        "recent_contracts": contracts.select_related(
            "project",
            "client",
            "freelancer",
        )[:5],
    }

    return data


def get_freelancer_dashboard_data(user):


    bids = Bid.objects.filter(freelancer=user)
    contracts = Contract.objects.filter(freelancer=user)
    received_reviews = Review.objects.filter(freelancer=user)

    average_rating = received_reviews.aggregate(avg_rating=Avg("rating"))["avg_rating"]

    data = {
        "role": "freelancer",
        "bids": {
            "total": bids.count(),
            "pending": bids.filter(status=BidStatus.PENDING).count(),
            "accepted": bids.filter(status=BidStatus.ACCEPTED).count(),
            "rejected": bids.filter(status=BidStatus.REJECTED).count(),
            "withdrawn": bids.filter(status=BidStatus.WITHDRAWN).count(),
        },
        "contracts": {
            "total": contracts.count(),
            "active": contracts.filter(status=ContractStatus.ACTIVE).count(),
            "finished": contracts.filter(status=ContractStatus.FINISHED).count(),
            "cancelled": contracts.filter(status=ContractStatus.CANCELLED).count(),
        },
        "reviews": {
            "received": received_reviews.count(),
            "average_rating": round(average_rating, 2) if average_rating is not None else None,
        },
        "recent_bids": bids.select_related(
            "project",
            "freelancer",
            "project__client",
        )[:5],
        "recent_contracts": contracts.select_related(
            "project",
            "client",
            "freelancer",
        )[:5],
    }

    return data


def get_dashboard_data(user):


    if not user.is_authenticated:
        return None

    if getattr(user, "is_client", False):
        return get_client_dashboard_data(user)

    if getattr(user, "is_freelancer", False):
        return get_freelancer_dashboard_data(user)

    return {
        "role": None,
        "projects": {},
        "bids": {},
        "contracts": {},
        "reviews": {},
    }


def _get_period_range(period: str):

    today = timezone.localdate()

    if period == "week":
        start_date = today - timedelta(days=6)
        end_date = today
        return start_date, end_date

    if period == "month":
        start_date = today - timedelta(days=29)
        end_date = today
        return start_date, end_date

    if period == "last_month":
        first_day_this_month = today.replace(day=1)
        end_date = first_day_this_month - timedelta(days=1)
        start_date = end_date.replace(day=1)
        return start_date, end_date

    start_date = today - timedelta(days=6)
    end_date = today
    return start_date, end_date


def _build_daily_series(queryset, start_date: date, end_date: date):

    rows = (
        queryset.filter(created_at__date__range=(start_date, end_date))
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    counts_by_day = {row["day"]: row["count"] for row in rows}

    labels = []
    values = []

    current_day = start_date
    while current_day <= end_date:
        labels.append(current_day.strftime("%d %b"))
        values.append(counts_by_day.get(current_day, 0))
        current_day += timedelta(days=1)

    return labels, values


def get_activity_chart_data(user, period: str = "week"):

    if not user.is_authenticated:
        return {
            "period": period,
            "metric": None,
            "label": "",
            "labels": [],
            "values": [],
            "total": 0,
        }

    start_date, end_date = _get_period_range(period)

    if getattr(user, "is_client", False):
        queryset = Project.objects.filter(client=user)
        labels, values = _build_daily_series(queryset, start_date, end_date)

        return {
            "period": period,
            "metric": "projects",
            "label": "Созданные проекты",
            "labels": labels,
            "values": values,
            "total": sum(values),
            "start_date": start_date,
            "end_date": end_date,
        }

    if getattr(user, "is_freelancer", False):
        queryset = Bid.objects.filter(freelancer=user)
        labels, values = _build_daily_series(queryset, start_date, end_date)

        return {
            "period": period,
            "metric": "bids",
            "label": "Отправленные отклики",
            "labels": labels,
            "values": values,
            "total": sum(values),
            "start_date": start_date,
            "end_date": end_date,
        }

    return {
        "period": period,
        "metric": None,
        "label": "",
        "labels": [],
        "values": [],
        "total": 0,
        "start_date": start_date,
        "end_date": end_date,
    }