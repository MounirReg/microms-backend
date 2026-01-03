from django_filters import rest_framework as filters
from domain.models import Order

class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass

class OrderFilter(filters.FilterSet):
    status__in = CharInFilter(field_name='status', lookup_expr='in')
    
    status = filters.ChoiceFilter(choices=Order.Status.choices)

    class Meta:
        model = Order
        fields = ['status', 'reference']
