from django.urls import path
from . import views

app_name = 'frontpage'
urlpatterns = [
    path('', views.index, name='index'),  # 数据可视化
    path('query/', views.query, name='query'),  # 数据管理
    # 中国，全球疫情数据修改
    path('china_change/<int:data_id>/', views.china_change, name='china_change'),
    path('foreign_change/<int:data_id>/', views.foreign_change, name='foreign_change'),
]
