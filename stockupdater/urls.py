from django.urls import path, include

from stockupdater.views import initiate_scripts_execution, TireStockViewSet, UsersViewSet, AveragedTireStockViewSet
from rest_framework import routers

app_name = 'stock_updater'

router = routers.DefaultRouter()
router.register('tire_stock',TireStockViewSet)
router.register('averaged_tire_stock',AveragedTireStockViewSet)
router.register('users',UsersViewSet)

urlpatterns = [
    path('', include(router.urls)),

    # Endpoints for scripting
    path('scripts/stock/update', initiate_scripts_execution, name='initiate_scripts_execution'),

]
