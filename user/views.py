from django.shortcuts import render,redirect,reverse
from django.views.generic import View
from django.conf import settings
from django.http.response import HttpResponse
from django.contrib.auth import authenticate,login,logout
from django.core.paginator import Paginator

import re
from user.models import User,Address
from order.models import OrderInfo,OrderGoods
from good.models import GoodsSKU
from celery_tasks.tasks import send_register_active_email
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired

from django.contrib.auth.mixins import LoginRequiredMixin
from django_redis import get_redis_connection



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
        return redirect(reverse('login'))

class UserInfo(LoginRequiredMixin,View):
    '''用户中心页面'''
    def get(self,request):
        user = request.user
        address = Address.objects.get_default_address(user)

        #获取用户历史浏览记录
        con = get_redis_connection('default')#使用redis存储用户浏览过的商品
        history_key = 'history_%d'%user.id

        #获取用最近浏览的5个商品的id
        sku_ids = con.lrange(history_key,0,4)

        #遍历获取用户浏览的商品信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        context = {'page':'user',
                   'address':address,
                   'goods_li':goods_li}

        return render(request,'user_center_info.html',context)

class UserOrder(LoginRequiredMixin,View):
    '''用户订单页面'''
    def get(self,request,page):
        #获取用户订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')
        #遍历订单的商品信息
        for order in orders:
            #根据order_id查询商品
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)
            #计算商品小计
            for order_sku in order_skus:
                amount = order_sku.count*order_sku.price
                order_sku.amount = amount  #动态添加属性

            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]#动态增加属性，保存订单状态
            order.order_skus = order_skus #动态增加属性，保存订单商品信息

        #分页
        paginator = Paginator(orders, 5)
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

            # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # 进行页码的控制，页面上最多显示5个页码
        # 1.总页数小于5页，页面上显示所有页码
        # 2.如果当前页是前3页，显示1-5页
        # 3.如果当前页是后3页，显示后5页
        # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        context = {'order_page':order_page,
                   'pages':pages,
                   'page':'order',
                   }

        return render(request,'user_center_order.html',context)


class UserAddress(LoginRequiredMixin,View):
    '''用户地址页面'''
    def get(self,request):
        user = request.user

        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None
        address = Address.objects.get_default_address(user)
        return render(request,'user_center_site.html',{'page':'address','address':address})

    def post(self,request):
        '''添加地址'''
        #1.接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        phone =  request.POST.get('phone')
        zip_code = request.POST.get('zip_code')

        #2.数据校验
        if not all([receiver,addr,phone]):
            return render(request,'user_center_site.html',{'errmsg':'数据不完整'})

        if not re.match(r'1[35678]\d{9}',phone):#正则表达式匹配手机号码
            return render(request,'user_center_site.html',{'errmsg':'手机号码不正确'})
        #3.业务处理
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None
        address = Address.objects.get_default_address(user)
        if address:
            is_default = False
        else:
            is_default = True

        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        #4.返回应答
        return redirect(reverse('address'))









