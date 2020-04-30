import json, math
from functools import reduce

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.views.generic.base import View
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse

from background_task.models import Task
from equipments.tasks import notify_user

from .models import UserProfile, EmailVerifyRecord
from operation.models import UserEquipment, UserFavorite, UserMessage
from .forms import LoginForm, RegisterForm, ForgetForm, ModifyPwdForm
from utils.email_send import send_register_email
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger

from organization.models import Team, Engineer
from equipments.models import Equipment
from .models import Banner
from .forms import UploadImageForm, UserInfoForm


class CustomBackend(ModelBackend):  # 有了这个就可以实现用户和邮箱都可以登录，authenticate在这里被重写此方法自动被调用
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:  # Model的objects管理器 ？？？
            user = UserProfile.objects.get(Q(username=username) | Q(email=username))    # 到数据库查询用户名或者邮箱是否有并做检查是否一致，取出 user。这里不检查密码因为django后台存的是密文没法把前端页面传进来的明文进行数据库查询
            if user.check_password(password):    # user是UserProfile继承AbstractUser，AbstractUser有一个方法check_password；明文传进去并加密与后台数据库中user的password密文对比
                return user
        except Exception as e:
            return None


class ActiveUserView(View):     #用户点击激活邮件里的链接会跳到这里是GET 方法
    def get(self, request, active_code): #active_code 要与url参数中的名称一样，提取出来啦
        all_records = EmailVerifyRecord.objects.filter(code= active_code)  # 发送链接邮件之前已经将EmailVerifyRecord信息code,email,send_type保存到数据库users_emailverifyrecord  参见email_send.py文件
                                                                           # 因为现在用户点击这个链接了，需要查一下这个链接是否存在，通过 users_emailverifyrecord表中的code(这里是参数active_code)字段到表users_emailverifyrecord中查询是否有记录
        if all_records: # 如果users_emailverifyrecord中有记录，就到这个表里去获取email(email = record.email)并通过这个email 在users_userprofile表中找到这个user（UserProfile类型）激活它（is_active = 1）（RegisterView的POST里is_active = False 并保存userprofile后发送邮件，等用户点击后在此激活）
            for record in all_records:
                email = record.email
                user = UserProfile.objects.get(email= email)  # user 是一个UserProfile类型
                user.is_active = True   #用户点击那个链接了  激活吧
                user.save()  # 保存到users_userprofile表
        else:
            return render(request, 'active_fail.html') # 用户试图在浏览器输入他邮箱里的链接并访问来激活注册的账号，可是链接失效，给一个信息提示
        return render(request, 'login.html')


class RegisterView(View):
    def get(self, request):
        register_form = RegisterForm()
        return render(request, 'register.html', {'register_form': register_form})
        # 这里的register_form是可以传给前端页面使用的，返回form的验证信息到页面，验证的逻辑和输出信息是django的forms自动完成的，配置好就可以了

    def post(self, request):
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            user_name = request.POST.get('email', '')  # 注册的时候用的是 email注册
            if UserProfile.objects.filter(email=user_name):
                return render(request, 'register.html', {'register_form': register_form,
                                                         'msg': '用户已经存在！'})  # 回填用户信息register_form(html中的value=部分)， 需要显示它的验证码
            pass_word = request.POST.get('password', '')  # 前端输入的是明文， 不是django数据库中的密文
            user_profile = UserProfile()
            user_profile.username = user_name  # 其实这里user_name是邮箱因为注册是用邮箱注册的
            user_profile.email = user_name
            user_profile.is_active = False  # 用户点击那个链接后才能激活
            user_profile.password = make_password(pass_word)  # 对前端明文加密然后存到后台数据库
            user_profile.save()  # 保存到数据库users_userprofile表中不是users_emailverifyrecord

            # 写入欢迎注册消息
            user_message = UserMessage()
            user_message.user = user_profile.id  # 因为operation\models\UserMessage\user不是指向外键UserProfile，而是一个int
            user_message.message = "欢迎注册Test&Lab"
            user_message.save()

            send_register_email(user_name, 'register')  # 发送动作之前是要保存code,email,send_type到数据库users_emailverifyrecord中
            return render(request, 'login.html')
        else:
            return render(request, 'register.html', {'register_form': register_form})


import re
class LogoutView(View):
    '''
    刚开始是用户登出到首页index.html，后台根据https://juejin.im/post/5a780ced6fb9a063395c4b6f登出到
    '''
    def get(self, request):
        next = request.GET.get('next', '')
        logout(request)
        if next:
            if 'equipments/info' in next or 'equipments/comment'in next or 'equipments/reserve'in next:
                return HttpResponseRedirect('/equipments/detail/' + re.findall('\d+', next)[0] +'/')
            return HttpResponseRedirect(next)
        return HttpResponseRedirect(reverse('index'))
        # logout(request)
        #    # HttpResponseRedirect重定向到一个url的地址
        # return HttpResponseRedirect(reverse('index'))  # reverse可以把url的名称name反解成url的地址
        #                                                # 传equipments:equipment_list等也是可以


class LoginView(View):  #  重写View的get和post方法。View会根据get方法自动调用get函数，post方法就自动调用post函数。 request是django自动给我们添加的；当在urls.py中配置了url，django就会自动生成一个request放到函数View.get/post里面作为参数。
    # def get(self, request): # 刷新页面login就是get。就是django自动注册进来的request， 如果是get方法，自动调用View的get函数
    #     return render(request, 'login.html', {})

    def get(self, request):
        # 获取到next参数，渲染到template中，在form表单添加一个hidden类型的元素
        next = request.GET.get('next', '')
        return render(request, "login.html", {'next': next})

    def post(self, request):
        # #下面邮件发送是为了调试用
        # email_body = 'request.POST里的next是:{}' \
        #     .format(request.POST.get('next', ''))
        # send_status = send_mail('测试request.POST里的next是？', email_body,
        #                         EMAIL_FROM,
        #                         ['419099632@qq.com'])
        login_form = LoginForm(request.POST)    # 会把login.html中的username和password字段对应到forms.py中的LoginForm中username和password字段去并做两个字段的校验
        # 上面实例化的时候View已经做了form的检查验证(每个字段是否合法)：包括两个必填字段，密码最少5个字符
        if login_form.is_valid():  # is_valid就是检查login_form下的_errors是否为空；如果字段都合法（LoginForm中的两个字段必填，密码至少5个字符），则_errors为空
            user_name = request.POST.get('username', '')  # 字典的用法 必须用username password? 因为前端页面login用这两个名称，保持一致？
            pass_word = request.POST.get('password', '')   # 字典的用法 csrtoken那个不用管，因为能进入这里说明django已经验证过了的否则进不了这里的
            user = authenticate(username=user_name, password=pass_word)  # authenticate只是向数据库发起验证二者是否存在若存在返回UserProfile类型，并没有登录
            if user is not None:   # user是UserProfile类型,邮箱和用户名都可以实现登录因为有重写authenticate方法
                if user.is_active:  # 激活的用户才登录哦
                    login(request, user)  #  session 和 cookie里有讲login如何实现登录机制。注意这里的request/user是注册到index.html中去的
                    if request.POST.get('next', ''):
                        # 如果request.POST.get('next', '')存在，直接跳转到指定页面
                        return HttpResponseRedirect(request.POST.get('next', ''))
                    # return render(request, 'index.html')  # 登录成功 返回首页，html中对登录成功后的页面改显示什么有判断处理
                    return HttpResponseRedirect(reverse('index'))#这样用户登录后就会进入IndexView把相关数据传递到index.html；而上面的render到index.html则没有数据传递到index.html

                else:   #未激活的用户当然不能登录哦,回到登录页面
                    return render(request, 'login.html', {'login_form': login_form, 'msg': '用户未激活！'})    # 这里的msg是可以传给前端页面使用的,'login_form'返回是用于回填
            else:
                return render(request, 'login.html', {'login_form': login_form, 'msg': '用户名或者密码错误！'})  # 这里的msg是可以传给前端页面使用的,'login_form'返回是用于回填
        else:
            return render(request, 'login.html', {'login_form': login_form})  # 这里的login_form是可以传给前端页面使用的，返回form的验证信息到页面，验证的逻辑和输出信息是django的forms自动完成的，配置好就可以了


class ForgetPwdView(View):
    def get(self, request):
        forget_form = ForgetForm()
        return render(request, 'forgetpwd.html', {'forget_form': forget_form})

    def post(self, request):
        forget_form = ForgetForm(request.POST)  # 会把forgetpwd.html中的email字段对应到forms.py中的ForgetForm中email字段去并做字段的校验
        # 上面实例化的时候View已经做了form的检查验证(字段是否合法)：email字段
        if forget_form.is_valid():# is_valid就是检查forget_form下的_errors是否为空；如果字段都合法，则_errors为空
            email = request.POST.get('email', '')
            send_register_email(email, 'forget')

            # 在ActiveUserView中用户试图在浏览器输入他邮箱里的链接并访问来激活注册的账号，可是链接失效，给一个信息提示
            # 邮件发送成功也给一个邮件发送成功的提示
            return render(request, 'send_success.html')
        else:
            return render(request, 'forgetpwd.html', {'forget_form': forget_form})# 这里的forget_form是可以传给前端页面使用的，返回form的验证信息到页面，验证的逻辑和输出信息是django的forms自动完成的，配置好就可以了


class ResetView(View):
    '''
    用户在浏览器输入http://127.0.0.1:8000/reset/********** 是get   **********是存在EmailVerifyRecord中的code
    '''
    def get(self, request, active_code):
        all_records = EmailVerifyRecord.objects.filter(code= active_code) # 发送链接邮件之前已经将EmailVerifyRecord信息code,email,send_type保存到数据库users_emailverifyrecord  参见email_send.py文件
                                                                           # 因为现在用户点击这个链接了，需要查一下这个链接是否存在，通过 users_emailverifyrecord表中的code(这里是参数active_code)字段到表users_emailverifyrecord中查询是否有记录
        if all_records:# 如果users_emailverifyrecord中有记录，就到这个表里去获取email(email = record.email). 然后返回一个密码重置页面password_reset.html并把email返回，在此页面中有个hidden的input框会把这个email以POST方法返回（<form id="reset_password_form" action="{% url 'modify_pwd' %}" method="post">）到ModifyPwdView，在ModifyPwdView中这样取email = request.POST.get('email', '')
            for record in all_records:#record是EmailVerifyRecord类型
                email = record.email
                return render(request, 'password_reset.html', {'email': email})
        else:
            return render(request, 'active_fail.html')
        return render(request, 'login.html')


class ModifyPwdView(View):
    '''
    修改用户密码，用户在http://127.0.0.1:8000/reset/uaJKy1TJtW7NAR44/ 页面点击提交是post
    '''
    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        if modify_form.is_valid():
            pwd1 = request.POST.get('password1', '') #password1,2是password_reset Html页面input框传过来的,email也是。
            pwd2 = request.POST.get('password2', '')
            email = request.POST.get('email', '') #password_reset.html中的隐藏的输入框传来的 <input type = 'hidden' name= 'email' value="{{ email }}" /> <!-- 后台ResetView的get返回的email -->
            if pwd1 != pwd2:
                return render(request, 'password_reset.html', {'modify_form': modify_form, 'email': email, 'msg': '密码不一致！'})
            user = UserProfile.objects.get(email=email) # 因为是老用户找回密码所以这个email应该在users_userprofile表中
                                                        # 注意：通过注册和激活的步骤，这个user信息是保存到 users_userprofile中的
            user.password = make_password(pwd1)
            user.save()
            return render(request, 'login.html', {'email': email, 'modify_form': modify_form})   # 在login页面能否回填来自ModifyPwdView的密码？
        else:
            email = request.POST.get('email', '')
            return render(request, 'password_reset.html', {'email': email, 'modify_form': modify_form})


from utils.mixin_utils import LoginRequiredMixin


class UserinfoView(LoginRequiredMixin, View):
    '''
    用户个人信息
    '''
    def get(self, request):
        return render(request, 'usercenter-info.html', {
        })

    def post(self, request):
        user_info_form = UserInfoForm(request.POST, instance=request.user)#一定要指明instance，否则是新增而不是修改, 与用户咨询不一样
        if user_info_form.is_valid():
            user_info_form.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse(json.dumps(user_info_form.errors), content_type='application/json')


class UploadImageView(LoginRequiredMixin, View):
    '''
    用户修改头像
    '''
    def post(self, request):
        image_form = UploadImageForm(request.POST, request.FILES, instance=request.user)        #instance传的就是modelform:UploadImageForm指代的model:UserProfile。 image_form就具有了modelform的功能（里面有model）:直接存
        if image_form.is_valid():
            # image = image_form.cleaned_data['image']
            # request.user.image = image
            # request.user.save()
            image_form.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse('{"status":"fail"}', content_type='application/json')


class UpdatePwdView(View):
    '''
    在个人用户中心修改用户密码
    '''
    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        if modify_form.is_valid():
            pwd1 = request.POST.get('password1', '') #password1,2是password_reset Html页面input框传过来的,email也是。
            pwd2 = request.POST.get('password2', '')
            # email = request.POST.get('email', '')
            if pwd1 != pwd2:
                return HttpResponse('{"status":"fail", "msg":"密码不一致！"}', content_type='application/json')
            user = request.user
            user.password = make_password(pwd1)
            user.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse(json.dumps(modify_form.errors), content_type='application/json')


class SendEmailCodeView(LoginRequiredMixin, View):
    '''
    个人中心修改邮箱时发送邮箱验证码
    '''
    def get(self,request):
        email = request.GET.get('email', '')
        if UserProfile.objects.filter(email=email):
            return HttpResponse('{"email":"邮箱已经存在"}', content_type='application/json')
        send_register_email(email, 'update_email')
        return HttpResponse('{"status":"success"}', content_type='application/json')


class UpdateEmailView(LoginRequiredMixin, View):
    '''
    个人中心拿到验证码后修改个人邮箱
    '''
    def post(self, request):
        email = request.POST.get('email', '')
        code = request.POST.get('code', '') # 为什么是code?     usercenter-base.html中有<input class="fl email_code" type="text" id="jsChangeEmailCode" name="code" placeholder="输入邮箱验证码">

        existed_records = EmailVerifyRecord.objects.filter(email=email, code=code, send_type='update_email')
        if existed_records:
            user = request.user
            user.email = email
            user.save()  # 这样 数据库中userprofile里的邮箱也改成与emailverifyrecord中的邮箱一致了
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse('{"email":"验证码出错"}', content_type='application/json')


class MyEquipmentView(LoginRequiredMixin, View):
    '''
    个人中心 我借用过的设备
    '''
    def get(self, request):
        # 下面这句是我未还的设备
        user_equipments = UserEquipment.objects.filter(return_time__isnull=True, user=request.user)
        # 下面4行代码实现对我用过的设备里同样设备去重
        user_equipments_ids = UserEquipment.objects.filter(user=request.user).values('equipment_id').distinct()
        equipments_list = []
        for user_equipment_id in user_equipments_ids:
            equipments_list += Equipment.objects.filter(id=user_equipment_id['equipment_id'])
        return render(request, 'usercenter-myequipment.html', {
            'user_equipments': user_equipments,
            'equipments_list': equipments_list,

        })


class MyFavTeamView(LoginRequiredMixin, View):
    '''
    个人中心 我收藏的team
    '''
    def get(self, request):
        team_list =[]
        fav_teams = UserFavorite.objects.filter(user=request.user, fav_type=2)
        for fav_team in fav_teams:
            team_id = fav_team.fav_id
            team = Team.objects.get(id=team_id)
            team_list.append(team)
        return render(request, 'usercenter-fav-team.html', {
            'team_list': team_list,

        })


class MyFavEngineerView(LoginRequiredMixin, View):
    '''
    个人中心 我收藏的工程师
    '''
    def get(self, request):
        engineer_list =[]
        fav_engineers = UserFavorite.objects.filter(user=request.user, fav_type=3)
        for fav_engineer in fav_engineers:
            engineer_id = fav_engineer.fav_id
            engineer = Engineer.objects.get(id=engineer_id)
            engineer_list.append(engineer)
        return render(request, 'usercenter-fav-engineer.html', {
            'engineer_list': engineer_list,

        })


class MyFavEquipmentView(LoginRequiredMixin, View):
    '''
    个人中心 我收藏的设备
    '''
    def get(self, request):
        equipment_list =[]
        fav_equipments = UserFavorite.objects.filter(user=request.user, fav_type=1)
        for fav_equipment in fav_equipments:
            equipment_id = fav_equipment.fav_id
            equipment = Equipment.objects.get(id=equipment_id)
            equipment_list.append(equipment)
        return render(request, 'usercenter-fav-equipment.html', {
            'equipment_list': equipment_list,

        })


class MymessageView(LoginRequiredMixin, View):
    '''
    个人中心 我的消息
    '''
    def get(self, request):
        all_messages = UserMessage.objects.filter(user=request.user.id)       #因为operation\models\UserMessage\user不是指向外键UserProfile，而是一个int
        # 用户进入个人消息后清空未读消息记录
        all_unread_messages = UserMessage.objects.filter(user=request.user.id, has_read=False)
        for unread_message in all_unread_messages:
            unread_message.has_read = True
            unread_message.save()

        # 对消息进行分页
        try:  # request.GET  <QueryDict: {'page': ['2']}>
            page = request.GET.get('page', 1)  # 取页数编号 返回的是 1,2 这样的int页数
        except PageNotAnInteger:
            page = 1

        p = Paginator(all_messages, 10, request=request)  # p是Paginator对象类型，all_orgs是QuerySet

        messages = p.page(page)  # orgs是Page类型： Page 1 of 2  / Page 2 of 2

        return render(request, 'usercenter-message.html', {
            "messages": messages,
        })


class MytoolView(LoginRequiredMixin, View):
    '''
    个人中心 我的工具
    '''
    def get(self, request):

        return render(request, 'usercenter-mytool.html', {
        })


class MyQuizView(LoginRequiredMixin, View):
    '''
    个人中心 我的答卷测试
    '''
    def get(self, request):

        return render(request, 'usercenter-myquiz.html', {
        })


def mean(L=[]):
    r = reduce(lambda x,y:x+y,L)
    return r*1.0/len(L)


from django.core.mail import send_mail
from TestLabManagement.settings import EMAIL_FROM
class MytoolUcalView(LoginRequiredMixin, View):
    '''
    个人中心 我的工具  直接测量量不确定度计算
    '''
    def post(self, request):# 对表单form的请求是post
        list_value = []
        test_value1 = request.POST.get('test_value1', '')
        if test_value1:
            list_value.append(float(test_value1))
        test_value2 = request.POST.get('test_value2', '')
        if test_value2:
            list_value.append(float(test_value2))
        test_value3 = request.POST.get('test_value3', '')
        if test_value3:
            list_value.append(float(test_value3))
        test_value4 = request.POST.get('test_value4', '')
        if test_value4:
            list_value.append(float(test_value4))
        test_value5 = request.POST.get('test_value5', '')
        if test_value5:
            list_value.append(float(test_value5))
        test_value6 = request.POST.get('test_value6', '')
        if test_value6:
            list_value.append(float(test_value6))
        test_value7 = request.POST.get('test_value7', '')
        if test_value7:
            list_value.append(float(test_value7))
        test_value8 = request.POST.get('test_value8', '')
        if test_value8:
            list_value.append(float(test_value8))
        test_value9 = request.POST.get('test_value9', '')
        if test_value9:
            list_value.append(float(test_value9))
        test_value10 = request.POST.get('test_value10', '')
        if test_value10:
            list_value.append(float(test_value10))

        Umean = mean(list_value)

        list_temp_submean = [value-Umean for value in list_value]

        list_temp_submean_square = [value**2 for value in list_temp_submean]

        sUx = math.sqrt(sum(list_temp_submean_square) / (len(list_temp_submean_square) - 1))
        # 测量一次报结果，由重复性引入的不确定度
        uUx = sUx/1

        resolution = request.POST.get('resolution', '')
        if resolution:
            resolution = float(resolution)

        # 由仪器分辨力引入的不确定度分量
        uUr = 0.5*resolution/math.sqrt(3)

        readout = request.POST.get('readout', '')
        if readout:
            readout = float(readout)
        range_value = request.POST.get('range_value', '')
        if range_value:
            range_value = float(range_value)
        mpe = request.POST.get('mpe', '')
        if mpe:
            mpe = float(mpe)
        # 由仪表最大允差引入的不确定度
        uUn = mpe/math.sqrt(3)

        # 合成标准不确定度
        uc = math.sqrt(uUx**2 + uUr**2 + uUn**2)

        # 扩展不确定度
        U = 2 * uc

        #下面邮件发送是为了调试用
        email_body = '你输入的重复性评定测量值是：{}\n\n你输入的此次读数：{}\n所用量程是：{}\n仪器最大允许误差(此读数与此量程下)是:{}\n\n仪器分辨力(此量程下)：{}\n\n ----------------------------------\n\n uUx重复性引入的不确定度分量：{} \n\n uUr仪器分辨力引入的不确定度分量:{}\n\n uUn仪表本身引入的不确定度:{}\n\nuc合成标准不确定度是：{}\n\nU扩展不确定度是：{}'.format\
            (list_value, readout, range_value, mpe, resolution, uUx, uUr, uUn, uc, U)
        send_status = send_mail('直接测量量不确定度计算', email_body, EMAIL_FROM, [request.user.email])
        return HttpResponse('{"status":"success","msg":"testing..."}', content_type='application/json')


class MytoolUtcalView(LoginRequiredMixin, View):
    '''
    个人中心 我的工具  pt1000温度测试不确定度计算
    '''
    def post(self, request):# 对表单form的请求是post
        list_value = []
        t_value1 = request.POST.get('t_value1', '')
        if t_value1:
            list_value.append(float(t_value1))
        t_value2 = request.POST.get('t_value2', '')
        if t_value2:
            list_value.append(float(t_value2))
        t_value3 = request.POST.get('test_value3', '')
        if t_value3:
            list_value.append(float(t_value3))
        t_value4 = request.POST.get('t_value4', '')
        if t_value4:
            list_value.append(float(t_value4))
        t_value5 = request.POST.get('t_value5', '')
        if t_value5:
            list_value.append(float(t_value5))
        t_value6 = request.POST.get('t_value6', '')
        if t_value6:
            list_value.append(float(t_value6))
        t_value7 = request.POST.get('t_value7', '')
        if t_value7:
            list_value.append(float(t_value7))
        t_value8 = request.POST.get('t_value8', '')
        if t_value8:
            list_value.append(float(t_value8))
        t_value9 = request.POST.get('t_value9', '')
        if t_value9:
            list_value.append(float(t_value9))
        t_value10 = request.POST.get('t_value10', '')
        if t_value10:
            list_value.append(float(t_value10))

        Umean = mean(list_value)

        list_temp_submean = [value - Umean for value in list_value]

        list_temp_submean_square = [value ** 2 for value in list_temp_submean]

        sUx = math.sqrt(sum(list_temp_submean_square) / (len(list_temp_submean_square) - 1))
        # 测量一次报结果，由重复性引入的不确定度
        uUx = sUx / 1

        t_readout = request.POST.get('t_readout', '')
        if t_readout:
            t_readout = float(t_readout)
        mpe = 0.3 + 0.005*abs(t_readout)
        # 由于传感器的允差引入的不确定度分量
        uUn = mpe / math.sqrt(3)

        resistor = request.POST.get('resistor', '')
        if resistor:
            resistor = float(resistor)
        temp = resistor*0.1/0.391
        # 由于引线电阻引入的不确定度分量
        uUw = temp / math.sqrt(3)

        t_max = request.POST.get('t_max', '')
        if t_max:
            t_max = float(t_max)
        # 由于软件转换引入的不确定度分量
        uUsoft = t_max / math.sqrt(3)

        # 合成标准不确定度
        uc = math.sqrt(uUx ** 2 + uUn ** 2 + uUw ** 2 + uUsoft ** 2)

        # 扩展不确定度
        U = 2 * uc

        #下面邮件发送是为了调试用
        email_body = '你输入的重复性评定测量值是：{}\n\n你输入的此次读数：{}\n\n你输入的引线阻值：{}\n\n你输入的程序转换的最大温度差值：{}\n\n ----------------------------------\n\nuUx重复性引入的不确定度分量：{} \n\n uUn由于传感器的允差引入的不确定度分量:{}\n\n uUw由于引线电阻引入的不确定度分量:{}\n\nuUsoft由于软件转换引入的不确定度分量:{}\n\nuc合成标准不确定度是：{}\n\nU扩展不确定度是：{}'.format\
            (list_value, t_readout, resistor, t_max, uUx, uUn, uUw, uUsoft, uc, U)
        send_status = send_mail('温度测试不确定度计算', email_body, EMAIL_FROM, [request.user.email])
        return HttpResponse('{"status":"success","msg":"testing..."}', content_type='application/json')


class MytoolSafetyQuizView(LoginRequiredMixin, View):
    '''
    个人中心 我的答卷测试  安全培训后测试 如果测试通过在这里发一封邮件给相关人员
    '''
    def post(self, request):# 对表单form的请求是post
        #下面邮件发送是为了调试用
        email_body = '{}:\n\n恭喜你通过了测试，你这次测试的分数是:{}\n\n\n\n\n------------------------------------------------------------\n以上信息来自 Test&Lab管理后台 自动发送内容，请勿回复此邮件！'.format(request.user.username, request.POST.get('score',''))
        send_status = send_mail('测试通过！', email_body, EMAIL_FROM, [request.user.email])
        return HttpResponse('{"status":"success","msg":"通过测试！"}', content_type='application/json')


class IndexView(View):
    '''
    首页
    '''
    def get(self, request):
        # 取出轮播图
        # print (1/0)
        all_banners = Banner.objects.all().order_by('index')
        equipments = Equipment.objects.filter(is_banner=False)[:6]
        banner_equipments = Equipment.objects.filter(is_banner=True)[:3]
        teams = Team.objects.all()[:15]

        # # 查询background_task是否有任务存在并执行
        # if Task.objects.filter(task_name="equipments.tasks.notify_user").exists():
        #     pass
        # else:
        #     notify_user(repeat=60)#向后台注册任务

        # notify_user(repeat=120)#向后台注册任务
        return render(request, 'index.html', {
            'all_banners': all_banners,
            'equipments': equipments,
            'banner_equipments': banner_equipments,
            'teams': teams,
            })


def page_not_found(request):
    # 全局404处理函数
    from django.shortcuts import render_to_response
    response = render_to_response('404.html', {})
    response.status_code = 404
    return response


def page_error(request):
    # 全局500处理函数
    from django.shortcuts import render_to_response
    response = render_to_response('500.html', {})
    response.status_code = 500
    return response





