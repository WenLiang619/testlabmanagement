from django.shortcuts import render
from django.views.generic import View
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.db.models import Q

from .models import Location, Team, Engineer
from .forms import UserAskForm

from operation.models import UserFavorite
from equipments.models import Equipment

from utils.mixin_utils import LoginRequiredMixin
# Create your views here.


class OrgView(View):
    """
    team列表功能
    """
    def get(self, request):
        all_teams = Team.objects.all()
        hot_teams = all_teams.order_by('-click_nums')[:2]
        all_locations = Location.objects.all()

        # team搜索
        search_keywords = request.GET.get('keywords', '')
        if search_keywords:
            all_teams = all_teams.filter(Q(name__icontains=search_keywords)
                                        | Q(desc__icontains=search_keywords))

        location_id = request.GET.get('location', '')
        if location_id:
            all_teams = all_teams.filter(location_id=int(location_id))

        category = request.GET.get('category', '')
        if category:
            all_teams = all_teams.filter(category=category)

        sort = request.GET.get('sort', '')
        if sort:
            if sort == 'click_nums':
                all_teams = all_teams.order_by("-click_nums") # 如果前端传过来的 是“students”,那么就按照model：CourseOrg中的字段student_num倒序排列
            elif sort == 'engineer_num':
                all_teams = all_teams.order_by("-engineer_num")

        team_nums = all_teams.count()

        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1

        p = Paginator(all_teams, 2, request=request)

        teams = p.page(page)
        return render(request, 'org-list.html', {
            'all_teams': teams,
            'all_locations': all_locations,
            'location_id': location_id,
            'team_nums': team_nums,
            'category': category,
            'hot_teams': hot_teams,
            'sort': sort,

        })


class AddUserAskView(View):
    '''
    用户添加咨询
    '''
    def post(self, request):# 对表单form的请求是post
        userask_form = UserAskForm(request.POST) #定义的时候从model转成form  #这里初始化UserAskForm的时候 会主动调用forms.UserAskForm.clean_mobile方法进行mobile的验证
        if userask_form.is_valid(): # ModeForm比Form多了一个功能,就是model的属性，可以直接save Form,save之后就是一个model类，这与users里的ModifyPwdView手法不一样
            user_ask = userask_form.save(commit=True)    # 必须设置为True,否则并没有保存到数据库。ModelForm的save方法与Model的save 方法一样效果
            #断点调试可以发现user_ask是 UserAsk object.即ModelForm 保存后就是一个model类operation.models.UserAsk
            return HttpResponse('{"status":"success"}', content_type='application/json')

        else:
            return HttpResponse('{"status":"fail","msg":"添加出错"}', content_type='application/json')


class TeamHomeView(View):
    '''
    测试小组首页
    '''
    def get(self, request, team_id):#org_id url中配置的。  org-list.html中 <a href="{% url 'org:org_home' course_org.id %} ">
        current_page = 'home'
        team = Team.objects.get(id=int(team_id))# 通过org_id（url返回）找到course_org（CourseOrg类型）
        team.click_nums += 1
        team.save()
        has_fav = False
        if request.user.is_authenticated():# 与courses\views\CourseDetailView对比
            if UserFavorite.objects.filter(user=request.user, fav_id=team.id, fav_type=2):
                has_fav = True
        all_equipments = team.equipment_set.all()[:3] # 每个Course有一个外键course_org指向CourseOrg，现在是通过course_org去取这个机构下的所有Course
        all_engineers = team.engineer_set.all()[:2] # Teacher也有一个外键org 指向CourseOrg，现在是通过course_org去找出此机构下的所有老师
        return render(request, 'org-detail-homepage.html', {
            'all_equipments': all_equipments,
            'all_engineers': all_engineers,
            'team': team, # 这些变量传递到org-detail-homepage.html，因为继承自org_base.html,所以org_base.html中也可以用这些变量
            'current_page': current_page,
            'has_fav': has_fav,#传递到org-detail-homepage.html,它继承自org_base.html(这里用到了{% if has_fav %}已收藏{% else %}收藏{% endif %})
        })


class TeamEquipmentView(View):
    '''
    机构首页
    '''
    def get(self, request, team_id):#org_id url中配置的。  org-list.html中 <a href="{% url 'org:org_home' course_org.id %} ">
        current_page = 'equipment'
        team = Team.objects.get(id=int(team_id))# 通过org_id（url返回）找到course_org（CourseOrg）
        has_fav = False
        if request.user.is_authenticated():# 与courses\views\CourseDetailView对比
            if UserFavorite.objects.filter(user=request.user, fav_id=team.id, fav_type=2):
                has_fav = True
        all_equipments = team.equipment_set.all()# 每个Course有一个外键course_org指向CourseOrg，现在是通过这个course_org去取这个机构下的所有Course
        return render(request, 'org-detail-equipment.html', {
            'all_equipments': all_equipments,
            'team': team,# 这些变量传递到org-detail-course.html，因为继承自org_base.html,所以org_base.html中也可以用这些变量
            'current_page': current_page,
            'has_fav': has_fav,#传递到org-detail-course.html,它继承自org_base.html(这里用到了{% if has_fav %}已收藏{% else %}收藏{% endif %})
        })


class TeamDescView(View):
    '''
    team介绍页
    '''
    def get(self, request, team_id):
        current_page = 'desc'
        team= Team.objects.get(id=int(team_id))  # 通过org_id（url返回）找到course_org（CourseOrg）
        has_fav = False
        if request.user.is_authenticated():# 与courses\views\CourseDetailView对比
            if UserFavorite.objects.filter(user=request.user, fav_id=team.id, fav_type=2):
                has_fav = True
        return render(request, 'org-detail-desc.html', {
            'team': team,  # 这些变量传UserAskForm递到org-detail-desc.html，因为继承自org_base.html,所以org_base.html中也可以用这些变量
            'current_page': current_page,
            'has_fav': has_fav, #传递到org-detail-desc.html.html,它继承自org_base.html(这里用到了{% if has_fav %}已收藏{% else %}收藏{% endif %})
        })


class TeamEngineerView(View):
    '''
    Team工程师
    '''
    def get(self, request, team_id):
        current_page = 'engineer'
        team = Team.objects.get(id=int(team_id))# 通过org_id（url返回）找到course_org（CourseOrg）
        has_fav = False
        if request.user.is_authenticated():  # 与courses\views\CourseDetailView对比
            if UserFavorite.objects.filter(user=request.user, fav_id=team.id, fav_type=2):
                has_fav = True
        all_engineers = team.engineer_set.all() # Teacher也有一个外键org 指向CourseOrg，现在是通过course_org去找出此机构下的所有老师
        return render(request, 'org-detail-engineers.html', {
            'all_engineers': all_engineers,
            'team': team,  # 这些变量传递到org-detail-teachers.html，因为继承自org_base.html,所以org_base.html中也可以用这些变量
            'current_page': current_page,
            'has_fav': has_fav,    # 传递到org-detail-teachers.html,它继承自org_base.html(这里用到了{% if has_fav %}已收藏{% else %}收藏{% endif %})
        })


class AddFavView(View):
    '''
    用户收藏，用户取消收藏
    '''
    def post(self, request): # 为什么就是 post?因为是Ajax
        fav_id = request.POST.get('fav_id', 0)    # 前台ajax传过来的(org_base.html data:{'fav_id':fav_id, 'fav_type':fav_type}, add_fav($(this), {{ course_org.id }}, 2);)
        fav_type = request.POST.get('fav_type', 0)

        if not request.user.is_authenticated():# 无论是否有用户登录，request都有一个user(匿名的类或者UserProfile) 有一个这个is_authenticated()方法
            # 上一句判断用户登录状态，未登录则返回给ajax 会跳转到登录
            return HttpResponse('{"status":"fail","msg":"用户未登录"}', content_type='application/json')# "用户未登录"是在后台ajax中跳转到登录页面
        # 已经登录
        exist_records = UserFavorite.objects.filter(user=request.user, fav_id=int(fav_id), fav_type=int(fav_type))
        if exist_records: # 这里其实只可能返回一条记录，所以下面可以 用delete。 那么既然只有一条，那么可以用get吗？
            #如果记录已经存在则表示用户取消收藏
            exist_records.delete()
            if int(fav_type) == 1:   # 设备
                equipment = Equipment.objects.get(id=int(fav_id))
                equipment.fav_nums -= 1
                if equipment.fav_nums < 0:
                    equipment.fav_nums = 0
                equipment.save()
            elif int(fav_type) == 2:
                team = Team.objects.get(id=int(fav_id))
                team.fav_nums -= 1
                if team.fav_nums < 0:
                    team.fav_nums = 0
                team.save()
            elif int(fav_type) == 3:
                engineer = Engineer.objects.get(id=int(fav_id))
                engineer.fav_nums -= 1
                if engineer.fav_nums < 0:
                    engineer.fav_nums = 0
                engineer.save()

            return HttpResponse('{"status":"success","msg":"收藏"}', content_type='application/json')
        else:
            user_fav = UserFavorite()
            if int(fav_id) > 0 and int(fav_type) > 0:
                user_fav.user = request.user
                user_fav.fav_id = int(fav_id)
                user_fav.fav_type = int(fav_type)
                user_fav.save()

                if int(fav_type) == 1:  # 设备
                    equipment = Equipment.objects.get(id=int(fav_id))
                    equipment.fav_nums += 1
                    equipment.save()
                elif int(fav_type) == 2:
                    team = Team.objects.get(id=int(fav_id))
                    team.fav_nums += 1
                    team.save()
                elif int(fav_type) == 3:
                    engineer = Engineer.objects.get(id=int(fav_id))
                    engineer.fav_nums += 1
                    engineer.save()

                return HttpResponse('{"status":"success","msg":"已收藏"}', content_type='application/json')
            else:
                return HttpResponse('{"status":"fail","msg":"收藏出错"}', content_type='application/json')


class EngineerListView(View):
    '''
    工程师列表页
    '''
    def get(self, request):
        # current_page = 'teachers-list'
        all_engineers = Engineer.objects.all()
        # 工程师搜索
        search_keywords = request.GET.get('keywords', '')
        if search_keywords:
            all_engineers = all_engineers.filter(Q(name__icontains=search_keywords)
                                               | Q(team__name__icontains=search_keywords)
                                               | Q(work_position__icontains=search_keywords))

        # 根据Engineer中的字段 click_nums 对工程师排序
        sort = request.GET.get('sort', '')  # sort是由前端页面传过来的空或者hot
        if sort:
            if sort == 'hot':
                all_engineers = all_engineers.order_by("-click_nums")  # 如果前端传过来的 是“hot”,那么就按照organization\model：Teacher中的字段click_nums倒序排列

        # 工程师排序
        sorted_engineers = Engineer.objects.all().order_by('-click_nums')[:3]

        engineer_nums = all_engineers.count()

        # 对工程师进行分页
        try:  # request.GET  <QueryDict: {'page': ['2']}>
            page = request.GET.get('page', 1)  # 取页数编号 返回的是 1,2 这样的int页数
        except PageNotAnInteger:
            page = 1

        p = Paginator(all_engineers, 2, request=request)  # p是Paginator对象类型，all_orgs是QuerySet

        engineers = p.page(page)  # teachers是Page类型： <Page 1 of 4>,它的object_list：<QuerySet [<Course: delphi>, <Course: 操作系统>, <Course: 数据结构>]>

        return render(request, 'engineers-list.html', {
            # 'current_page': current_page,
            'all_engineers': engineers,
            'sorted_engineers': sorted_engineers,
            'sort': sort,
            'engineer_nums': engineer_nums,
        })


class EngineerDetailView(View):
    def get(self, request, engineer_id):   #要与 url中的名字一样 否则无法映射过来
        engineer = Engineer.objects.get(id=int(engineer_id))  # Model中的Engineer类

        # 增加engineer点击数
        engineer.click_nums += 1
        engineer.save()

        all_res_equipments = Equipment.objects.filter(responsible_person=engineer)

        has_engineer_faved = False
        if request.user.is_authenticated():  # 与courses\views\CourseDetailView对比
            if UserFavorite.objects.filter(user=request.user, fav_id=engineer.id, fav_type=3):
                has_engineer_faved = True

        has_team_faved = False
        if request.user.is_authenticated():  # 与courses\views\CourseDetailView对比
            if UserFavorite.objects.filter(user=request.user, fav_id=engineer.team.id, fav_type=2):
                has_team_faved = True

        # 工程师排序
        sorted_engineers = Engineer.objects.all().order_by('-click_nums')[:3]

        return render(request, 'engineer-detail.html', {
            'engineer': engineer,
            'all_res_equipments': all_res_equipments,
            'sorted_engineers': sorted_engineers,
            'has_engineer_faved': has_engineer_faved,
            'has_team_faved': has_team_faved,

        })





