# _*_ coding: utf-8 _*_
__author__ = 'bobby'
__date__ = '2019/3/29 8:47'


import xadmin
from xadmin.views import BaseAdminPlugin, ListAdminView
from django.template import loader
from xadmin.plugins.utils import get_context_dict


#excel 导入
class ListImportExcelPlugin(BaseAdminPlugin):
    import_excel = False

    def init_request(self, *args, **kwargs):    #插件的入口函数，返回为True的时候加载插件，import_excel在equipments\adminx里可以设置
        return bool(self.import_excel)

    def block_top_toolbar(self, context, nodes): #把自己写的HTML文件显示到一个地方top_toolbar
        nodes.append(loader.render_to_string('xadmin/excel/model_list.top_toolbar.import.html', context=get_context_dict(context))) #相对路径，相对于MxOnline\extra_apps\xadmin\templates\


xadmin.site.register_plugin(ListImportExcelPlugin, ListAdminView)

