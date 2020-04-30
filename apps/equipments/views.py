from django.shortcuts import render
from django.views.generic import View
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse

from .models import Equipment, EquipmentVideo, EquipmentResource
from .forms import UserEquipmentForm
from operation.models import UserFavorite, EquipmentComments, UserEquipment, UserEquipmentInadvance
from users.models import UserProfile
from django.core.mail import send_mail
from TestLabManagement.settings import EMAIL_FROM
from django.db.models import Q, Max
from organization.models import Team

from utils.mixin_utils import LoginRequiredMixin


# Create your views here.


class EquipmentsListView(View):
    def get(self, request):
        all_teams = Team.objects.all()

        #  current_page = 'course-list'
        all_equipments = Equipment.objects.all().order_by(
            'add_time')  # QuerySet  <QuerySet [<Course: delphi>, <Course: 操作系统>, <Course: 数据结构>, <Course: djangoORM>, <Course: Java>, <Course: python入门>, <Course: C语言>, <Course: Go语言>, <Course: django入门>, <Course: django入门2>]>
        hot_equipments = Equipment.objects.all().order_by('-click_nums')[:2]  # 根据点击数排名 倒序

        # 设备搜索HttpResponse
        search_keywords = request.GET.get('keywords',
                                          '')  # 这里的keywords是从deco-common.js 62行函数在url中带过来的！！！即用户在页面输入搜索内容点击搜索后跳转到deco-common.js  417、62行运行之后request_url中带上keywords参数跳转到request_url指向的EquipmentsListView中（request.GET.get('keywords', '')就可以获取url中的keywords参数）做搜索后展示出来给用户
        if search_keywords:  # 带个i 就是不区分大小写，还有__lte  __gte
            all_equipments = all_equipments.filter(Q(name__icontains=search_keywords)
                                                   | Q(desc__icontains=search_keywords)
                                                   | Q(detail__icontains=search_keywords))
        # 根据前端页面通过url穿过来的team_id对设备做删选
        team_id = request.GET.get('team_id', '')
        if team_id:
            all_equipments = all_equipments.filter(team_id=int(team_id))

        # 根据Course中的字段students，click_nums课程排序
        sort = request.GET.get('sort', '')  # sort是由前端页面通过URL传过来的空，students或者hot
        if sort:
            if sort == 'click_nums':
                all_equipments = all_equipments.order_by(
                    "-click_nums")  # 如果前端传过来的 是“students”,那么就按照model：Course中的字段students倒序排列
            elif sort == 'reserve_times':
                all_equipments = all_equipments.order_by(
                    "-reserve_times")  # 如果前端传过来的 是“hot”,那么就按照model：Course中的字段click_nums倒序排列

        equip_nums = all_equipments.count()

        # 对课程进行分页
        try:  # request.GET  <QueryDict: {'page': ['2']}>
            page = request.GET.get('page', 1)  # 取页数编号 返回的是 1,2 这样的int页数
        except PageNotAnInteger:
            page = 1

        p = Paginator(all_equipments, 4, request=request)  # p是Paginator对象类型，all_orgs是QuerySet

        equipments = p.page(
            page)  # courses是Page类型： <Page 1 of 4>,它的object_list：<QuerySet [<Course: delphi>, <Course: 操作系统>, <Course: 数据结构>]>

        return render(request, 'equipment-list.html', {
            'all_teams': all_teams,
            'team_id': team_id,
            'all_equipments': equipments,
            'sort': sort,
            'equip_nums': equip_nums,
            'hot_equipments': hot_equipments,
            # # 'current_page': current_page,

        })


# from django.utils.dateparse import parse_datetime
# from django.utils.timezone import is_aware, make_aware
#
# def get_aware_datetime(date_str):
#     ret = parse_datetime(date_str)
#     if not is_aware(ret):
#         ret = make_aware(ret)
#     return ret

from django.utils.timezone import get_current_timezone
from datetime import datetime

tz = get_current_timezone()


class UserReserveEquipmentView(View):
    '''
    用户借用/预定（含取消）设备
    '''

    def post(self, request):  # 对表单form的请求是post
        if not Equipment.objects.get(
                name=request.POST.get('equipment')).reservable_inadvance:  # reserve页面点击按钮后 不能提前预定设备的逻辑到这里
            if request.user.is_authenticated():
                user_id = request.user.id  # 外键传id是可以的
                # user = request.user#外键传类是可以的，但是到了后面的user_reserve_form.is_valid过不去
                borrow_time = datetime.now()
                plan_to_return_time = request.POST.get('plan_to_return_time', '')
                if plan_to_return_time != '' and len(plan_to_return_time) >= 19:
                    plan_to_return_time = datetime.strptime(plan_to_return_time, "%Y-%m-%dT%H:%M:%S")
                elif plan_to_return_time != '' and len(plan_to_return_time) < 19:
                    plan_to_return_time = datetime.strptime(plan_to_return_time, "%Y-%m-%dT%H:%M")
                else:
                    return HttpResponse('{"status":"fail","msg":"计划归还日期非法，无法借用"}', content_type='application/json')
                equipment_id = (Equipment.objects.get(name=request.POST.get('equipment'))).id  # 外键传id是可以的
                # equipment = (Equipment.objects.get(name=request.POST.get('equipment')))  # 外键传类是可以的 但是到了后面的user_reserve_form.is_valid过不去
                user_reserve_form = UserEquipmentForm({'user': user_id, 'borrow_time': borrow_time,
                                                       'plan_to_return_time': plan_to_return_time,
                                                       'equipment': equipment_id})
                if (plan_to_return_time >= borrow_time) and (
                        Equipment.objects.get(name=request.POST.get('equipment')).status == 'Active'):
                    if user_reserve_form.is_valid():
                        # Equipment.objects.get(name=request.POST.get('equipment')).has_checked_before_return = False
                        # Equipment.objects.get(name=request.POST.get('equipment')).save()
                        equip = Equipment.objects.get(name=request.POST.get('equipment'))
                        equip.has_checked_before_return = False
                        equip.save()
                        user_equipment = user_reserve_form.save(commit=True)
                        # 发送邮件给借用者,此设备被成功预定请到责任人那里取用
                        email_title = 'Test&Lab预定设备成功通知！'
                        email_body = '亲爱的用户{0}:\n恭喜您预定到了下面的设备:{1},{2}\n计划归还日期是：{3}\n请联系设备责任人{4}取用\n\n\n\n\n------------------------------------------------------------\n以上信息来自 Test&Lab管理后台 自动发送内容，请勿回复此邮件！' \
                            .format(UserProfile.objects.get(id=user_id).username,
                                    Equipment.objects.get(name=request.POST.get('equipment')).item,
                                    Equipment.objects.get(name=request.POST.get('equipment')).name,
                                    plan_to_return_time,
                                    Equipment.objects.get(name=request.POST.get('equipment')).responsible_person)
                        send_status = send_mail(email_title, email_body, EMAIL_FROM,
                                                [(UserProfile.objects.get(id=user_id)).email])

                        # 发送邮件给设备责任人此设备已经预定，请把设备给他
                        email_body = '亲爱的设备责任人{0}:\n\n现有一个设备:{1},{2} 被预定或借用。\n计划归还日期是：{3}\n请将设备转交给借用人{4}\n\n\n\n\n------------------------------------------------------------\n以上信息来自 Test&Lab管理后台 自动发送内容，请勿回复此邮件！' \
                            .format(Equipment.objects.get(id=equipment_id).responsible_person.name,
                                    Equipment.objects.get(name=request.POST.get('equipment')).item,
                                    Equipment.objects.get(name=request.POST.get('equipment')).name,
                                    plan_to_return_time,
                                    UserProfile.objects.get(id=user_id).username)
                        send_status = send_mail(email_title, email_body, EMAIL_FROM,
                                                [Equipment.objects.get(id=equipment_id).responsible_person.email])

                        if send_status:
                            # 给用户个人中心发个消息说你已经借用了这个设备
                            from operation.models import UserMessage
                            user_message = UserMessage()
                            user_message.user = user_id  # 因为operation\models\UserMessage\user不是指向外键UserProfile，而是一个int
                            user_message.message = "您成功预定了此设备{0}-{1}".format(
                                (Equipment.objects.get(name=request.POST.get('equipment'))).item,
                                (Equipment.objects.get(name=request.POST.get('equipment'))).name)
                            user_message.save()
                            # 增加此设备的预定次数
                            equip = Equipment.objects.get(id=equipment_id)
                            equip.reserve_times += 1
                            equip.save()
                            return HttpResponse('{"status":"success"}', content_type='application/json')
                    else:
                        return HttpResponse('{"status":"fail","msg":"无法借用"}', content_type='application/json')
                else:
                    return HttpResponse('{"status":"fail","msg":"日期非法或者设备不可用，无法借用"}', content_type='application/json')
            else:
                return HttpResponse('{"status":"fail","msg":"无法借用,请先登录"}', content_type='application/json')
        else:  # reserve页面点击按钮后 可提前预定设备的逻辑到这里了
            if request.user.is_authenticated():
                if 'reserve_id' in request.POST:
                    # 前端ajax form POST 过来的数据里有reserve_id字段，说明用户点击的是 取消预订 不是 预订
                    # #下面邮件发送是为了调试用
                    # email_body = 'request.POST有啥：{}' \
                    #     .format(request.POST)
                    # send_status = send_mail('测试request.POST有啥', email_body, EMAIL_FROM,
                    #                         ['419099632@qq.com'])
                    reserve_id = request.POST.get('reserve_id', '')
                    if reserve_id != '':
                        reserve_id = int(reserve_id)
                        # 删除之前要判断这个 预定 id是否存在？,而且还要检查是不是本人在 取消操作，一定要本人才能取消
                        reserve_ids = [userequipmentinadvance.id for userequipmentinadvance in
                                       UserEquipmentInadvance.objects.filter(equipment=Equipment.objects.get(
                                           name=request.POST.get('equipment')))]  # 找到此设备的提前预定id列表
                        if reserve_id in reserve_ids:
                            if UserEquipmentInadvance.objects.get(id=reserve_id).user == request.user:
                                UserEquipmentInadvance.objects.get(id=reserve_id).delete()
                                return HttpResponse('{"status":"success","msg":"取消预订成功！"}',
                                                    content_type='application/json')
                            else:
                                return HttpResponse('{"status":"fail","msg":"你无权取消此预定"}',
                                                    content_type='application/json')
                        else:
                            return HttpResponse('{"status":"fail","msg":"预定ID无效"}', content_type='application/json')
                    else:
                        return HttpResponse('{"status":"fail","msg":"死鬼，输入想取消的预定ID了吗？"}',
                                            content_type='application/json')
                # 前端ajax form POST 过来的数据里没有reserve_id字段，说明用户点击的是 预定 而不是点击 取消预订
                borrow_time = request.POST.get('borrow_time', '')
                # 16 与 19的判断是为了适配苹果手机操作  预定
                if borrow_time != '' and len(borrow_time) == 19:
                    # # #下面邮件发送是为了调试用
                    # email_body = 'borrow_time:{}其类型:{}和长度：{}' \
                    #     .format(borrow_time, type(borrow_time), len(borrow_time))
                    # send_status = send_mail('手机操作测试borrow_time是什么东西？其类型是,长度是', email_body, EMAIL_FROM,
                    #                         ['419099632@qq.com'])
                    borrow_time = datetime.strptime(borrow_time, "%Y-%m-%dT%H:%M:%S")
                elif borrow_time != '' and len(borrow_time) == 16:
                    borrow_time = datetime.strptime(borrow_time, "%Y-%m-%dT%H:%M")
                else:
                    return HttpResponse('{"status":"fail","msg":"起始时间非法，无法预定"}', content_type='application/json')

                plan_to_return_time = request.POST.get('plan_to_return_time', '')
                if plan_to_return_time != '' and len(plan_to_return_time) == 19:
                    plan_to_return_time = datetime.strptime(plan_to_return_time, "%Y-%m-%dT%H:%M:%S")
                elif plan_to_return_time != '' and len(plan_to_return_time) == 16:
                    plan_to_return_time = datetime.strptime(plan_to_return_time, "%Y-%m-%dT%H:%M")
                else:
                    return HttpResponse('{"status":"fail","msg":"计划归还日期非法，无法预定"}', content_type='application/json')

                equipment = (Equipment.objects.get(name=request.POST.get('equipment')))

                userequipmentsinadvance_log = UserEquipmentInadvance.objects.filter(equipment=equipment,
                                                                                    return_time=None).order_by(
                    'borrow_time')
                # #下面邮件发送是为了调试用
                # email_body = '找到userequipmentsinadvance_log:{}\n\n及其长度{}' \
                #     .format(userequipmentsinadvance_log, len(userequipmentsinadvance_log))
                # send_status = send_mail('测试userequipmentsinadvance_log', email_body, EMAIL_FROM,
                #                         ['419099632@qq.com'])
                if userequipmentsinadvance_log:
                    if len(userequipmentsinadvance_log) == 1:  # 此设备只有一条预定记录
                        if (borrow_time >= userequipmentsinadvance_log[
                            0].plan_to_return_time and plan_to_return_time >= borrow_time >= datetime.now() and equipment.status == 'Active') or \
                                (plan_to_return_time <= userequipmentsinadvance_log[
                                    0].borrow_time and plan_to_return_time >= borrow_time >= datetime.now() and equipment.status == 'Active'):
                            user_equip_inadvance = UserEquipmentInadvance()
                            user_equip_inadvance.user = request.user
                            user_equip_inadvance.borrow_time = borrow_time
                            user_equip_inadvance.plan_to_return_time = plan_to_return_time
                            user_equip_inadvance.equipment = equipment
                            user_equip_inadvance.add_time = datetime.now()
                            user_equip_inadvance.save()
                            return HttpResponse('{"status":"success"}', content_type='application/json')
                        else:
                            return HttpResponse('{"status":"fail","msg":"此段时间已经被预定或时间非法或者设备不可用！"}',
                                                content_type='application/json')
                    else:  # 此设备有2条以上预定记录
                        # # 下面邮件发送是为了调试用
                        # email_body = '进入，len(userequipmentsinadvance_log)：{}' \
                        #     .format(len(userequipmentsinadvance_log))
                        # send_status = send_mail('测试len(userequipmentsinadvance_log)', email_body, EMAIL_FROM,
                        #                         ['419099632@qq.com'])
                        for i in range(len(userequipmentsinadvance_log) - 1):
                            # # 下面邮件发送是为了调试用
                            # email_body = '进入for循环，循环变量i：{}' \
                            #     .format(i)
                            # send_status = send_mail('测试len(userequipmentsinadvance_log)', email_body, EMAIL_FROM,
                            #                         ['419099632@qq.com'])
                            if (borrow_time >= userequipmentsinadvance_log[
                                i].plan_to_return_time and plan_to_return_time >= borrow_time >= datetime.now() \
                                and plan_to_return_time <= userequipmentsinadvance_log[
                                    i + 1].borrow_time and equipment.status == 'Active') or \
                                    (borrow_time >= userequipmentsinadvance_log[len(
                                        userequipmentsinadvance_log) - 1].plan_to_return_time and plan_to_return_time >= borrow_time >= datetime.now() and equipment.status == 'Active') or \
                                    (plan_to_return_time <= userequipmentsinadvance_log[
                                        0].borrow_time and plan_to_return_time >= borrow_time >= datetime.now() and equipment.status == 'Active'):
                                user_equip_inadvance = UserEquipmentInadvance()
                                user_equip_inadvance.user = request.user
                                user_equip_inadvance.borrow_time = borrow_time
                                user_equip_inadvance.plan_to_return_time = plan_to_return_time
                                user_equip_inadvance.equipment = equipment
                                user_equip_inadvance.add_time = datetime.now()
                                user_equip_inadvance.save()
                                return HttpResponse('{"status":"success"}', content_type='application/json')

                        # # 下面邮件发送是为了调试用
                        # email_body = '进入for循环，循环变量i：{}' \
                        #     .format(i)
                        # send_status = send_mail('测试len(userequipmentsinadvance_log)', email_body, EMAIL_FROM,
                        #                         ['419099632@qq.com'])
                        return HttpResponse('{"status":"fail","msg":"此段时间已经被预定或时间非法或者设备不可用！"}',
                                            content_type='application/json')
                else:  # 这个设备是第一次被预定
                    if (plan_to_return_time >= borrow_time >= datetime.now()) and (equipment.status == 'Active'):
                        user_equip_inadvance = UserEquipmentInadvance()
                        user_equip_inadvance.user = request.user
                        user_equip_inadvance.borrow_time = borrow_time
                        user_equip_inadvance.plan_to_return_time = plan_to_return_time
                        user_equip_inadvance.equipment = equipment
                        user_equip_inadvance.add_time = datetime.now()
                        user_equip_inadvance.save()
                        return HttpResponse('{"status":"success"}', content_type='application/json')
                    else:
                        return HttpResponse('{"status":"fail","msg":"日期非法或者设备不可用，无法预定"}',
                                            content_type='application/json')
                # # 依据equipment找出提前预定设备的表格中plan_to_return_time字段最大的值
                # args = UserEquipmentInadvance.objects.filter(equipment=equipment)
                # max_time_plantoreturn = args.aggregate(Max('plan_to_return_time'))['plan_to_return_time__max']
                # #下面邮件发送是为了调试用
                # email_body = '找到args（UserEquipmentInadvance的qureyset）:{}\n\nmax_time_plantoreturn:{}\n\nborrow_time:{}' \
                #     .format(args, max_time_plantoreturn, borrow_time)
                # send_status = send_mail('测试max_time_plantoreturn', email_body, EMAIL_FROM,
                #                         ['419099632@qq.com'])

                # if max_time_plantoreturn: # 如果之前这个设备有了预定的记录
                #     if (plan_to_return_time >= borrow_time >= datetime.now()) and (borrow_time > max_time_plantoreturn) and (equipment.status == 'Active'):
                #         user_equip_inadvance = UserEquipmentInadvance()
                #         user_equip_inadvance.user = request.user
                #         user_equip_inadvance.borrow_time = borrow_time
                #         user_equip_inadvance.plan_to_return_time = plan_to_return_time
                #         user_equip_inadvance.equipment = equipment
                #         user_equip_inadvance.add_time = datetime.now()
                #         user_equip_inadvance.save()
                #         return HttpResponse('{"status":"success"}', content_type='application/json')
                #     else:
                #         return HttpResponse('{"status":"fail","msg":"日期非法或者设备不可用，无法预定"}', content_type='application/json')
                # else: # 这个设备是第一次被预定
                #     if (plan_to_return_time >= borrow_time >= datetime.now()) and (equipment.status == 'Active'):
                #         user_equip_inadvance = UserEquipmentInadvance()
                #         user_equip_inadvance.user = request.user
                #         user_equip_inadvance.borrow_time = borrow_time
                #         user_equip_inadvance.plan_to_return_time = plan_to_return_time
                #         user_equip_inadvance.equipment = equipment
                #         user_equip_inadvance.add_time = datetime.now()
                #         user_equip_inadvance.save()
                #         return HttpResponse('{"status":"success"}', content_type='application/json')
                #     else:
                #         return HttpResponse('{"status":"fail","msg":"日期非法或者设备不可用，无法预定"}', content_type='application/json')
            else:
                return HttpResponse('{"status":"fail","msg":"无法操作,请先登录"}', content_type='application/json')


class UserReturnEquipmentView(View):
    '''
    用户归还设备
    '''

    def post(self, request):  # 对表单form的请求是post
        # user = request.user.id #只能用下一句 确保只能借用的那个人才能归还
        user_id = (UserProfile.objects.get(username=request.POST.get('user'))).id  # 这里的user_id是前端返回的最近一次借用这个设备的用户id
        equipment_id = (Equipment.objects.get(name=(request.POST.get('equipment')))).id
        # 下面是判断如果是设备责任人点击 可以归还 到了这里的话说明他已经查验了设备允许借用人归还操作
        if request.user.is_authenticated() and request.user.email == Equipment.objects.get(
                id=equipment_id).responsible_person.email \
                and Equipment.objects.get(id=equipment_id).has_checked_before_return == False:
            equip = Equipment.objects.get(id=equipment_id)
            equip.has_checked_before_return = True
            equip.save()
            return HttpResponse('{"status":"fail", "msg":"谢谢你的查验"}', content_type='application/json')
        if request.user.is_authenticated() and user_id == request.user.id:  # 这里判断了目前登录用户是不是最近借用(使用)此设备的那个用户
            if Equipment.objects.get(id=equipment_id).has_checked_before_return == False:
                return HttpResponse('{"status":"fail","msg":"请联系设备责任人查验设备后进行归还！"}', content_type='application/json')
            borrow_time = request.POST.get('borrow_time', '')
            # # 下面邮件发送是为了调试用
            # email_body = 'borrow_id:{} ' \
            #     .format(request.POST.get('borrow_id', ''))
            # send_status = send_mail('手机操作测试borrow_id是什么东西', email_body, EMAIL_FROM,
            #                         ['419099632@qq.com'])
            if borrow_time != '' and len(borrow_time) >= 19:
                borrow_time = datetime.strptime(borrow_time, "%Y年%m月%d日 %H:%M:%S")
            elif borrow_time != '' and (len(borrow_time) < 19):
                borrow_time = datetime.strptime(borrow_time, "%Y年%m月%d日 %H:%M")
            else:
                return HttpResponse('{"status":"fail","msg":"借用日期非法，无法借用"}', content_type='application/json')

            plan_to_return_time = request.POST.get('plan_to_return_time', '')

            if plan_to_return_time != '' and len(plan_to_return_time) >= 19:
                plan_to_return_time = datetime.strptime(plan_to_return_time, "%Y年%m月%d日 %H:%M:%S")
            elif plan_to_return_time != '' and (len(plan_to_return_time) < 19):
                plan_to_return_time = datetime.strptime(plan_to_return_time, "%Y年%m月%d日 %H:%M")
            else:
                return HttpResponse('{"status":"fail","msg":"计划归还日期非法，无法借用"}', content_type='application/json')

            return_time = datetime.now()
            equ = Equipment.objects.get(name=(request.POST.get('equipment')))

            if not equ.reservable_inadvance:  # 对于  不可预定设备  的归还走到这里
                user_equipments_return = UserEquipment.objects.filter(borrow_time__hour=borrow_time.hour,
                                                                      borrow_time__minute=borrow_time.minute,
                                                                      borrow_time__month=borrow_time.month,
                                                                      borrow_time__day=borrow_time.day,
                                                                      equipment=equ, user=request.user)
                user_equipment_x = user_equipments_return[len(user_equipments_return) - 1]
                user_reserve_form = UserEquipmentForm(
                    {'user': user_id, 'borrow_time': borrow_time, 'plan_to_return_time': plan_to_return_time,
                     'return_time': return_time, 'equipment': equipment_id},
                    instance=user_equipment_x)
                if return_time >= borrow_time:
                    if user_reserve_form.is_valid():
                        user_equipment = user_reserve_form.save(commit=True)
                        # 给用户个人中心发个消息说你已经归还了这个设备
                        from operation.models import UserMessage
                        user_message = UserMessage()
                        user_message.user = user_id  # 因为operation\models\UserMessage\user不是指向外键UserProfile，而是一个int
                        user_message.message = "您归还了此设备{0}-{1}".format(equ.item, equ.name)
                        user_message.save()
                        return HttpResponse('{"status":"success"}', content_type='application/json')
                    else:
                        return HttpResponse('{"status":"fail","msg":"无法归还"}', content_type='application/json')
                else:
                    return HttpResponse('{"status":"fail","msg":"日期非法，无法归还"}', content_type='application/json')
            else:  # 对于  可预定设备  的归还走到这里
                if return_time >= borrow_time:
                    # UserEquipmentInadvance.objects.get(id=int(request.POST.get('reserve_id'))).return_time = return_time
                    # UserEquipmentInadvance.objects.get(id=int(request.POST.get('reserve_id'))).save()
                    userequipmentinadvance_return = UserEquipmentInadvance.objects.get(
                        id=int(request.POST.get('reserve_id')))
                    userequipmentinadvance_return.return_time = return_time
                    userequipmentinadvance_return.save()
                    # 给用户个人中心发个消息说你已经归还了这个设备
                    from operation.models import UserMessage
                    user_message = UserMessage()
                    user_message.user = user_id  # 因为operation\models\UserMessage\user不是指向外键UserProfile，而是一个int
                    user_message.message = "您归还了此设备{0}-{1}".format(equ.item, equ.name)
                    user_message.save()
                    # 把这条预定和使用记录里设备的has_checked_before_return从True(设备责任人将之改成了True)改成False,即此条预定/使用记录完成了，拜拜
                    userequipmentinadvance_return.equipment.has_checked_before_return = False
                    userequipmentinadvance_return.equipment.save()
                    # 还前增加此设备的预定次数
                    equip = Equipment.objects.get(id=equipment_id)
                    equip.reserve_times += 1
                    equip.save()
                    # 把设备从预定状态进入到借用状态的邮件发送标志位改成False 即允许下一个进入借用状态的设备发送通知邮件
                    from equipments.tasks import has_sentmail_userequipmentinadvance_to_using
                    has_sentmail_userequipmentinadvance_to_using = False
                    return HttpResponse('{"status":"success"}', content_type='application/json')
                else:
                    return HttpResponse('{"status":"fail","msg":"日期非法，无法归还"}', content_type='application/json')
        else:
            return HttpResponse('{"status":"fail","msg":"无法归还,请联系借用人归还"}', content_type='application/json')


class VideoPlayView(View):
    '''
    视频播放页面 与equipment-info.html的view:EquipmentInfoView一样要传递设备的相关信息到页面
    '''

    def get(self, request, video_id):
        # 根据video_id找到这个视频
        video = EquipmentVideo.objects.get(id=int(video_id))
        equipment = video.equipment
        # 根据上面设备找到点击过这个设备的“设备信息”（Equipment类）的UserEquipment有哪些？返回是UserEquipment类型的表格
        user_equipments = UserEquipment.objects.filter(equipment=equipment)
        # 找到所有用过这个设备的用户的id; 取出UserCourse中所有用户id
        user_ids = [user_equipment.user.id for user_equipment in user_equipments]
        # 找到上面id的所有用户使用过的所有设备
        all_user_equipments = UserEquipment.objects.filter(
            user_id__in=user_ids)  # UserCourse有一个外键User,在UserCourse数据库中实际是以user_id存储
        # 取出所有设备的id
        equipment_ids = [user_equipment.equipment.id for user_equipment in all_user_equipments]
        # 获取用过该设备并且还用过的其他设备里面前5个
        relate_equipments = Equipment.objects.filter(id__in=equipment_ids).order_by('-click_nums')[:5]

        all_resources = EquipmentResource.objects.filter(equipment=equipment)
        return render(request, 'equipmen-play.html', {
            "equipment": equipment,  # Model中的Equipment类
            "all_resources": all_resources,
            "relate_equipments": relate_equipments,
            'video': video,
        })


class EquipDetailView(View):
    '''
    设备详情页
    '''

    def get(self, request, equipment_id):
        equipment = Equipment.objects.get(id=int(equipment_id))  # Model中的Course类
        #
        # 增加设备点击数
        equipment.click_nums += 1
        equipment.save()
        #
        has_fav_equipment = False
        has_fav_team = False
        # 与orgationzation\views\OrgHomeView,OrgCourseView,OrgDescView及OrgTeacherView对比
        if request.user.is_authenticated():  # int(course_id)??
            if UserFavorite.objects.filter(user=request.user, fav_id=equipment.id, fav_type=1):
                has_fav_equipment = True
            if UserFavorite.objects.filter(user=request.user, fav_id=equipment.team.id, fav_type=2):
                has_fav_team = True

        tag = equipment.tag
        if tag:
            relate_equipments = Equipment.objects.filter(tag=tag)[:2]
        else:
            relate_equipments = []
        return render(request, 'equipment-detail.html', {
            "equipment": equipment,  # Model中的Course类
            'relate_equipments': relate_equipments,  # Model中的Course类
            # 这里与organization\views\OrgXXXView不同，只需要传递到上一级页面就被使用了,而organization\views\OrgXXXView四个是传递两级到org-base.html被使用的
            'has_fav_equipment': has_fav_equipment,
            # 传递到course-detail.html(这里用到了 {% if has_fav_course %}已收藏{% else %}收藏{% endif %})
            'has_fav_team': has_fav_team,  # 传递到course-detail.html(这里用到了 {% if has_fav_org %}已收藏{% else %}收藏{% endif %})

        })


class EquipmentInfoView(LoginRequiredMixin, View):
    '''
     点击  设备信息 的响应函数
    '''

    def get(self, request, equipment_id):
        # 根据equipment_id找到这个设备
        equipment = Equipment.objects.get(id=int(equipment_id))
        # # 查询用户是否关联了此课程. 不需要，因为我这里UserEquipment只和预定有关
        # user_courses = UserCourse.objects.filter(user=request.user, course=course)
        # if not user_courses:
        #     user_course = UserCourse(user=request.user, course=course)
        #     user_course.save()
        #
        # 根据上面设备找到点击过这个设备的“设备信息”（Equipment类）的UserEquipment有哪些？返回是UserEquipment类型的表格
        user_equipments = UserEquipment.objects.filter(equipment=equipment)
        # 找到所有用过这个设备的用户的id; 取出UserCourse中所有用户id
        user_ids = [user_equipment.user.id for user_equipment in user_equipments]
        # 找到上面id的所有用户使用过的所有设备
        all_user_equipments = UserEquipment.objects.filter(
            user_id__in=user_ids)  # UserCourse有一个外键User,在UserCourse数据库中实际是以user_id存储
        # 取出所有设备的id
        equipment_ids = [user_equipment.equipment.id for user_equipment in all_user_equipments]
        # 获取用过该设备并且还用过的其他设备里面前5个
        relate_equipments = Equipment.objects.filter(id__in=equipment_ids).order_by('-click_nums')[:5]

        all_resources = EquipmentResource.objects.filter(equipment=equipment)
        return render(request, 'equipment-info.html', {
            "equipment": equipment,  # Model中的Equipment类
            "all_resources": all_resources,
            "relate_equipments": relate_equipments,

        })


class CommentsView(LoginRequiredMixin, View):
    def get(self, request, equipment_id):
        equipment = Equipment.objects.get(id=int(equipment_id))

        # ####################################与CommentsView中的一样
        # # 查询用户是否关联了此课程 不需要，因为我这里UserEquipment只和预定有关
        # user_courses = UserCourse.objects.filter(user=request.user, course=course)
        # if not user_courses:
        #     user_course = UserCourse(user=request.user, course=course)
        #     user_course.save()
        #
        # 根据上面设备找到点击过这个设备的“设备信息”（Equipment类）的UserEquipment有哪些？返回是UserEquipment类型的表格
        user_equipments = UserEquipment.objects.filter(equipment=equipment)
        # 找到所有用过这个设备的用户的id; 取出UserCourse中所有用户id
        user_ids = [user_equipment.user.id for user_equipment in user_equipments]
        # 找到上面id的所有用户使用过的所有设备
        all_user_equipments = UserEquipment.objects.filter(
            user_id__in=user_ids)  # UserCourse有一个外键User,在UserCourse数据库中实际是以user_id存储
        # 取出所有设备的id
        equipment_ids = [user_equipment.equipment.id for user_equipment in all_user_equipments]
        # 获取用过该设备并且还用过的其他设备里面前5个
        relate_equipments = Equipment.objects.filter(id__in=equipment_ids).order_by('-click_nums')[:5]
        # ####################################
        all_resources = EquipmentResource.objects.filter(equipment=equipment)
        all_comments = EquipmentComments.objects.filter(equipment=equipment)

        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1

        p = Paginator(all_comments, 3, request=request)

        comments = p.page(page)

        return render(request, 'equipment-comment.html', {
            "equipment": equipment,  # Model中的Course类
            "all_resources": all_resources,
            "all_comments": comments,
            # #####################################
            "relate_equipments": relate_equipments,
            # #####################################

        })


class AddCommentsView(View):
    '''
    用户添加设备评论到数据库中
    '''

    def post(self, request):  # ajax  在course-comment.html中有url:"{% url 'course:add_comments' %}",
        if not request.user.is_authenticated():  # 无论是否有用户登录，request都有一个user 有一个这个方法
            # 判断用户登录状态
            return HttpResponse('{"status":"fail","msg":"用户未登录"}', content_type='application/json')

        equipment_id = request.POST.get('equipment_id', 0)
        comments = request.POST.get('comments', '')
        if int(equipment_id) > 0 and comments:
            equipment_comments = EquipmentComments()
            equipment = Equipment.objects.get(id=int(equipment_id))  # get：只能取出一条数据，如果满足这个条件的数据有多条或者没有数据会抛出一个异常
            # filter:如果有数据就返回一个QueseySet(可遍历)，如果没有数据返回空的QueseySet，不会抛异常
            equipment_comments.user = request.user
            equipment_comments.equipment = equipment
            # equipment_comments.user_id = request.user.id  #这么写也可以
            # equipment_comments.equipment_id = equipment.id  #这么写也可以
            equipment_comments.comments = comments
            equipment_comments.save()
            return HttpResponse('{"status":"success","msg":"添加成功"}', content_type='application/json')
        else:
            return HttpResponse('{"status":"fail","msg":"添加失败"}', content_type='application/json')


class ReserveView(LoginRequiredMixin, View):
    def get(self, request, equipment_id):
        equipment = Equipment.objects.get(id=int(equipment_id))
        if not equipment.reservable_inadvance:
            # ####################################与CommentsView中的一样
            # # 查询用户是否关联了此课程 不需要，因为我这里UserEquipment只和预定有关
            # user_courses = UserCourse.objects.filter(user=request.user, course=course)
            # if not user_courses:
            #     user_course = UserCourse(user=request.user, course=course)
            #     user_course.save()
            #
            # 根据上面设备找到点击过这个设备的“设备信息”（Equipment类）的UserEquipment有哪些？返回是UserEquipment类型的表格
            user_equipments = UserEquipment.objects.filter(equipment=equipment)
            # 找到所有借用过这个设备的用户的id; 取出UserEquipment中所有用户id
            user_ids = [user_equipment.user.id for user_equipment in user_equipments]
            # 找到上面id的所有用户使用过的所有设备
            all_user_equipments = UserEquipment.objects.filter(
                user_id__in=user_ids)
            # 取出所有设备的id
            equipment_ids = [user_equipment.equipment.id for user_equipment in all_user_equipments]
            # 获取用过该设备并且还用过的其他设备里面前5个
            relate_equipments = Equipment.objects.filter(id__in=equipment_ids).order_by('-click_nums')[:5]
            # ####################################
            all_resources = EquipmentResource.objects.filter(equipment=equipment)
            all_comments = EquipmentComments.objects.filter(equipment=equipment)

            if equipment.get_last_borrow_user():
                duration = datetime.now() - equipment.get_last_borrow_user().borrow_time
                return_time = equipment.get_last_borrow_user().return_time
            else:
                duration = 0
                return_time = datetime.now()

            return render(request, 'equipment-reserve.html', {
                "equipment": equipment,
                "all_resources": all_resources,
                "all_comments": all_comments,
                'duration': duration,
                'return_time': return_time,
                # #####################################
                "relate_equipments": relate_equipments,
                # #####################################
            })
        else:
            # 根据上面设备找到点击过这个设备的“设备信息”（Equipment类）的UserEquipmentInadvance有哪些？返回是UserEquipmentInadvance类型的表格
            user_equipmentsinadvance = UserEquipmentInadvance.objects.filter(equipment=equipment)
            # 找到所有提前预定了这个设备的用户的id; 取出UserEquipmentInadvance中所有用户id
            user_ids = [user_equipmentinadvance.user.id for user_equipmentinadvance in user_equipmentsinadvance]
            # 找到上面id的所有用户提前预定过的所有设备
            all_user_equipmentsinadvance = UserEquipmentInadvance.objects.filter(user_id__in=user_ids)
            # 取出所有设备的id
            equipment_ids = [user_equipmentinadvance.equipment.id for user_equipmentinadvance in
                             all_user_equipmentsinadvance]
            # 获取提前预定过该设备并且还预定过的其他设备里面前5个
            relate_equipments = Equipment.objects.filter(id__in=equipment_ids).order_by('-click_nums')[:5]
            # ####################################
            all_resources = EquipmentResource.objects.filter(equipment=equipment)
            all_comments = EquipmentComments.objects.filter(equipment=equipment)
            # 获得此设备的提前预定记录,不包括已经还掉的（return_time=None）
            user_borrow_equipmentsinadvance = UserEquipmentInadvance.objects.filter(equipment=equipment,
                                                                                    return_time=None).order_by(
                'borrow_time')
            # # #下面邮件发送是为了调试用
            # email_body = 'user_borrow_equipmentsinadvance有啥：{}' \
            #     .format(user_borrow_equipmentsinadvance)
            # send_status = send_mail('测试user_borrow_equipmentsinadvance有啥', email_body, EMAIL_FROM,
            #                         ['419099632@qq.com'])
            if user_borrow_equipmentsinadvance:
                # 要考虑长时间没有人来点这个设备的预定页面导致 有多条预定记录在的话怎么办
                if user_borrow_equipmentsinadvance[
                    0].borrow_time < datetime.now():  # < user_equipmentsinadvance[0].plan_to_return_time:
                    # 修改进入使用状态的borrow_time最前的预定设备条目为在用设备
                    # (设备的 还前检查属性 在line358用户点击归还的时候从True(归还的时候由设备责任人从False改成了True)改成False)
                    # #下面邮件发送是为了调试用
                    # email_body = 'user_borrow_equipmentsinadvance[0].borrow_time有啥：{},\n\n datetime.now():{}' \
                    #     .format(user_borrow_equipmentsinadvance[0].borrow_time, datetime.now())
                    # send_status = send_mail('测试user_borrow_equipmentsinadvance[0].borrow_time有啥', email_body,
                    #                         EMAIL_FROM,
                    #                         ['419099632@qq.com'])
                    userequipmentinadvance0isusing = user_borrow_equipmentsinadvance[0]
                    if len(user_borrow_equipmentsinadvance) > 1:
                        user_borrow_equipmentsinadvance = user_borrow_equipmentsinadvance[1:]
                    else:
                        user_borrow_equipmentsinadvance = None
                else:
                    userequipmentinadvance0isusing = None
            else:
                userequipmentinadvance0isusing = None
            return render(request, 'equipment-reserve.html', {
                "equipment": equipment,
                "all_resources": all_resources,
                "all_comments": all_comments,
                # 'duration': duration,
                # 'return_time': return_time,
                # #####################################
                "relate_equipments": relate_equipments,
                # #####################################
                'current_using_userequipmentinadvance': userequipmentinadvance0isusing,
                'reserve_log_userequipmentinadvance': user_borrow_equipmentsinadvance,

            })
