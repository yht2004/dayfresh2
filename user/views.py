from django.shortcuts import render,redirect,reverse
from django.views.generic import View
from django.conf import settings
from django.http.response import HttpResponse
from django.contrib.auth import authenticate,login,logout

import re
from user.models import User
from celery_tasks.tasks import send_register_active_email
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired

from django.contrib.auth.mixins import LoginRequiredMixin


# def index(request):
#     return render(request,'index.html')

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

        #发送邮件
        send_register_active_email.delay(email,username,token)

        # 返回应答
        return redirect(reverse('index'))#使用反向解析url

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
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request,'login.html',{'username':username,'checked':checked})
        #return render(request, 'login.html')

    def post(self,request):
        '''登陆校验'''
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        #数据校验
        user = authenticate(username=username, password=password)
        if not all([username,password]):
            return render(request,'login.html',{'errmsg':'数据不完整'})
        #验证用户
        if user is not None:
            if user.is_active:
                login(request,user)#保存sessionid
                #如果用户未登陆访问资源时，直接跳转到登陆页面
                next_url = request.GET.get('next',reverse('index'))
                response = redirect(next_url)
                #response = redirect(reverse('index'))
                #如果记住用户名，下次登陆时直接显示用户名，否则不显示
                remember = request.POST.get('remember')
                if remember == 'on':
                    response.set_cookie('username',username,max_age=3*24*36000)
                else:
                    response.delete_cookie('username')
                return response
                #return render(request,'index.html')
            else:
                return render(request,'login.html',{'errmsg':'账号未激活'})
        else:
            return render(request,'login.html',{'errmsg':'用户名或密码错误'})


class LogoutView(View):
    def logout_view(request):
        logout(request)
        return redirect(reverse('index'))

class UserInfo(LoginRequiredMixin,View):
    '''用户中心页面'''
    def get(self,request):
        return render(request,'user_center_info.html',{'page':'user'})

class UserOrder(LoginRequiredMixin,View):
    '''用户订单页面'''
    def get(self,request):
        return render(request,'user_center_order.html',{'page':'order'})


class UserAddress(LoginRequiredMixin,View):
    '''用户地址页面'''
    def get(self,request):
        return render(request,'user_center_site.html',{'page':'address'})











