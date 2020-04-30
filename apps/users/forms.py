# _*_ coding: utf-8 _*_
__author__ = 'wenliang'
__date__ = '2019/4/11 13:16'
from django import forms
from captcha.fields import CaptchaField
from .models import UserProfile


class LoginForm(forms.Form):  # 这里username和password与login.html中的字段名称一致，否则不会做验证的
    username = forms.CharField(required=True)   # 验证的时候username这个字段是必须要有的否则报错
    password = forms.CharField(required=True, min_length=5)  # 验证的时候password这个字段是必须要有并且至少5个字符，否则报错


# 实际上form在生成EmailField，CaptchaField和CharField字段时会生成input框，生成不同的HTML代码。
class RegisterForm(forms.Form):   # 对前端注册表单的一种验证,这里三个字段名称要与register.html中的一致，否则不会做验证的
    email = forms.EmailField(required=True)    # forms的EmailField字段实际上是会对email进行验证的：前端页面传过来的email地址必须符合email的正则表达式，EmailField字段已经在后台做了验证
    password = forms.CharField(required=True, min_length=5)
    captcha = CaptchaField(error_messages={'invalid': '验证码错误了啊！'}) # 定制错误信息error_messages ，invalid，可以直接返回到前端页面
    # 用户在注册页面填写验证码后其实是验证码和隐藏的hashkey一并传到django后台（后台早已经生成了），并在表中做两个字段参数的比对（对应页面源码的captcha_1，captcha_0）


class ForgetForm(forms.Form):   # 对忘记密码表单的一种验证,这里两个字段名称要与forgetpwd.html中的一致，否则不会做验证的
    email = forms.EmailField(required=True)    # forms的EmailField字段实际上是会对email进行验证的：前端传过来的email地址必须符合email的正则表达式，EmailField字段已经在后台做了验证
    captcha = CaptchaField(error_messages={'invalid': '验证码错误了啊！'})


class ModifyPwdForm(forms.Form):   # 对注册表单的一种验证,这里两个字段名称要与password_reset.html中的一致，否则不会做验证的,也要与usercenter-base.html中的一致
    password1 = forms.CharField(required=True, min_length=6)
    password2 = forms.CharField(required=True, min_length=6)


class UploadImageForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['image']


class UserInfoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['nick_name', 'gender', 'birday', 'address', 'mobile']

