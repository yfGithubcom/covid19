from django.db import models


class China(models.Model):
    """中国疫情数据"""
    date = models.CharField(max_length=20)
    area = models.CharField(max_length=40)
    newly = models.IntegerField()
    total = models.IntegerField()
    cure = models.IntegerField()
    dead = models.IntegerField()

    def __str__(self):
        """返回描述模型的字符串"""
        return f"{self.area}"


class ForeignArea(models.Model):
    """全球疫情数据"""
    date = models.CharField(max_length=20)
    country = models.CharField(max_length=40)
    newly = models.IntegerField()
    total = models.IntegerField()
    cure = models.IntegerField()
    dead = models.IntegerField()

    def __str__(self):
        """返回描述模型的字符串"""
        return f"{self.country}"
