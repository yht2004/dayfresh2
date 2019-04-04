from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
import time

import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dayfresh2.settings")
django.setup()
#创建一个Celery实例对象
app = Celery('celery_tasks.tasks',broker='redis://localhost:6379/8')


#定义任务函数
@app.task
def send_register_active_email(to_email,username,token):
    '''发送激活邮件'''
    #组织邮件信息
    subject = '天天生鲜欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<h1>%s欢迎成为天天生鲜会员</h1><p>请点击激活链接激活用户</br><a href="http://127.0.0.1:8000/user/active/%s">' \
                   'http://127.0.0.1:8000/user/active/%s</a></p>'%(username,token,token)
    send_mail(subject,message,sender,receiver,html_message=html_message)
    #time.sleep(5)

    #manual  remove regular file `python'?
