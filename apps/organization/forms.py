# _*_ coding: utf-8 _*_
__author__ = 'wenliang'
__date__ = '2019/4/17 10:41'
import re

from django import forms
from operation.models import UserAsk

# class UserAskForm(forms.Form):
#     name = forms.CharField(required=True, min_length=2, max_length=20)
#     mobile = forms.CharField(required=True, min_length=11, max_length=11)
#     equipment_name = forms.CharField(required=True, min_length=5, max_length=50)


class UserAskForm(forms.ModelForm):
    # my_field = forms.CharField()  # 可以新增字段
    class Meta:
        model = UserAsk  # 继承operation.models.UserAsk的字段。 ModelForm还可以在表单验证后手动调用Model的save到数据库中，Form不行
        fields = ['name', 'mobile', 'equipment_name']

    def clean_mobile(self):  # views中初始化UserAskForm的时候（userask_form = UserAskForm(request.POST)） 会主动调用这里的函数???
        '''
        验证手机号码是否合法
        '''
        mobile = self.cleaned_data['mobile']
        REGEX_MOBILE = "^1[358]\d{9}$|^147\d{8}$|^176\d{8}$"
        p = re.compile(REGEX_MOBILE)
        if p.match(mobile):
            return mobile
        else:
            raise forms.ValidationError('手机号码非法!!!!', code='mobile_invalid')


