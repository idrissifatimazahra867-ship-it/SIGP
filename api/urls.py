from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeViewSet, PointageViewSet, CongeViewSet, RapportViewSet

router = DefaultRouter()
router.register(r'employes',  EmployeViewSet,  basename='employe')
router.register(r'pointages', PointageViewSet, basename='pointage')
router.register(r'conges',    CongeViewSet,    basename='conge')
router.register(r'rapports',  RapportViewSet,  basename='rapport')

urlpatterns = [
    path('', include(router.urls)),
]