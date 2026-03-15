import django_filters

from .models import Contract


class ContractFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status")

    class Meta:
        model = Contract
        fields = ["status"]
