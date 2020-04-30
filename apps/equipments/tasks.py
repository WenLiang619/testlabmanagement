# _*_ coding: utf-8 _*_
__author__ = 'wenliang'
__date__ = '2019/5/4 10:45'

from django.core.mail import send_mail
from datetime import datetime

from TestLabManagement.settings import EMAIL_FROM
from operation.models import UserEquipment, UserEquipmentInadvance

from background_task import background
from users.models import UserProfile

has_sentmail_userequipmentinadvance_to_using = False


@background()
def notify_user():
    # 对于不可提前预定的设备 查询是否有逾期未归还的设备，是则邮件催还
    all_overdue_user_equipments = UserEquipment.objects.filter(return_time=None,
                                                     plan_to_return_time__lte=datetime.now())#日期小在前，大在后
    if all_overdue_user_equipments:
        for overdue_user_equipment in all_overdue_user_equipments:
            email_title = 'Test&Lab借用设备超期提醒！'
            user_name = overdue_user_equipment.user.username
            borrow_time = overdue_user_equipment.borrow_time
            item = overdue_user_equipment.equipment.item
            equipment = overdue_user_equipment.equipment.name
            plan_to_return_time = overdue_user_equipment.plan_to_return_time
            resp_person = overdue_user_equipment.equipment.responsible_person
            user_email = overdue_user_equipment.user.email
            email_body = '尊敬的{0}：\n\n您在{1}借用的设备{2}/{3} 已经超过了预计的归还时间{4}。\n请将设备归还给设备责任人{5}或者办理续' \
                         '借手续。\n\n\n\n\n-----------------------------------------------------------------------------------\n以上信息来自 ' \
                         'Test&Lab管理后台 自动发送内容，请勿回复此邮件！'\
                        .format(user_name, borrow_time, item, equipment, plan_to_return_time, resp_person)
            send_status = send_mail(email_title, email_body, EMAIL_FROM, [user_email])

            email_title = 'Test&Lab借用设备超期提醒！'
            email_body = '实验室设备管理人员：你好。\n\n现有用户{1}在{2}借用的设备{2}/{3} 已经超过了预计的归还时间{4}。\n请督促使用人将设备归还给实验室或者办理续' \
                         '借手续。\n\n\n\n\n-----------------------------------------------------------------------------------\n以上信息来自 ' \
                         'Test&Lab管理后台 自动发送内容，请勿回复此邮件！'.format(user_name, borrow_time, item, equipment, plan_to_return_time)
            lab_equ_respons_email = overdue_user_equipment.equipment.responsible_person.email
            send_status2 = send_mail(email_title, email_body, EMAIL_FROM, [lab_equ_respons_email])

            if send_status2:
                print('设备借用超期，请及时归还！不可提前预定')
    else:
        print('ok ,无逾期未归还设备！不可提前预定')
    #对于 可提前预定的设备 查询是否有逾期未归还的设备，是则邮件催还
    all_overdue_user_equipmentsinadvance = UserEquipmentInadvance.objects.filter(return_time=None,
                                                     plan_to_return_time__lte=datetime.now())#日期小在前，大在后
    if all_overdue_user_equipmentsinadvance:
        for overdue_user_equipmentinadvance in all_overdue_user_equipmentsinadvance:
            email_title = 'Test&Lab借用设备超期提醒！'
            user_name = overdue_user_equipmentinadvance.user.username
            borrow_time = overdue_user_equipmentinadvance.borrow_time
            item = overdue_user_equipmentinadvance.equipment.item
            equipment = overdue_user_equipmentinadvance.equipment.name
            plan_to_return_time = overdue_user_equipmentinadvance.plan_to_return_time
            resp_person = overdue_user_equipmentinadvance.equipment.responsible_person
            user_email = overdue_user_equipmentinadvance.user.email
            email_body = '尊敬的{0}：\n\n您在{1}借用的设备{2}/{3} 已经超过了预计的归还时间{4}。\n请将设备归还给设备责任人{5}或者办理续' \
                         '借手续。\n\n\n\n\n-----------------------------------------------------------------------------------\n以上信息来自 ' \
                         'Test&Lab管理后台 自动发送内容，请勿回复此邮件！' \
                .format(user_name, borrow_time, item, equipment, plan_to_return_time, resp_person)
            send_status = send_mail(email_title, email_body, EMAIL_FROM, [user_email])

            email_title = 'Test&Lab借用设备超期提醒！'
            email_body = '实验室设备管理人员：你好。\n\n现有用户{0}在{1}借用的设备{2}/{3} 已经超过了预计的归还时间{4}。\n请督促使用人将设备归还给实验室或者办理续' \
                         '借手续。\n\n\n\n\n-----------------------------------------------------------------------------------\n以上信息来自 ' \
                         'Test&Lab管理后台 自动发送内容，请勿回复此邮件！'.format(user_name, borrow_time, item, equipment,
                                                               plan_to_return_time)
            lab_equ_respons_email = overdue_user_equipmentinadvance.equipment.responsible_person.email
            # lab_equ_respons_email = '419099632@qq.com' #调试用
            send_status2 = send_mail(email_title, email_body, EMAIL_FROM, [lab_equ_respons_email])

            if send_status2:
                print('设备借用超期，请及时归还！可提前预定')
    else:
        print('ok ,无逾期未归还设备！可提前预定')

    # 对于可提前预定的设备，查询是否有预定的设备进入借用（使用）状态，是则发送邮件通知预定人和设备责任人
    # 找出return_time是空并且borrow_time字段是最近的那个，只要这条记录没有进入借用状态那么后面的必定没有进入借用状态
    userquipmentinadvance_latest = UserEquipmentInadvance.objects.filter(return_time=None).order_by('borrow_time')
    global has_sentmail_userequipmentinadvance_to_using #局部变量全局化
    print('---', has_sentmail_userequipmentinadvance_to_using)
    if userquipmentinadvance_latest:
        if userquipmentinadvance_latest[0].borrow_time <= datetime.now() and (not has_sentmail_userequipmentinadvance_to_using):
            email_title = 'Test&Lab设备借用成功通知！'
            email_body = '亲爱的用户{0}:\n恭喜您借用到了下面的设备:{1},{2}\n计划归还日期是：{3}\n请联系设备责任人{4}取用\n\n\n\n\n------------------------------------------------------------\n以上信息来自 Test&Lab管理后台 自动发送内容，请勿回复此邮件！' \
            .format(userquipmentinadvance_latest[0].user.username,
                    userquipmentinadvance_latest[0].equipment.item,
                    userquipmentinadvance_latest[0].equipment.name,
                    userquipmentinadvance_latest[0].plan_to_return_time,
                    userquipmentinadvance_latest[0].equipment.responsible_person)
            send_status = send_mail(email_title, email_body, EMAIL_FROM,
                                [userquipmentinadvance_latest[0].user.email])
            email_body = '亲爱的设备责任人{0}:\n\n现有一个设备:{1},{2} 从预定转入借用状态。\n计划归还日期是：{3}\n请将设备转交给借用人{4}\n\n\n\n\n------------------------------------------------------------\n以上信息来自 Test&Lab管理后台 自动发送内容，请勿回复此邮件！' \
            .format(userquipmentinadvance_latest[0].equipment.responsible_person,
                    userquipmentinadvance_latest[0].equipment.item,
                    userquipmentinadvance_latest[0].equipment.name,
                    userquipmentinadvance_latest[0].plan_to_return_time,
                    userquipmentinadvance_latest[0].user.username)
            send_status2 = send_mail(email_title, email_body, EMAIL_FROM,
                                [userquipmentinadvance_latest[0].equipment.responsible_person.email])
            if send_status2:
                print('设备从预定进入借用状态。')

            has_sentmail_userequipmentinadvance_to_using = True # 在设备归还里改成了False 允许下一个进入借用状态的预定条目在这里发送邮件 line366
            print('+++', has_sentmail_userequipmentinadvance_to_using)
        else:  # 最近的那条记录没有进入借用状态那么后面的必定没有进入借用状态
            print('ok ,无设备从预定进入借用状态!')
    else:
        print('当前没有设备预定记录。 ')



