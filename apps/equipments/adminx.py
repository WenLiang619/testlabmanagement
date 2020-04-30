# _*_ coding: utf-8 _*_
__author__ = 'wenliang'
__date__ = '2019/4/10 15:12'
from datetime import datetime
from datetime import timedelta
import xadmin

from .models import Equipment, BannerEquipment,Plan2CaliEquipment, EquipmentVideo, EquipmentResource
from organization.models import Team


class EquipmentResourceInline(object):
    model = EquipmentResource
    extra = 0


class EquipmentVideoInline(object):
    model = EquipmentVideo
    extra = 0


class EquipmentAdmin(object):
    list_display = ['item', 'name', 'desc', 'detail','is_banner', 'sn', 'asset_num', 'type', 'team', 'responsible_person', 'fav_nums',
                    'click_nums', 'reserve_times', 'tag', 'image', 'cal_date', 'next_cal_date', 'manufacturer', 'location', 'status', 'add_time',
                    'get_resource_nums', 'go_to']
    search_fields = ['item', 'name', 'desc', 'detail','is_banner', 'sn', 'asset_num', 'type', 'team', 'responsible_person', 'fav_nums',
                     'click_nums', 'reserve_times', 'tag', 'image', 'cal_date', 'next_cal_date', 'manufacturer', 'location', 'status',
                     'get_resource_nums', 'go_to']
    list_filter = ['item', 'name', 'desc', 'detail', 'is_banner', 'sn', 'asset_num', 'type', 'team', 'responsible_person', 'fav_nums',
                    'click_nums', 'reserve_times', 'tag', 'image', 'cal_date', 'next_cal_date', 'manufacturer', 'location', 'status', 'add_time',
                    ]    # get_resource_nums不能写在这里
    ordering = ['-click_nums'] #进入xadmin后默认以点击数排序
    readonly_fields = ['click_nums', 'fav_nums', 'reserve_times']
    # exclude = ['fav_nums'] #这个字段不显示在 点击这个设备后的页面中 exclude、readonly_fields互相矛盾的
    list_editable = ['cal_date', 'next_cal_date']
    inlines = [EquipmentResourceInline, EquipmentVideoInline]
    # refresh_times = [3, 5]    #xadmin定时刷新
    style_fields = {'detail': 'ueditor'}    # style_fields这个字段xadmin可以识别的（在ueditor.py\get_field_style中识别），class UserAdmin(object)中也用到了
                                            # ueditor需要在插件（在ueditor.py\get_field_style中识别）中识别
    import_excel = True  # 会覆盖 插件excel.py中的变量，使能Course表的excel导入插件功能

    # def queryset(self): #不用，还是显示全部设备吧
    #     qs = super(EquipmentAdmin, self).queryset()
    #     qs = qs.filter(is_banner=False)
    #     return qs

    def save_models(self):
        # 新增和修改-在保存设备的时候统计Team的设备数目
        obj = self.new_obj      # obj是一个Equipment
        obj.save()
        if obj.team is not None:
            team = obj.team         # team 是Team
            team.equipment_num = Equipment.objects.filter(team=team).count()
            team.save()


    def post(self, request, *args, **kwargs):
        if 'excel' in request.FILES:
            pass  #读取Excel的示例代码及更新数据库操作可以参考https://coding.imooc.com/learn/questiondetail/10727.html
        return super(EquipmentAdmin, self).post(request, args, kwargs)


class BannerEquipmentAdmin(object):
    list_display = ['item', 'name', 'desc', 'detail','is_banner', 'sn', 'asset_num', 'type', 'team', 'responsible_person', 'fav_nums',
                    'click_nums', 'reserve_times', 'tag', 'image', 'cal_date', 'next_cal_date', 'manufacturer', 'location', 'status', 'add_time',
                    'get_resource_nums', 'go_to']
    search_fields = ['item', 'name', 'desc', 'detail','is_banner', 'sn', 'asset_num', 'type', 'team', 'responsible_person', 'fav_nums',
                     'click_nums', 'reserve_times', 'tag', 'image', 'cal_date', 'next_cal_date', 'manufacturer', 'location', 'status',
                     'get_resource_nums', 'go_to']
    list_filter = ['item', 'name', 'desc', 'detail', 'is_banner', 'sn', 'asset_num', 'type', 'team', 'responsible_person', 'fav_nums',
                    'click_nums', 'reserve_times', 'tag', 'image', 'cal_date', 'next_cal_date', 'manufacturer', 'location', 'status', 'add_time',
                    ]    # get_resource_nums不能写在这里
    ordering = ['-click_nums'] #进入xadmin后默认以点击数排序
    readonly_fields = ['click_nums', 'fav_nums', 'reserve_times']
    # exclude = ['fav_nums'] #这个字段不显示在 点击这个设备后的页面中 exclude、readonly_fields互相矛盾的
    list_editable = ['cal_date', 'next_cal_date']
    inlines = [EquipmentResourceInline, EquipmentVideoInline]
    # refresh_times = [3, 5]

    def queryset(self):
        qs = super(BannerEquipmentAdmin, self).queryset()
        qs = qs.filter(is_banner=True)
        return qs


class Plan2CaliEquipmentAdmin(object):
    list_display = ['item', 'name', 'desc', 'detail','is_banner', 'sn', 'asset_num', 'type', 'team', 'responsible_person', 'fav_nums',
                    'click_nums', 'reserve_times', 'tag', 'image', 'cal_date', 'next_cal_date', 'manufacturer', 'location', 'status', 'add_time',
                    'get_resource_nums', 'go_to']
    search_fields = ['item', 'name', 'desc', 'detail','is_banner', 'sn', 'asset_num', 'type', 'team', 'responsible_person', 'fav_nums',
                     'click_nums', 'reserve_times', 'tag', 'image', 'cal_date', 'next_cal_date', 'manufacturer', 'location', 'status',
                     'get_resource_nums', 'go_to']
    list_filter = ['item', 'name', 'desc', 'detail', 'is_banner', 'sn', 'asset_num', 'type', 'team', 'responsible_person', 'fav_nums',
                    'click_nums', 'reserve_times', 'tag', 'image', 'cal_date', 'next_cal_date', 'manufacturer', 'location', 'status', 'add_time',
                    ]    # get_resource_nums不能写在这里
    ordering = ['-click_nums'] #进入xadmin后默认以点击数排序
    readonly_fields = ['click_nums', 'fav_nums', 'reserve_times']
    # exclude = ['fav_nums'] #这个字段不显示在 点击这个设备后的页面中 exclude、readonly_fields互相矛盾的
    list_editable = ['cal_date', 'next_cal_date']
    inlines = [EquipmentResourceInline, EquipmentVideoInline]
    # refresh_times = [3, 5]

    def queryset(self):
        qs = super(Plan2CaliEquipmentAdmin, self).queryset()
        cal_interval = timedelta(days=30)
        qs = qs.filter(next_cal_date__lte=datetime.now() + cal_interval)
        return qs


class EquipmentVideoAdmin(object):
    list_display = ['equipment', 'name', 'time', 'url', 'add_time']
    search_fields = ['equipment', 'name', 'time', 'url']
    list_filter = list_display


class EquipmentResourceAdmin(object):
    list_display = ['equipment', 'name', 'download', 'add_time']
    search_fields = ['equipment', 'name', 'download']
    list_filter = ['equipment__name', 'name', 'download', 'add_time']
    list_editable = ['name']


xadmin.site.register(Equipment, EquipmentAdmin)
xadmin.site.register(BannerEquipment, BannerEquipmentAdmin)
xadmin.site.register(Plan2CaliEquipment, Plan2CaliEquipmentAdmin)
xadmin.site.register(EquipmentVideo, EquipmentVideoAdmin)
xadmin.site.register(EquipmentResource, EquipmentResourceAdmin)





