from datetime import datetime

from django.db import models
from django.contrib.auth.models import AbstractUser


class UserProfile(AbstractUser):
    nick_name = models.CharField(max_length=50, verbose_name='昵称', default='')
    birday = models.DateField(verbose_name='生日', null=True, blank=True)
    gender = models.CharField(max_length=6, choices=(('male', '男'), ('female', '女')), default='female')  #  CharField必须定义max_length
    address = models.CharField(max_length=100, default='')
    mobile = models.CharField(max_length=11, null=True, blank=True)
    image = models.ImageField(upload_to='image/%Y/%m', default='image/default.png', max_length=100)

    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name

    def unread_nums(self):
        #获取用户未读消息的数量
        from operation.models import UserMessage# 只能在这里引用，不能放在开头，否则就和operation\model成了循环的import,放在这里就只有调用的时候才会import
        return UserMessage.objects.filter(user=self.id, has_read=False).count()

    def __str__(self):
        return self.username


class EmailVerifyRecord(models.Model):
    code = models.CharField(max_length=20, verbose_name='验证码')     #  没有设置null=True表示不能为空
    email = models.EmailField(max_length=50, verbose_name='邮箱')    # verbose_name 邮箱 体现在后台 中否则显示 email
    send_type = models.CharField(verbose_name='验证码类型', choices=(('register', '注册'), ('forget', '找回密码'),
                                                                     ('update_email', '修改邮箱')), max_length=30)
    send_time = models.DateTimeField(verbose_name='发送时间', default=datetime.now)   # 不是now() ，带括号是编译的时间，无括号则是EmailVerifyRecord实例化的时间

    class Meta:
        verbose_name = '邮箱验证码'  # 在xadmin中看到的导航栏名字一样
        verbose_name_plural = verbose_name

    def __str__(self):
        return '{0}({1})'.format(self.code, self.email)


class Banner(models.Model):
    title = models.CharField(max_length=100, verbose_name='标题')
    image = models.ImageField(upload_to='banner/%Y/%m', verbose_name='轮播图', max_length=100)  # ImageField是保存为char因此max_length必须
    url = models.URLField(max_length=200, verbose_name='访问地址')
    index = models.IntegerField(default=100, verbose_name='顺序')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '轮播图'
        verbose_name_plural = verbose_name







