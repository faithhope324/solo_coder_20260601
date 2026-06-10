from django.urls import path
from . import views

app_name = 'lottery_app'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.index_view, name='lottery_index'),
    
    path('api/prizes/', views.get_prizes_api, name='api_prizes'),
    path('api/chances/', views.get_remaining_chances_api, name='api_chances'),
    path('api/draw/', views.draw_api, name='api_draw'),
    path('api/records/', views.get_lottery_records_api, name='api_records'),
]
