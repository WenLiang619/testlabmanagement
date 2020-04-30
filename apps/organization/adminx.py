# _*_ coding: utf-8 _*_
__author__ = 'wenliang'
__date__ = '2019/4/10 15:57'
import xadmin

from .models import Location, Team, Engineer


class LocationAdmin(object):
    list_display = ['name', 'desc', 'add_time']
    search_fields = ['name', 'desc']
    list_filter = ['name', 'desc', 'add_time']


class TeamAdmin(object):
    list_display = ['name', 'desc', 'category', 'click_nums', 'fav_nums', 'image', 'location', 'engineer_num', 'equipment_num', 'add_time']
    search_fields = ['name', 'desc', 'category', 'click_nums', 'fav_nums', 'image', 'location__name', 'engineer_num', 'equipment_num']
    list_filter = list_display
    #relfield_style = 'fk-ajax' # 上面search_fields的 外键 需要加__name, 别的model字段如果指向这里可以实现搜索选择而不是全部罗列
    readonly_fields = ['click_nums', 'fav_nums', 'engineer_num', 'equipment_num']

class EngineerAdmin(object):
    list_display = ['team', 'name', 'work_years', 'work_position', 'expertise', 'click_nums', 'fav_nums', 'age', 'image', 'add_time']
    search_fields = ['team__name', 'name', 'work_years', 'work_position', 'expertise', 'click_nums', 'fav_nums', 'age', 'image']
    list_filter = list_display
    relfield_style = 'fk-ajax'  # 上面search_fields的 外键team 需要加__name
    readonly_fields = ['click_nums', 'fav_nums']

    def save_models(self):
        # 新增和修改  -- 在保存工程师的时候统计Team的工程师数目
        obj = self.new_obj      # obj是一个Engineer
        obj.save()
        if obj.team is not None:
            team = obj.team         # team 是Team
            team.engineer_num = Engineer.objects.filter(team=team).count()
            team.save()


xadmin.site.register(Location, LocationAdmin)
xadmin.site.register(Team, TeamAdmin)
xadmin.site.register(Engineer, EngineerAdmin)









