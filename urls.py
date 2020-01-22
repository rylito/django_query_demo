from django.urls import include, path, re_path
from tracer_assignment import views
from rest_framework.urlpatterns import format_suffix_patterns
from django.views.generic import TemplateView

app_name = 'tracer_assignment'

urlpatterns = [
    re_path(r'^$',TemplateView.as_view(template_name="assignment/index.html"),name='tracer_assignment_index'),
]

apipatterns = [
    # API views
    re_path(r'^api/', include([
        re_path(r'^total_spent_purple_hair/$', views.TotalSpentPurpleHair.as_view(), name='total_spent_purple_hair'),
        re_path(r'^campaigns_spent_more_4_days/$', views.CampaignsSpentMore4Days.as_view(), name='campaigns_spent_more_4_days'),
        re_path(r'^source_h_reported_clicks/$', views.SourceHReportedClicks.as_view(), name='source_h_reported_clicks'),
        re_path(r'^sources_more_junk_than_noise/$', views.SourcesMoreJunkThanNoise.as_view(), name='sources_more_junk_than_noise'),
        re_path(r'^total_cost_per_view_for_video/$', views.TotalCostPerViewForVideo.as_view(), name='total_cost_per_view_for_video'),
        re_path(r'^source_b_conversions_ny/$', views.SourceBConversionsNY.as_view(), name='source_b_conversions_ny'),
        re_path(r'^combination_state_hair_color_best_cpm/$', views.CombinationStateHairColorBestCPM.as_view(), name='combination_state_hair_color_best_cpm'),
    ]))
]

urlpatterns += format_suffix_patterns(apipatterns)
