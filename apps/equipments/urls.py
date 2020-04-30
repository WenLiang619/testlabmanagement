# _*_ coding: utf-8 _*_
__author__ = 'wenliang'
__date__ = '2019/4/18 14:29'

from django.conf.urls import url
from .views import EquipmentsListView, EquipDetailView, EquipmentInfoView, CommentsView, AddCommentsView, ReserveView, \
                    UserReserveEquipmentView, UserReturnEquipmentView, VideoPlayView


urlpatterns = [
    #设备列表
    url(r'^list/$', EquipmentsListView.as_view(), name='equipment_list'),

    # 用户借用设备form的ajax提交
    url(r'^user_reserve/$', UserReserveEquipmentView.as_view(), name='user_reserve'),

    # 用户归还设备form的ajax提交
    url(r'^user_return/$', UserReturnEquipmentView.as_view(), name='user_return'),

    # 设备详情页
    url(r'^detail/(?P<equipment_id>\d+)/$', EquipDetailView.as_view(), name='equipment_detail'),

    url(r'^info/(?P<equipment_id>\d+)/$', EquipmentInfoView.as_view(), name='equipment_info'),

    # 设备评论
    url(r'^comment/(?P<equipment_id>\d+)/$', CommentsView.as_view(), name='equipment_comments'),

    # 设备预定页面
    url(r'^reserve/(?P<equipment_id>\d+)/$', ReserveView.as_view(), name='equipment_reserve'),


    # 添加设备评论 在URL中没有设备id是因为设备id已经放在POST数据中了，所以这里就不需要URL中传这个参数了
    url(r'^add_comment/$', AddCommentsView.as_view(), name='add_comment'),

    # 设备视频
    url(r'^video/(?P<video_id>\d+)/$', VideoPlayView.as_view(), name='video_play'),
]
















































