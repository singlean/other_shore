from django.shortcuts import render,redirect        # 模板函数,重定向
from apps.user.models import User,Address       # 用户信息表
from apps.goods.models import GoodsSKU
from apps.order.models import OrderGoods,OrderInfo
from django.views.generic import View       # 类视图
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer      # 签名邮件用户信息
from celery_tasks.tasks import send_register_active_email       # celery异步邮件处理
from dailyfresh import settings         # 项目配置
from django.core.urlresolvers import reverse        # 反向解析
import re       # 正则
from django.http import HttpResponse        # 返回结果对象
from django.contrib.auth import authenticate,login,logout        # 认证函数,记录登陆状态函数
from utils.mixin import LoginRequiredMixin      # 用户登陆验证,未登录无法进入
from django_redis import get_redis_connection       # 快捷创建链接redis对象的方法
from django.core.paginator import Paginator

# Create your views here.


# 注册
class RegisterView(View):
    """注册类"""

    def get(self,request):

        return render(request,"register.html")

    def post(self,request):
        # 接收数据
        username = request.POST.get("user_name")
        password = request.POST.get("pwd")
        cpwd = request.POST.get("cpwd")
        email = request.POST.get("email")
        allow = request.POST.get("allow")

        # 对数据进行校验
        # 检查是否勾选协议
        if allow == None:
            return render(request, 'register.html', {"error": "请勾选协议"})
        # 验证是否有内容为空
        if not all([username,password,cpwd,email]):
            return render(request,'register.html',{"error":"有内容为空,请填写完整"})
        # 验证邮箱
        ret = re.match(r"^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$",email)
        if not ret:
            return render(request, 'register.html', {"error": "邮箱格式错误"})
        # 验证密码
        if cpwd !=password:
            return render(request, 'register.html', {"error": "两次密码不一致"})
        # 验证用户名是否重复
        # filter没有查到数据会返回一个空的查询集,python的[]
        user = User.objects.filter(username=username)
        if user:
            return render(request, 'register.html', {"error": "用户名已注册"})

        # 处理数据
        # 调用django自带的创建用户函数,然后将激活状态修改
        user = User.objects.create_user(username,email,password)
        user.is_active = 0
        user.save()

        # 创建编码对象,对信息编码生成token
        serializer = Serializer(settings.SECRET_KEY,3600)
        token = serializer.dumps({"confirm":user.id})
        token = token.decode()

        # 发送邮件
        # obj = "天天生鲜"
        # massage = ""
        # html_mess = '<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br/><a href="http://192.168.110.133:8001/user/active/%s">http://192.168.100.133:8001/user/active/%s</a>' % (username, token, token)
        # # 邮件标题,正文内容,发件人,收件人列表,html内容
        # send_mail(obj,massage,settings.EMAIL_FROM,[email],html_message=html_mess)

        # celery异步发送邮件
        send_register_active_email.delay(username,email,token)

        # 返回结果
        return redirect(reverse("user:login"))


# 激活
class ActiveView(View):
    """用户激活"""

    def get(self,request,token):
        """激活用户"""
        # 创建解码对象
        serializer = Serializer(settings.SECRET_KEY,3600)
        try:
            # 解码错误会报错
            info = serializer.loads(token)
            # 获取此用户并激活
            user_id = info["confirm"]
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            return redirect(reverse("user:login"))
        except:
            return HttpResponse("激活链接已过期")


# 登陆
class LoginView(View):
    """登陆类"""

    def get(self,request):

        if "username" in request.COOKIES:
            username = request.COOKIES["username"]
            checked = "checked"
        else:
            username = ""
            checked = ""

        return render(request,"login.html",{"username":username,"checked":checked})


    def post(self,request):

        # 接受数据
        username = request.POST.get("username")
        password = request.POST.get("pwd")
        affirm = request.POST.get("affirm")

        # 校验数据
        if not all([username,password]):
            return render(request,"login.html",{"error":"不可为空"})
        # 验证用户名密码,为真返回这个用户信息,为假返回空
        user = authenticate(username=username,password=password)
        if not user:
            return render(request, "login.html", {"error": "用户名或密码错误"})
        else:
            # 判断用户是否激活账号
            if not user.is_active:
                return render(request, "login.html", {"error": "未激活"})

        # 处理数据
        # 记住用户的登陆状态
        login(request,user)
        # 获取GET中的next的值,没有就给定一个动态链接
        next_url = request.GET.get("next",reverse("goods:index"))
        result = redirect(next_url)

        if affirm == "on":
            result.set_cookie("username",username,max_age=7*24*3600)
        else:
            result.delete_cookie("username")

        # 返回结果
        return result


# 退出
class Logoutview(View):

    def get(self,request):
        # django内置退出函数
        logout(request)
        return redirect(reverse("goods:index"))


# 个人信息
class Userinfoview(LoginRequiredMixin,View):

    def get(self, request):

        # 获取用户的个人信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # 获取用户的历史浏览记录
        # 创建一个redis操作对象
        con = get_redis_connection('default')

        history_key = 'history_%d'%user.id

        # 获取用户最新浏览的5个商品的id
        sku_ids = con.lrange(history_key, 0, 4) # [2,3,1]

        # 遍历获取用户浏览的商品信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        # 组织上下文
        context = {'page':'user',
                   'address':address,
                   'goods_li':goods_li}

        # 除了你给模板文件传递的模板变量之外，django框架会把request.user也传给模板文件
        return render(request, 'user_center_info.html', context)

    def post(self,request):

        return render(request, "user_center_info.html")


# 订单界面
class Userorderview(LoginRequiredMixin,View):

    def get(self,request,page_num):
        user = request.user
        order_infos = OrderInfo.objects.filter(user=user).order_by('-create_time')
        # 获取分页对象
        paginator = Paginator(order_infos,2)
        # 获取总页数
        pages = paginator.num_pages
        # 页码数为空或大于总页数,赋值为１
        if not page_num:
            page_num = 1
        elif pages < int(page_num):
            page_num = 1
        # 获取当前页数据
        page = paginator.page(page_num)
        # 总页数小于等于五,显示所有
        # 当前页小于等于３,显示1到5
        # 当前页为后三页,显示最后5页
        # 显示前后共5页
        # 获取页码列表
        if pages <=5:
            page_list = range(1,pages+1)
        elif int(page_num)<=3:
            page_list = range(1,6)
        elif int(page_num) > pages-3:
            page_list = range(pages-4,pages+1)
        else:
            page_list = range(page_num-2,page_num+3)

        context = {"order_infos":order_infos,"page":page,"page_list":page_list}

        return render(request, "user_center_order.html",context)


# 收件人信息界面
class Addressview(LoginRequiredMixin,View):

    def get(self, request):


        user = request.user
        address = Address.objects.get_default_address(user)

        return render(request, "user_center_site.html",{"page":"address","address":address})

    def post(self, request):

        # 获取数据
        receiver = request.POST.get("receiver")
        addr = request.POST.get("addr")
        zip_code = request.POST.get("zip_code")
        phone = request.POST.get("phone")

        # 校验数据
        if not all([receiver,addr,phone]):
            return render(request, "user_center_site.html",{"error":"数据不完整"})

        ret = re.match(r'^1[3|4|5|7|8][0-9]{9}$',phone)
        if not ret:
            return render(request, "user_center_site.html", {"error": "手机号码不正确"})

        # 业务处理：添加用户收货地址
        user = request.user
        defa = Address.objects.filter(user=user,is_default=True)
        if defa:
            is_default = False
        else:
            is_default = True

        Address.objects.create(user=user,receiver=receiver,addr=addr,
                               zip_code=zip_code,phone=phone,
                               is_default=is_default)

        return redirect(reverse("user:address"))
























