from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='index'),
    path('query_results', views.query_results, name='query_results'),
    path('add_transaction', views.add_transaction, name='add_transaction'),
    path('index', views.index, name='index'),
    path('buy_stocks', views.buy_stocks, name='buy_stocks'),
]