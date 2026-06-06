from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_document, name='upload'),
    path('search/', views.search_document, name='search'),
    path('documents/', views.document_list, name='document_list'),
    path('document/<int:doc_id>/', views.document_detail, name='document_detail'),
    path('document/<int:doc_id>/delete/', views.delete_document, name='delete_document'),
    path('api/hot-keywords/', views.hot_keywords_api, name='hot_keywords_api'),
    path('api/wordcloud/', views.wordcloud_image, name='wordcloud_image'),
    path('api/wordcloud-data/', views.wordcloud_data, name='wordcloud_data'),
]
