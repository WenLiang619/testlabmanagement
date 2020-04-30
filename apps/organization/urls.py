# _*_ coding: utf-8 _*_
__author__ = 'wenliang'
__date__ = '2019/4/17 10:41'
from django.conf.urls import url
from .views import OrgView, AddUserAskView, TeamHomeView, TeamEquipmentView, TeamDescView, TeamEngineerView,\
                   AddFavView, EngineerListView, EngineerDetailView


urlpatterns = [
    #team首页
    url(r'^list/$', OrgView.as_view(), name='team_list'),

    url(r'^add_ask/$', AddUserAskView.as_view(), name='add_ask'),

    url(r'^home/(?P<team_id>\d+)/$', TeamHomeView.as_view(), name='team_home'),# 是哪个页面？课程机构的id.#

    url(r'^equipment/(?P<team_id>\d+)/$', TeamEquipmentView.as_view(), name='team_equipment'),

    url(r'^desc/(?P<team_id>\d+)/$', TeamDescView.as_view(), name='team_desc'),

    url(r'^engineer/(?P<team_id>\d+)/$', TeamEngineerView.as_view(), name='team_engineer'),

    # 机构收藏
    url(r'^add_fav/$', AddFavView.as_view(), name='add_fav'),

    # 工程师列表页
    url(r'^engineer/list/$', EngineerListView.as_view(), name='engineer_list'),

    # 工程师详情
    url(r'^engineer/detail/(?P<engineer_id>\d+)/$', EngineerDetailView.as_view(), name='engineer_detail'),
]














