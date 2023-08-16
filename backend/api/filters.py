from django.db.models import BooleanField, ExpressionWrapper, Q
from django_filters.rest_framework import FilterSet, filters
from recipes.models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    """
    Filter ingredient by name
    """
    name = filters.CharFilter(method='filter_by_name')

    class Meta:
        model = Ingredient
        fields = ('name',)

    def filter_by_name(self, qs, name, value):
        return qs.filter(
            Q(name__istartswith=value) | Q(name__icontains=value)
        ).annotate(
            startswith=ExpressionWrapper(
                Q(name__istartswith=value),
                output_field=BooleanField()
            )
        ).order_by('-startswith')


class RecipeFilter(FilterSet):
    """
    Recipe filter by different params
    """
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.BooleanFilter(method='filter_by_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_by_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_by_is_favorited(self, qs, name, value):
        if value and self.request.user.is_authenticated:
            return qs.filter(favorite__user=self.request.user)
        return qs

    def filter_by_is_in_shopping_cart(self, qs, name, value):
        if value and self.request.user.is_authenticated:
            return qs.filter(shopping_cart__user=self.request.user)
        return qs
