# _*_ coding: utf-8 _*_
__author__ = 'wenliang'
__date__ = '2019/4/10 16:08'
import xadmin

from .models import UserAsk, EquipmentComments, UserFavorite, UserMessage, UserEquipment


class UserAskAdmin(object):
    list_display = ['name', 'mobile', 'equipment_name', 'add_time']
    search_fields = ['name', 'mobile', 'equipment_name']
    list_filter = list_display


class EquipmentCommentsAdmin(object):
    list_display = ['user', 'equipment', 'comments', 'add_time']
    search_fields = ['user', 'equipment', 'comments']
    list_filter = list_display


class UserFavoriteAdmin(object):
    list_display = ['user', 'fav_id', 'fav_type', 'add_time']
    search_fields = ['user', 'fav_id', 'fav_type']
    list_filter = list_display


class UserMessageAdmin(object):
    list_display = ['user', 'message', 'has_read', 'add_time']
    search_fields = ['user', 'message', 'has_read']
    list_filter = list_display


class UserEquipmentAdmin(object):
    list_display = ['user', 'equipment', 'add_time']
    search_fields = ['user', 'equipment']
    list_filter = list_display


xadmin.site.register(UserAsk, UserAskAdmin)
xadmin.site.register(EquipmentComments, EquipmentCommentsAdmin)
xadmin.site.register(UserFavorite, UserFavoriteAdmin)
xadmin.site.register(UserMessage, UserMessageAdmin)
xadmin.site.register(UserEquipment, UserEquipmentAdmin)










