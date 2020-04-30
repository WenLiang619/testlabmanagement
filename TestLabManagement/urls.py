"""TestLabManagement URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import TemplateView
import xadmin

from django.views.static import serve
from TestLabManagement.settings import MEDIA_ROOT#,STATIC_ROOT

from users.views import LoginView, LogoutView, RegisterView, ActiveUserView, ForgetPwdView, ResetView, ModifyPwdView
from users.views import IndexView
from organization.views import OrgView
import xadmin


urlpatterns = [
    url(r'^xadmin/', xadmin.site.urls),

    # url('^$', TemplateView.as_view(template_name='index.html'), name='index'),
    url('^$', IndexView.as_view(), name='index'),

    # url('^login/$', TemplateView.as_view(template_name='login.html'), name='login'),
    # url('^login/$', user_login, name='login'),
    url('^login/$', LoginView.as_view(), name='login'),
    url('^logout/$', LogoutView.as_view(), name='logout'),

    url('^register/$', RegisterView.as_view(), name='register'),
    url(r'^captcha/', include('captcha.urls')), # 这个url是django自己配置的 具体是在验证码的页面源码中可以看到自动生成了一个url  127.0.../caprcha/image/...
    url(r'^active/(?P<active_code>.*)/$', ActiveUserView.as_view(), name='user_active'),#用户在浏览器点击邮件里的链接就是调用这个url # 提取出用户点击那个链接active后面的串放入active_code中去，在ActiveUserView的get方法中会用到

    url(r'^forget/$', ForgetPwdView.as_view(), name='forget_pwd'),
    url(r'^reset/(?P<active_code>.*)/$', ResetView.as_view(), name='reset_pwd'),
    url(r'^modify_pwd/$', ModifyPwdView.as_view(), name='modify_pwd'), # modify_pwd 在password_reset.html中使用

    # team url分发
    url(r'^org/', include('organization.urls', namespace='org')),

    # 设备相关url配置
    url(r'^equipments/', include('equipments.urls', namespace='equipments')),

    # 配置上传文件的访问处理函数,否则org/list上的机构图片显示不了，org-list.html中用到MEDIA_ROOT
    url(r'^media/(?P<path>.*)$', serve, {"document_root": MEDIA_ROOT}),

    # # 配置static文件的访问路径处理函数debug=false用这里
    # url(r'^static/(?P<path>.*)$',  serve, {"document_root": STATIC_ROOT}),

    # 用户相关url配置
    url(r'^users/', include('users.urls', namespace='users')),

    # 配置富文本相关url
    url(r'^ueditor/', include('DjangoUeditor.urls')),

]

# 全局404/500页面配置
handler404 = 'users.views.page_not_found'
handler500 = 'users.views.page_error'

