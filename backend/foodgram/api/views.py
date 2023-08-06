from django.shortcuts import render, HttpResponse
from rest_framework.viewsets import ModelViewSet

from recipes.models import Tag, Recipe, Ingredient
from api.serializers import TagSerializer, RecipeCreateSerializer, IngredientSerializer, RecipeReadSerializer
from djoser.views import UserViewSet


def index(request):
    return HttpResponse('index')


class CustomUserViewSet(UserViewSet):
    pass


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeReadSerializer

    def get_queryset(self):
        recipes = Recipe.objects.prefetch_related(
            'recipes', 'tags'
        ).all()
        return recipes

    def get_serializer_class(self):
        if self.action == 'create':
            return RecipeCreateSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        recipe = Recipe.objects.create()
        serializer.save(author=self.request.user, recipe=recipe)
