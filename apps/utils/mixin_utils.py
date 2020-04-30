# _*_ coding: utf-8 _*_
__author__ = 'bobby'
__date__ = '2019/3/18 13:03'


from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from TestLabManagement.settings import EMAIL_FROM


class LoginRequiredMixin(object):

    @method_decorator(login_required(login_url='/login/', redirect_field_name='next'))
    def dispatch(self, request, *args, **kwargs):
        # # # 下面邮件发送是为了调试用
        # email_body = 'request:{}'.format(request)
        # send_status = send_mail('request是什么东西', email_body, EMAIL_FROM, ['419099632@qq.com'])
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)









