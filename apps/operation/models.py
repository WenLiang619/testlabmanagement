from datetime import datetime

from django.db import models

from users.models import UserProfile
from equipments.models import Equipment

# Create your models here.


class UserAsk(models.Model):
    name = models.CharField(max_length=20, verbose_name='姓名')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    equipment_name = models.CharField(max_length=50, verbose_name='设备名')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '用户咨询'
        verbose_name_plural = verbose_name


class EquipmentComments(models.Model):
    '设备评论'
    user = models.ForeignKey(UserProfile, verbose_name='用户')
    equipment = models.ForeignKey(Equipment, verbose_name='设备')
    comments = models.CharField(max_length=200, verbose_name='评论')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '设备评论'
        verbose_name_plural = verbose_name


class UserFavorite(models.Model):
    user = models.ForeignKey(UserProfile, verbose_name='用户')
    fav_id = models.IntegerField(default=0, verbose_name='数据id')
    fav_type = models.IntegerField(choices=((1, '设备'), (2, '测试组'), (3, '工程师')), default=1, verbose_name='收藏类型')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '用户收藏'
        verbose_name_plural = verbose_name


class UserMessage(models.Model):
    user = models.IntegerField(default=0, verbose_name='接收用户')     # 0 是发给所有用户的消息，否则就是发给登录用户（用户的id就是这个user）的消息，不用外键
    message = models.CharField(max_length=500, verbose_name='消息内容')
    has_read = models.BooleanField(default=False, verbose_name='是否已读')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '用户消息'
        verbose_name_plural = verbose_name


class UserEquipment(models.Model):
    '''用户的借用信息这里'''
    user = models.ForeignKey(UserProfile, verbose_name='用户')
    borrow_time = models.DateTimeField(default=datetime.now, verbose_name='借用日期(时分)')
    plan_to_return_time = models.DateTimeField(null=True, blank=True, verbose_name='计划归还日期(时分)')
    return_time = models.DateTimeField(null=True, blank=True, verbose_name='归还日期(时分)')
    equipment = models.ForeignKey(Equipment, verbose_name='设备')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '用户借用设备'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.equipment.name


class UserEquipmentInadvance(models.Model):
    '''用户提前预定信息在这里'''
    user = models.ForeignKey(UserProfile, verbose_name='用户')
    borrow_time = models.DateTimeField(default=datetime.now, verbose_name='借用日期(时分)')
    plan_to_return_time = models.DateTimeField(null=True, blank=True, verbose_name='计划归还日期(时分)')
    return_time = models.DateTimeField(null=True, blank=True, verbose_name='归还日期(时分)')
    equipment = models.ForeignKey(Equipment, verbose_name='设备')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '用户预定设备'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.equipment.name





















