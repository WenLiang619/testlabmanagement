# _*_ coding: utf-8 _*_
__author__ = 'wenliang'
__date__ = '2019/4/19 16:28'
from django import forms
from operation.models import UserEquipment


class UserEquipmentForm(forms.ModelForm):
    # my_field = forms.CharField()  # 可以新增字段
    class Meta:
        model = UserEquipment
        fields = ['user', 'borrow_time', 'plan_to_return_time', 'return_time', 'equipment']



