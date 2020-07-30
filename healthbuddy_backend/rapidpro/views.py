from datetime import date
import requests
from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Flow, DailyFlowRuns
from .rapidpro import ProxyRapidPro
from .serializers import FlowSerializer


class RapidProProxyView(ListAPIView):
    """
    Endpoint to transforms the current request into a RapidPro request
    """

    def get(self, request, *args, **kwargs):
        resource: str = kwargs.get("resource")
        proxy = ProxyRapidPro(request)
        response: requests.models.Response = proxy.make_request(resource)

        try:
            data = response.json()
        except Exception as e:
            data = {"message": "An error has occurred!", "error": str(e)}

        return Response(data=data, status=response.status_code)


class FlowViewSet(viewsets.ModelViewSet):
    serializer_class = FlowSerializer
    queryset = Flow.objects.all()
    filterset_fields = ["uuid", "name"]
    search_fields = ["uuid", "name"]
    ordering_fields = ["uuid", "name"]
    http_method_names = ["get", "post", "delete"]


class RunsDataListView(APIView):
    def _get_filters(self, query_params={}):
        filters = {}

        start_date = query_params.get("start_date", "2000-01-01")
        end_date = query_params.get("end_date", "2999-01-01")
        filters["day__range"] = [
            start_date,
            end_date
        ]

        flow = query_params.get("flow")
        if flow:
            filters["flow__uuid"] = flow

        return filters

    def get(self, request):
        query_params = request.query_params
        filters = self._get_filters(query_params)
        runs_data = DailyFlowRuns.objects.all().filter(**filters)
        sum_results = runs_data.aggregate(
            active=Sum("active"),
            completed=Sum("completed"),
            interrupted=Sum("interrupted"),
            expired=Sum("expired")
        )

        return Response(sum_results, status=200)
