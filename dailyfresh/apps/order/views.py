from django.shortcuts import render,redirect
from django.views.generic import View
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection
from apps.goods.models import *
from apps.user.models import *
from apps.order.models import *
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from datetime import datetime
from django.db import transaction

# Create your views here.


class PlaceView(LoginRequiredMixin,View):

    def post(self,request):

        # 获取数据
        sku_list = request.POST.getlist("sku_id")
        user = request.user
        if not sku_list:
            return redirect(reverse("cart:info"))
        # 商品总数,商品总价,商品列表
        sku_count = 0
        price_count = 0
        skus = []
        # 连接redis
        conn = get_redis_connection("default")
        cart_key = "cart_%d"%user.id
        # 便宜商品id
        for sku_id in sku_list:
            # 获取商品对象和此商品在数据库中的对象
            sku = GoodsSKU.objects.get(id=sku_id)
            s_count = int(conn.hget(cart_key,sku_id))
            s_price = sku.price*s_count
            # 总价、总数量、商品列表
            price_count += s_price
            sku_count += s_count
            skus.append(sku)
            # 动态添加属性
            sku.s_count = s_count
            sku.s_price = s_price

        address = Address.objects.filter(user=user)
        total = price_count + 10
        sku_ids = ",".join(sku_list)
        context = {"price_count":price_count,"sku_count":sku_count,
                   "skus":skus,"total":total,"sku_ids":sku_ids,
                   "address":address
                    }

        return render(request,"place_order.html",context)


class CommitView(View):

    # 事务装饰函数
    @transaction.atomic
    def post(self,request):

        # 验证登陆
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({"res":0,"error":"用户未登陆"})

        # 接受数据
        addr_id = request.POST.get("addr_id")
        pay_method = request.POST.get("pay_method")
        sku_ids = request.POST.get("sku_ids")

        # 数据校验
        if not all([addr_id,pay_method,sku_ids]):
            return JsonResponse({"res": 1, "error": "数据不完整"})
        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法的支付方式'})
        # 验证地址是否正确
        try:
            addr = Address.objects.get(id=addr_id)
        except:
            return JsonResponse({"res":3,"error":"地址错误"})

        # 组织参数
        # 订单id: 20171122181630+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)
        # 运费
        transit_price = 10
        # 总数目和总金额
        total_count = 0
        total_price = 0

        #　创建事务保存点
        sid = transaction.savepoint()
        # 如果出错,回滚到保存点
        try:
            # 创建用户订单表
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transit_price)
            # 获取链接
            conn = get_redis_connection("default")
            cart_key = "cart_%d"%user.id
            # 循环创建订单商品详情表
            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                try:
                    # sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                    sku = GoodsSKU.objects.get(id=sku_id)

                except:
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({"res":4,"error":"商品不存在"})
                # 获取此商品数量
                count = conn.hget(cart_key,sku_id)

                # 更新库存和销量
                new_stock = sku.stock - int(count)
                new_sales = sku.sales + int(count)
                # 乐观锁判断库存是否充足
                rel_num = GoodsSKU.objects.filter(id=sku_id,stock__gte=count).update(stock=new_stock,sales=new_sales)
                print(rel_num)
                if not rel_num:
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({"res": 6, "error": "库存不足"})
                # 创建一个订单商品详情表
                order_info = OrderGoods.objects.create(order=order,
                                                       sku=sku,
                                                       count=count,
                                                       price=sku.price)
                # 累加总商品数和总价
                total_count += int(count)
                total_price += int(count)*sku.price

            # 更新总价和数量
            order.total_price = total_price
            order.total_count = total_count
            order.save()

        except Exception as ret:
            transaction.savepoint_rollback(sid)
            return JsonResponse({"res":8,"error":"下单失败"})

        # 提交事务
        transaction.savepoint_commit(sid)
        # 删除购物车中购买的商品
        conn.hdel(cart_key, *sku_ids)

        # 返回成功结果
        return JsonResponse({"res":5,"ok":"添加成功"})















































