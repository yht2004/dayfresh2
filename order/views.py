from django.shortcuts import render, redirect,reverse
from django.http import JsonResponse
from django.views.generic import View
from django.db import transaction
from django.conf import settings

from user.models import Address
from good.models import GoodsSKU
from order.models import OrderInfo, OrderGoods

from django_redis import get_redis_connection
from datetime import datetime

from alipay import AliPay
import os

class OrderPlaceView(View):
    '''提交订单页面显示'''
    def post(self,request):
        user = request.user
        #获取参数sku_ids
        sku_ids = request.POST.getlist('sku_ids')
        #校验参数
        if not sku_ids:
            #跳转到购物车页面
            return redirect(reverse('show'))

        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id

        skus = []
        #保存商品的总件数和总价格
        total_count = 0
        total_price = 0
        #遍历sku_ids获取用户要购买的商品信息
        for sku_id in sku_ids:
            #根据商品的id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 获取用户所要购买的商品的数量
            count = conn.hget(cart_key, sku_id)
            # 计算商品的小计
            amount = sku.price * int(count)
            # 动态给sku增加属性count,保存购买商品的数量
            sku.count = int(count)
            # 动态给sku增加属性amount,保存购买商品的小计
            sku.amount = amount
            # 追加
            skus.append(sku)
            # 累加计算商品的总件数和总价格
            total_count += int(count)
            total_price += amount

            # 运费:实际开发的时候，属于一个子系统
        transit_price = 10  # 写死

        # 实付款
        total_pay = total_price + transit_price

        # 获取用户的收件地址
        addrs = Address.objects.filter(user=user)

        # 组织上下文
        sku_ids = ','.join(sku_ids)  # [1,25]->1,25
        context = {'skus': skus,
                   'total_count': total_count,
                   'total_price': total_price,
                   'transit_price': transit_price,
                   'total_pay': total_pay,
                   'addrs': addrs,
                   'sku_ids': sku_ids}

        # 使用模板
        return render(request, 'place_order.html', context)

class OrderCommitView(View):
    '''订单创建'''

    @transaction.atomic
    def post(self, request):
        '''订单创建'''
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')  # 1,3

        # 校验参数
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})

        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法的支付方式'})

        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            # 地址不存在
            return JsonResponse({'res': 3, 'errmsg': '地址非法'})

        # todo: 创建订单核心业务

        # 组织参数
        # 订单id: 20171122181630+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # 运费
        transit_price = 10

        # 总数目和总金额
        total_count = 0
        total_price = 0

        # 设置事务保存点
        save_id = transaction.savepoint()
        try:
            # todo: 向df_order_info表中添加一条记录
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transit_price)

            # todo: 用户的订单中有几个商品，需要向df_order_goods表中加入几条记录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                # 获取商品的信息
                try:
                    # select * from df_goods_sku where id=sku_id for update;
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                except:
                    # 商品不存在
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                print('user:%d stock:%d' % (user.id, sku.stock))
                import time
                time.sleep(10)

                # 从redis中获取用户所要购买的商品的数量
                count = conn.hget(cart_key, sku_id)

                # todo: 判断商品的库存
                if int(count) > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                # todo: 向df_order_goods表中添加一条记录
                OrderGoods.objects.create(order=order,
                                          sku=sku,
                                          count=count,
                                          price=sku.price)

                # todo: 更新商品的库存和销量
                sku.stock -= int(count)
                sku.sales += int(count)
                sku.save()

                # todo: 累加计算订单商品的总数量和总价格
                amount = sku.price * int(count)
                total_count += int(count)
                total_price += amount

            # todo: 更新订单信息表中的商品的总数量和总价格
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 7, 'errmsg': '下单失败'})

        # 提交事务
        transaction.savepoint_commit(save_id)

        # todo: 清除用户购物车中对应的记录
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '创建成功'})

class OrderPayView(View):
    '''订单支付'''
    def post(self,request):
        '''订单支付'''
        #判断用户是否登陆
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res':0,'errmsg':'用户未登陆'})

        #接收数据
        order_id = request.POST.get('order_id')
        #检验数据
        if not order_id:
            return JsonResponse({'res':1,'errmsg':'订单不存在'})

        try:
            order = OrderInfo.objects.get(
                                        order_id=order_id,
                                        user=user,
                                        pay_method=3,
                                        order_status=1
                                        )
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res':2,'errmsg':'订单错误'})

        #业务处理
        #调用支付宝接口
        #1.初始化
        alipay = AliPay(
            appid="2016092900625617",
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR,'order/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=os.path.join(settings.BASE_DIR,'order/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug = True  # 默认False
        )
        #2.调用支付接口
        # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        total_pay = order.total_price + order.transit_price
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(total_pay),
            subject='天天生鲜%s'%order_id,
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )

        #返回应答
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res':3,'pay_url':pay_url})

class CheckPayView(View):
    '''订单状态查询'''
    def post(self,request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res':0,'errmsg':'用户未登录'})

        #接收数据
        order_id = request.POST.get('order_id')
        #验证数据
        if not order_id:
            return  JsonResponse({'res':1,'errmsg':'订单不存在'})

        try:
            order = OrderInfo.objects.get(order_id=order_id,user=user,pay_method=3,order_status=1)
        except OrderInfo.DoesNotExist:
            JsonResponse({'res':2,'message':'订单错误'})

        #业务处理
        #1.初始化
        alipay = AliPay(
            appid="2016092900625617",
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, 'order/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'order/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )

        #2.调用查询接口
        while True:
            response = alipay.api_alipay_trade_query(order_id)
            code = response.get('code')

            if code == '10000' and response.get('trade_status') == 'TRADE_SUCCESS':
                #支付成功,获取支付宝交易号
                trade_no = response.get('trade_no')
                #更新订单状态
                order.trade_no = trade_no
                order.order_status = 4 #待评价
                order.save()
                return JsonResponse({'res':3,'errmsg':'支付成功'})
            elif code == '40004' or (code == '10000' and response.get('trade_status') == 'WAIT_BUYER_PAY'):
                #等待买家付款，业务处理失败，可能一会就会成功
                import time
                time.sleep(5)
                continue
            else:
                #支付出错
                print(code)
                return JsonResponse({'res':4,'errmsg':'支付失败'})

class CommentView(View):
    '''订单评论'''
    def get(self,request,order_id):
        '''提供评论页面'''
        user = request.user
        #校验数据
        if not order_id:
            return redirect(reverse('order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id,user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse('order'))

        #根据订单状态回去订单状态的标题
        order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

        #获取订单商品信息
        order_skus = OrderGoods.objects.filter(order_id=order_id)
        for order_sku in order_skus:
            #计算商品小计
            amount = order_sku.count*order_sku.price
            #动态给order_sku增加属性amount，保存商品小计
            order_sku.amount = amount
        #动态给order增加order_skus属性，保存订单商品信息
        order.order_skus = order_skus

        return render(request,'order_comment.html',{'order':order})

    def post(self,request,order_id):
        '''处理评论内容'''
        user = request.user
        #校验数据
        if not order_id:
            return redirect(reverse('order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id,user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse('order'))

        #获取评论条数
        total_count = request.POST.get('total_count')
        total_count = int(total_count)

        #循环获取订单中商品的品论内容
        for i in range(1,total_count+1):
            #获取评论的商品id
            sku_id = request.POST.get('sku_%d'%i)
            #获取评论的商品内容
            content = request.POST.get('content_%d'%i)
            try:
                order_goods = OrderGoods.objects.get(order=order,sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue

            order_goods.comment = content
            order_goods.save()

        order.order_status = 5
        order.save()
        
        return redirect(reverse('order',kwargs={'page':1}))























