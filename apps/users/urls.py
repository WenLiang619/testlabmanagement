# _*_ coding: utf-8 _*_
from django.conf.urls import url, include

from .views import UserinfoView, UploadImageView, UpdatePwdView, SendEmailCodeView
from .views import UpdateEmailView, MyEquipmentView, MyFavTeamView, MyFavEngineerView, MyFavEquipmentView, \
    MymessageView, MytoolView,MyQuizView, MytoolUcalView, MytoolUtcalView, MytoolSafetyQuizView

urlpatterns = [
    # 用户信息
    url(r'^info/$', UserinfoView.as_view(), name='user_info'),

    # 用户头像上传
    url(r'^image/upload/$', UploadImageView.as_view(), name='image_upload'),

    # 用户个人中心修改密码
    url(r'^update/pwd/$', UpdatePwdView.as_view(), name='update_pwd'),

    # 个人中心修改邮箱时发送邮箱验证码
    url(r'^sendemail_code/$', SendEmailCodeView.as_view(), name='sendemail_code'),

    # 修改邮箱
    url(r'^update_email/$', UpdateEmailView.as_view(), name='update_email'),

    # 我的设备
    url(r'^myequipment/$', MyEquipmentView.as_view(), name='myequipment'),

    # 我收藏的测试组
    url(r'^myfav/team/$', MyFavTeamView.as_view(), name='myfav_team'),

    # 我收藏的工程师
    url(r'^myfav/engineer/$', MyFavEngineerView.as_view(), name='myfav_engineer'),

    # 我收藏的设备
    url(r'^myfav/equipment/$', MyFavEquipmentView.as_view(), name='myfav_equipment'),

    # 我的消息
    url(r'^mymessage/$', MymessageView.as_view(), name='mymessage'),

    # 我的工具
    url(r'^mytool/$', MytoolView.as_view(), name='mytool'),

    # 我的答卷
    url(r'^myquiz/$', MyQuizView.as_view(), name='myquiz'),

    # 我的工具-直接测量量不确定度计算
    url(r'^mytool/u_cal/$', MytoolUcalView.as_view(), name='mytool_u_cal'),

    # 我的工具-不确定度计算
    url(r'^mytool/ut_cal/$', MytoolUtcalView.as_view(), name='mytool_ut_cal'),

    # 我的答卷-安全培训后测试问卷
    url(r'^myquiz/safety/$', MytoolSafetyQuizView.as_view(), name='mytool_safety_quiz'),



]
