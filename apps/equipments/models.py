from datetime import datetime

from DjangoUeditor.models import UEditorField

from django.db import models

from organization.models import Team, Engineer
from users.models import UserProfile


# Create your models here.


class Equipment(models.Model):
    item = models.CharField(max_length=6, verbose_name='管理编号')
    name = models.CharField(max_length=50, verbose_name='设备名称')
    desc = models.CharField(max_length=300, verbose_name='设备描述')
    # detail = models.TextField(verbose_name='设备详情')
    detail = UEditorField(verbose_name='设备详情', width=600, height=300, imagePath="equipments/ueditor/",  #这里前面不能有/,这里配置的是相对路径，相对于MEDIA_ROOT的路径
                                 filePath="equipments/ueditor/", default='')
    is_banner = models.BooleanField(default=False, verbose_name='是否轮播')
    sn = models.CharField(max_length=50, verbose_name='设备序列号')
    asset_num = models.CharField(max_length=15, verbose_name='设备资产编号')
    type = models.CharField(max_length=20, verbose_name='设备型号')
    # 设备所属组 需要使用外键
    team = models.ForeignKey(Team, verbose_name='所属组', null=True, blank=True)
    # 设备责任人 需要使用外键
    responsible_person = models.ForeignKey(Engineer, verbose_name='设备责任人', null=True, blank=True)
    fav_nums = models.IntegerField(default=0, verbose_name='收藏人数')
    click_nums = models.IntegerField(default=0, verbose_name='点击数')
    reserve_times = models.IntegerField(default=0, verbose_name='借用次数')
    tag = models.CharField(default='', verbose_name='设备标签', max_length=10)
    has_checked_before_return = models.BooleanField(default=False, verbose_name='归还前是否查验')
    reservable_inadvance = models.BooleanField(default=False, verbose_name='是否允许提前预定')
    image = models.ImageField(upload_to='equipments/%Y/%m', verbose_name='封面图', max_length=100)
    cal_date = models.DateTimeField(default=datetime.now, verbose_name='校验日期')
    next_cal_date = models.DateTimeField(default=datetime.now, verbose_name='下次校验日期')
    manufacturer = models.CharField(max_length=30, verbose_name='制造商')
    location = models.CharField(max_length=30, verbose_name='设备位置')
    status = models.CharField(verbose_name='设备状态', choices=(('Inactive', '不在使用'), ('Active', '在用'),
                                                  ('Maintenance', '保养中'), ('Calibration', '校验中')), max_length=20)
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '所有设备'
        verbose_name_plural = verbose_name

    def get_borrow_users(self):
        ''' 借用此设备的UserEquipment类的实例组成的QuerySet,未去重'''
        user_equipments = self.userequipment_set.all()
        return user_equipments

    def get_borrow_users_distinct(self):
        '''借用此设备的UserProfile类的实例组成的列表,去重了'''
        user_ids = self.userequipment_set.values_list('user', flat=True).distinct()
        user_list = []#可以省，没有块级作用域
        for user_id in user_ids:
            user_list += UserProfile.objects.filter(id=user_id)
        return user_list

    def get_last_borrow_user(self):
        '''借用此设备的最近那个UserEquipment类的实例,即当前借用人的那个UserEquipment实例'''
        lenth = len(self.get_borrow_users())
        if lenth >= 1:
            return self.userequipment_set.all()[lenth-1]
        else:
            return None

    ############ 可以提前预定设备
    def get_borrowinadvance_userequipmentinadvance(self):
        ''' 提前预定此设备的UserEquipmentInadvance类的实例组成的QuerySet,未去重'''
        user_equipmentsinadvance = self.userequipmentinadvance_set.all()
        return user_equipmentsinadvance

    def get_borrowinadvance_users_distinct(self):
        '''预定过此设备的UserProfile类的实例组成的列表,去重了'''
        user_ids = self.userequipmentinadvance_set.values_list('user', flat=True).distinct()
        user_list = []#可以省，没有块级作用域
        for user_id in user_ids:
            user_list += UserProfile.objects.filter(id=user_id)
        return user_list

    def get_last_borrowinadvance_user(self):
        '''预定此设备的最近那个UserEquipmentInadvance类的实例,即当前预定人的那个UserEquipmentInadvance实例'''
        lenth = len(self.get_borrowinadvance_userequipmentinadvance())
        if lenth >= 1:
            return self.userequipmentinadvance_set.all()[lenth-1]
        else:
            return None
    ############

    def get_equipment_videos(self):
        '''获取设备的视频model'''
        return self.equipmentvideo_set.all()

    def get_resource_nums(self):
        return self.equipmentresource_set.all().count()
    get_resource_nums.short_description = '资源数目'

    def go_to(self):
        from django.utils.safestring import mark_safe
        return mark_safe("<a href='http://www.danfoss.com'>跳转</>")
    go_to.short_description = '跳转'  # 在CourseAdmin的list_display中添加进去

    def __str__(self):
        return self.item + '-' + self.name # 这里之所以这样是因为想在xadmin的设备资源、设备视频中的设备字段显示出HT编号与名称


class BannerEquipment(Equipment):
    class Meta:
        verbose_name = '轮播设备'   # 在xadmin中显示的名字
        verbose_name_plural = verbose_name
        proxy = True   # 这样就不会生成表了，但是又具有model的功能


class Plan2CaliEquipment(Equipment):
    class Meta:
        verbose_name = '待校验设备'  # 在xadmin中显示的名字
        verbose_name_plural = verbose_name
        proxy = True  # True不会生成表了，但是又具有model的功能 , 想要通过这里设置成False生成一个表来记录需要准备校验的设备是不行的，与queryset方法矛盾


class EquipmentVideo(models.Model):
    equipment = models.ForeignKey(Equipment, verbose_name='设备', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name='视频名')
    time = models.IntegerField(default=0, verbose_name='时长(分钟数)')
    url = models.CharField(max_length=200, default='', verbose_name='访问地址')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '设备视频'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class EquipmentResource(models.Model):
    equipment = models.ForeignKey(Equipment, verbose_name='设备')
    name = models.CharField(max_length=100, verbose_name='资源名称')
    download = models.FileField(upload_to='equipments/resource/%Y%m', verbose_name='资源文件', max_length=100)
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '设备资源'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name




