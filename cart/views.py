from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from good.models import GoodsSKU

from django_redis import get_redis_connection

class CartAddView(View):
    '''添加购物车'''
    def post(self,request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res':0,'errmsg':'请先登录'})

        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        #校验数据完整性
        if not all([sku_id,count]):
            return JsonResponse({'res':0,'errmsg':'数据不完整'})
        #校验添加商品的数量
        try:
            count = int(count)
        except Exception as e :
            return JsonResponse({'res':1,"errmsg":'商品数目出错'})
        #校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res':2,'errmsg':'商品不存在'})

        #业务处理
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id

        #尝试获取sku_id的值——>hget cart_key
        #弱国sku_id在hash中不存在，hget返回one
        cart_count = conn.hget(cart_key,sku_id)
        if cart_count:
            #累加购物车中商品数目
            count += int(cart_count)
        #校验商品的库存
        if count > sku.stock:
            return JsonResponse({'res':4,'errmsg':'商品库存不足'})

        #设置hash中sku_id对应的值
        #hset->如果sku_id已经存在，更新数据，如果sku_id不存在，添加数据
        conn.hset(cart_key,sku_id,count)

        #计算用户购物车商品的条目数
        total_count = conn.hlen(cart_key)

        #返回应答
        return JsonResponse({'res':5,'total_count':total_count,'message':'添加成功'})






















