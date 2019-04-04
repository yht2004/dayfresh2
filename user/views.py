from django.shortcuts import render,redirect
from django.views.generic import View
from django.conf import settings
from django.http.response import HttpResponse
from django.core.mail import send_mail
import re
from user.models import User
from celery_tasks.tasks import send_register_active_email
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired


def index(request):
    return render(request,'index.html')

class RegisterView(View):
    '''注册'''
    def get(self,request):
        return  render(request,'register.html')

    def post(self,request):
        '''注册处理'''
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        cpassword = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 校验数据
        if not all([username, password, email]):
            # 验证数据完整性
            return render(request, 'register.html', {'errorMessage': '数据不完整'})

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {'errorMessage': '用户名已存在'})

        # 校验邮箱 ^[A-Za-z\d]+([-_.][A-Za-z\d]+)*@([A-Za-z\d]+[-.])+[A-Za-z\d]{2,4}$
        if not re.match(r'^[A-Za-z\d]+([-_.][A-Za-z\d]+)*@([A-Za-z\d]+[-.])+[A-Za-z\d]{2,4}$', email):
            return render(request, 'register.html', {'errorMessage': '邮箱格式不正确'})

        if allow != 'on':
            return render(request, 'register.html', {'errorMessage': '请同意协议'})

        # 业务处理
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        #发送激活邮件，包含激活链接：http://127.0.0.1:8080/user/active/3
        #激活链接中包含用户的身份信息，并且把身份信息进行加密

        #加密用户信息，生成激活token
        serializer = Serializer(settings.SECRET_KEY,3600)
        info = {'confirm':user.id}
        token = serializer.dumps(info)
        token = token.decode()
        print('------------------========')
        #发送邮件
        send_register_active_email.delay(email,username,token)
        print('-------------------------')
        # subject = '天天生鲜欢迎信息'
        # message = ''
        # sender = settings.EMAIL_FROM
        # receiver = [email]
        # html_message = '<h1>%s欢迎成为天天生鲜会员</h1><p>请点击激活链接激活用户</br><a href="http://127.0.0.1:8000/user/active/%s">' \
        #                'http://127.0.0.1:8000/user/active/%s</a></p>' % (username, token, token)
        # send_mail(subject,message,sender,receiver,html_message=html_message)
        # 返回应答
        return redirect('index')

class ActiveView(View):
    '''用户激活'''
    def get(self, request,token):
        '''解密用户激活'''
        #进行解密，获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY,3600)
        try:
            info = serializer.loads(token)
            #获取待激活用户的id
            user_id = info['confirm']
            #根据id获取用户信息
            user = User.objects.get(id = user_id)
            user.is_active = 1
            user.save()
            #跳转到登录页面
            return redirect('login')
        except SignatureExpired as e:
            #激活链接已过期
            return HttpResponse('激活链接已过期')


class LoginView(View):
    '''登录'''
    def get(self,request):
        return render(request,'login.html')



#You are using pip version 7.1.2, however version 19.0.3 is available.
#You should consider upgrading via the 'pip install --upgrade pip' command.


