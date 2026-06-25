from django.conf import settings
from django.db import models


class BaseModel(models.Model):
    id = models.BigAutoField(primary_key=True, verbose_name="ID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="修改时间")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
        verbose_name="创建人",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
        verbose_name="修改人",
    )
    is_deleted = models.BooleanField(default=False, verbose_name="逻辑删除")
    remark = models.TextField(null=True, blank=True, verbose_name="备注")

    class Meta:
        abstract = True


class City(BaseModel):
    name = models.CharField(max_length=64, unique=True, verbose_name="城市名称")
    code = models.CharField(max_length=32, unique=True, verbose_name="城市编码")
    region = models.CharField(max_length=64, null=True, blank=True, verbose_name="所属地区")

    class Meta:
        db_table = "city"
        verbose_name = "城市"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Organization(BaseModel):
    name = models.CharField(max_length=128, verbose_name="组织名称")
    code = models.CharField(max_length=64, unique=True, verbose_name="组织编码")
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="上级组织",
    )

    class Meta:
        db_table = "organization"
        verbose_name = "组织"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Employee(BaseModel):
    name = models.CharField(max_length=64, verbose_name="员工姓名")
    job_no = models.CharField(max_length=64, unique=True, verbose_name="工号")
    phone = models.CharField(max_length=32, null=True, blank=True, verbose_name="手机号")
    email = models.EmailField(null=True, blank=True, verbose_name="邮箱")
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="employees",
        verbose_name="所属组织",
    )

    class Meta:
        db_table = "employee"
        verbose_name = "员工"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.name}({self.job_no})"


class ComputerRoom(BaseModel):
    STATUS_CHOICES = (
        ("enabled", "启用"),
        ("disabled", "停用"),
        ("maintenance", "维护中"),
    )

    name = models.CharField(max_length=128, verbose_name="机房名称")
    code = models.CharField(max_length=64, verbose_name="机房编码")
    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="computer_rooms",
        verbose_name="所属城市",
    )
    address = models.CharField(max_length=255, null=True, blank=True, verbose_name="机房地址")
    manager = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_rooms",
        verbose_name="机房负责人",
    )
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default="enabled",
        verbose_name="机房状态",
    )

    class Meta:
        db_table = "computer_room"
        verbose_name = "机房"
        verbose_name_plural = verbose_name
        unique_together = ("city", "code")

    def __str__(self):
        return f"{self.city.name}-{self.name}"


class Host(BaseModel):
    HOST_TYPE_CHOICES = (
        ("physical", "物理机"),
        ("virtual", "虚拟机"),
        ("cloud", "云主机"),
    )
    ENV_CHOICES = (
        ("dev", "开发环境"),
        ("test", "测试环境"),
        ("prod", "生产环境"),
    )
    STATUS_CHOICES = (
        ("running", "运行中"),
        ("stopped", "已停止"),
        ("maintenance", "维护中"),
        ("offline", "已下线"),
    )

    hostname = models.CharField(max_length=128, unique=True, verbose_name="主机名")
    ip_address = models.GenericIPAddressField(unique=True, verbose_name="主机IP")
    manage_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="管理IP")
    computer_room = models.ForeignKey(
        ComputerRoom,
        on_delete=models.PROTECT,
        related_name="hosts",
        verbose_name="所属机房",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="hosts",
        verbose_name="所属组织",
    )
    owner = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_hosts",
        verbose_name="负责人",
    )
    host_type = models.CharField(
        max_length=32,
        choices=HOST_TYPE_CHOICES,
        default="physical",
        verbose_name="主机类型",
    )
    environment = models.CharField(
        max_length=32,
        choices=ENV_CHOICES,
        default="prod",
        verbose_name="运行环境",
    )
    os_type = models.CharField(max_length=64, null=True, blank=True, verbose_name="操作系统")
    cpu_core = models.PositiveIntegerField(default=0, verbose_name="CPU核心数")
    memory_gb = models.PositiveIntegerField(default=0, verbose_name="内存GB")
    disk_gb = models.PositiveIntegerField(default=0, verbose_name="磁盘GB")
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default="running",
        verbose_name="主机状态",
    )
    last_check_time = models.DateTimeField(null=True, blank=True, verbose_name="上次检查时间")
    last_check_result = models.BooleanField(null=True, blank=True, verbose_name="上次检查结果")

    class Meta:
        db_table = "host"
        verbose_name = "主机"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.hostname}({self.ip_address})"


class HostDailyStatistic(BaseModel):
    statistic_date = models.DateField(verbose_name="统计日期")
    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="host_statistics",
        verbose_name="城市",
    )
    computer_room = models.ForeignKey(
        ComputerRoom,
        on_delete=models.PROTECT,
        related_name="host_statistics",
        verbose_name="机房",
    )
    host_count = models.PositiveIntegerField(default=0, verbose_name="主机数量")
    reachable_count = models.PositiveIntegerField(default=0, verbose_name="可达数量")
    unreachable_count = models.PositiveIntegerField(default=0, verbose_name="不可达数量")

    class Meta:
        db_table = "host_daily_statistic"
        verbose_name = "每日主机统计"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=["statistic_date", "city", "computer_room"],
                name="uniq_host_daily_statistic_date_city_room",
            )
        ]

    def __str__(self):
        return f"{self.statistic_date}-{self.city.name}-{self.computer_room.name}-{self.host_count}"


class HostConnectivityLog(BaseModel):
    CHECK_TYPE_CHOICES = (
        ("manual", "手动探测"),
        ("batch", "批量探测"),
        ("scheduled", "定时探测"),
    )

    host = models.ForeignKey(
        Host,
        on_delete=models.PROTECT,
        related_name="connectivity_logs",
        verbose_name="主机",
    )
    check_time = models.DateTimeField(verbose_name="探测时间")
    reachable = models.BooleanField(verbose_name="是否可达")
    check_type = models.CharField(
        max_length=32,
        choices=CHECK_TYPE_CHOICES,
        default="manual",
        verbose_name="探测类型",
    )
    target_ip = models.GenericIPAddressField(verbose_name="探测IP")
    command = models.CharField(max_length=255, verbose_name="执行命令")
    duration_ms = models.PositiveIntegerField(default=0, verbose_name="耗时毫秒")
    return_code = models.IntegerField(null=True, blank=True, verbose_name="返回码")
    output = models.TextField(null=True, blank=True, verbose_name="输出内容")

    class Meta:
        db_table = "host_connectivity_log"
        verbose_name = "主机连通性日志"
        verbose_name_plural = verbose_name
        ordering = ("-check_time", "-id")

    def __str__(self):
        result = "可达" if self.reachable else "不可达"
        return f"{self.host.hostname}-{self.check_time}-{result}"
