from django import forms
from .models import China, ForeignArea

"""创建表单(根据模型来创建)，其数据库迁移将由Django根据其指定的模型来自动完成"""


class ChinaForm(forms.ModelForm):
    class Meta:
        # 根据哪个模型来创建该表单
        model = China
        # 该表单类中包含的字段，"__all__"表示全部字段
        fields = '__all__'
        # 设置各字段在表单页面中生成的标签
        labels = {'date': '日期', 'area': '省份', 'newly': '新增确诊', 'total': '累计确诊', 'cure': '累计治愈', 'dead': '累计死亡'}


class ForeignAreaForm(forms.ModelForm):
    class Meta:
        model = ForeignArea
        fields = '__all__'
        labels = {'date': '日期', 'country': '国家', 'newly': '新增确诊', 'total': '累计确诊', 'cure': '累计治愈', 'dead': '累计死亡'}
