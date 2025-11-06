# pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math

class PaginacionPersonalizada(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'per_page'  # Esto lo controlas desde la URL
    max_page_size = 100

    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        per_page = self.get_page_size(self.request)
        current_page = self.page.number
        total_pages = math.ceil(total_items / per_page)

        return Response({
            'total': total_items,
            'per_page': per_page,
            'current_page': current_page,
            'total_pages': total_pages,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })
