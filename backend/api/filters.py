from django_filters import FilterSet, ModelMultipleChoiceFilter, NumberFilter
from recipes.models import Ingredient, Recipe, Tag
from rest_framework.filters import SearchFilter


class RecipeFilter(FilterSet):
    """Recipe filter by different params."""

    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    is_favorited = NumberFilter(method='get_is_favorited')
    is_in_shopping_cart = NumberFilter(
        method='get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def get_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(favorites__user=self.request.user.id)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_cart__user=self.request.user.id)
        return queryset


class IngredientFilter(SearchFilter):
    """Filter ingredient by name."""

    search_param = 'name'

    class Meta:
        model = Ingredient
        fields = ('name',)
