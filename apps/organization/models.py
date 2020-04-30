from datetime import datetime

from django.db import models


# Create your models here.
class Location(models.Model):
    name = models.CharField(max_length=20, verbose_name='所在位置')
    desc = models.CharField(max_length=200, verbose_name='描述')
    add_time = models.DateTimeField(default=datetime.now)

    class Meta:
        verbose_name = 'Team来自'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=50, verbose_name='组名')
    desc = models.TextField(verbose_name='组描述')
    tag = models.CharField(default='专业测试', max_length=10, verbose_name='小组标签')
    category = models.CharField(default='test', verbose_name='团队类型', max_length=20,
                                choices=(('develop', '研发'), ('test', '测试')))
    click_nums = models.IntegerField(default=0, verbose_name='点击数')
    fav_nums = models.IntegerField(default=0, verbose_name='收藏数')
    image = models.ImageField(upload_to='team/%Y/%m', verbose_name='logo', max_length=100)
    location = models.ForeignKey(Location, verbose_name='所在位置', on_delete=models.CASCADE, default=1)
    engineer_num = models.IntegerField(default=0, verbose_name='工程师人数')
    equipment_num = models.IntegerField(default=0, verbose_name='设备数')
    add_time = models.DateTimeField(default=datetime.now)

    class Meta:
        verbose_name = '组管理'
        verbose_name_plural = verbose_name

    def get_engineer_num(self):
        #获取team的工程师数
        return self.engineer_set.all().count()

    def __str__(self):
        return self.name


class Engineer(models.Model):
    team = models.ForeignKey(Team, verbose_name='所属组')
    name = models.CharField(max_length=50, verbose_name='工程师名字')
    email = models.EmailField(max_length=50, verbose_name='邮箱', null=True, blank=True)
    work_years = models.IntegerField(default=0, verbose_name='工作年限')
    work_position = models.CharField(max_length=50, verbose_name='公司职位')
    expertise = models.CharField(max_length=50, verbose_name='专业特长')
    click_nums = models.IntegerField(default=0, verbose_name='点击数')
    fav_nums = models.IntegerField(default=0, verbose_name='收藏数')
    age = models.IntegerField(default=18, verbose_name='年龄')
    image = models.ImageField(default='', upload_to='engineer/%Y/%m', verbose_name='头像', max_length=100)
    add_time = models.DateTimeField(default=datetime.now)

    class Meta:
        verbose_name = '工程师'
        verbose_name_plural = verbose_name

    def get_equip_nums(self):
        return self.equipment_set.all().count()

    def __str__(self):
        return self.name





























