# _*_ coding: utf-8 _*_
__author__ = 'wenliang'
__date__ = '2019/4/11 17:52'

from random import Random
from django.core.mail import send_mail
from django.http import HttpResponse

from users.models import EmailVerifyRecord
from TestLabManagement.settings import EMAIL_FROM


def random_str(randomlength=8):
    str_code = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str_code += chars[random.randint(0, length)]
    return str_code


def send_register_email(email, send_type='register'):
    email_record = EmailVerifyRecord()  # 发送链接邮件之前先将EmailVerifyRecord信息保存到数据库
                                        # 因为用户以后在点击这个链接的时候需要查一下这个链接是否存在
    if send_type == 'update_email':
        code = random_str(4)       # 用户在个人中心
    else:
        code = random_str(16)       # 在给用户的链接上加上的随机字符串（后台生成），这个字符串附加在url链接上,用户点击这个链接时，ResetView/ActiveUserView取出这个code去查询数据库这个code是否存在，存在就激活，否则就报错
    email_record.code = code
    email_record.email = email
    email_record.send_type = send_type
    email_record.save() # 需要发送的code事先保存到数据库users_emailverifyrecord中，然后就是发送邮件了

    if send_type == 'register':
        email_title = 'Test&Lab注册激活链接'
        # email_body = '请点击下面的链接激活你的账号：http://39.100.99.20:8000/active/{0}'.format(code)
        email_body = '请点击下面的链接激活你的账号：http://39.100.99.20/active/{0}'.format(code)

        send_status = send_mail(email_title, email_body, EMAIL_FROM, [email])
        if send_status:
            pass
    elif send_type == 'forget':
        email_title = 'Test&Lab注册密码重置链接'
        email_body = '请点击下面的链接重置你的密码：http://39.100.99.20/reset/{0}'.format(code)

        send_status = send_mail(email_title, email_body, EMAIL_FROM, [email])
        if send_status:
            pass
    elif send_type == "update_email":
        email_title = 'Test&Lab邮箱修改验证码'
        email_body = '你的邮箱验证码为：{0}'.format(code)

        send_status = send_mail(email_title, email_body, EMAIL_FROM, [email])
        if send_status:
            pass
        else:
            return HttpResponse('{"status":"failure"}', content_type='application/json')














