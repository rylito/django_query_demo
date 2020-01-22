from rest_framework.decorators import APIView
from rest_framework.response import Response
from tracer_assignment.models import *
from django.db.models import Sum, F, Count, Q
from django import db
from django.conf import settings
from abc import ABC, abstractmethod

# Base class for APIView that collects timing and query info
class TimedQueryAPIView(APIView, ABC):

    @abstractmethod
    def get_queries(self):
        # children override this method
        pass

    def get(self, request, format=None):
        # temporarily turn DEBUG on so that db.connections is populated with query info
        debug_state = settings.DEBUG
        settings.DEBUG = True
        data = {'query': self.get_queries()}
        settings.DEBUG = debug_state
        print(settings.DEBUG)
        data['stats'] = db.connections['default'].queries
        return Response(data)


class TotalSpentPurpleHair(TimedQueryAPIView):
    def get_queries(self):
        return Spend.objects.filter(audience__hair_color='purple').aggregate(Sum('spend'))['spend__sum']  # should return 566512.00


class CampaignsSpentMore4Days(TimedQueryAPIView):
    def get_queries(self):
        return Campaign.objects.filter(spend__spend__gt=0).annotate(Count('spend__date', distinct=True)).filter(spend__date__count__gt=4).count() # should return 77


class SourceHReportedClicks(TimedQueryAPIView):
    def get_queries(self):
        return {
            'excluding_0': Stat.objects.filter(source='H', action='clicks', count__gt=0).count(), # 614
            'including_0': Stat.objects.filter(source='H', action='clicks').count() # 623
        }


class SourcesMoreJunkThanNoise(TimedQueryAPIView):
    def get_queries(self):
        # TODO: why is this one not returning any stats?
        return {
            'excluding_0': Source.objects.annotate(count_junk=Count('pk', filter=Q(stat__action='junk')),
                count_noise=Count('pk', filter=Q(stat__action='noise'))).annotate(diff=F('count_junk')-F('count_noise'))
                .filter(diff__gt=0).values_list('pk', flat=True), # J, D, F

            'including_0': Source.objects.annotate(count_junk=Count('pk', filter=Q(stat__action='junk', stat__count__gt=0)),
                count_noise=Count('pk', filter=Q(stat__action='noise', stat__count__gt=0)))
                .annotate(diff=F('count_junk')-F('count_noise')).filter(diff__gt=0).values_list('pk', flat=True) # J, D, E
        }


class TotalCostPerViewForVideo(TimedQueryAPIView):
    def get_queries(self):
        query = Spend.objects.filter(ad_type='video').annotate(views_sum=Sum('stat__count', filter=Q(stat__action='views')  )).aggregate(total_spend=Sum('spend'), total_views=Sum('views_sum'))
        data = round(query['total_spend'] / query['total_views'], 2) # 16.49
        return data


class SourceBConversionsNY(TimedQueryAPIView):
    def get_queries(self):
        return Stat.objects.filter(source='B', action='conversions', audience__state='NY').aggregate(Sum('count'))['count__sum'] # should return 268


CPM_QUERY = """SELECT

sum_spend.state, sum_spend.hair_color,
round((spend_sum / imp_sum) * 1000::numeric,2) as cpm

FROM

(
    SELECT DISTINCT
    aud.state, aud.hair_color,
    SUM(spend.spend) OVER (PARTITION BY aud.state, aud.hair_color) as spend_sum
    FROM tracer_assignment_audience AS aud
    LEFT JOIN tracer_assignment_spend AS spend
    ON aud.id = spend.audience_id
) sum_spend

LEFT JOIN

(
    SELECT DISTINCT
    aud.state, aud.hair_color,
    SUM(imp.impressions) OVER (PARTITION BY aud.state, aud.hair_color) as imp_sum
    FROM tracer_assignment_audience AS aud
    LEFT JOIN tracer_assignment_impression AS imp
    ON aud.id = imp.audience_id
) sum_imp

ON sum_spend.state = sum_imp.state and sum_spend.hair_color = sum_imp.hair_color
ORDER BY cpm
LIMIT 1"""


class CombinationStateHairColorBestCPM(TimedQueryAPIView):
    def get_queries(self):
        with db.connection.cursor() as cursor:
            cursor.execute(CPM_QUERY)
            data = cursor.fetchone()
        return '{}, {}, cpm: ${}'.format(data[0], data[1], data[2]) # OR, green, cpm: 40.58
