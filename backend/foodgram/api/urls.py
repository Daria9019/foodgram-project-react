from rest_framework import routers
from django.urls import path, include

from api.views import index, TagViewSet, RecipeViewSet, IngredientViewSet, CustomUserViewSet

router = routers.DefaultRouter()
router.register('users', CustomUserViewSet, 'users')
router.register('tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('index', index),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls))
]
