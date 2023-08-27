from django.contrib import admin

from .models import Ingredient, Tag, Recipe, ShoppingCart, \
    Favorite


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
    search_fields = ['name', 'slug']


class RecipeIngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorites_number')
    search_fields = ['name', 'author__username']
    list_filter = ['tags']
    inlines = (RecipeIngredientInline, )

    def display_tags(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])
    display_tags.short_description = 'Tags'

    @admin.display(description='В избранном')
    def favorites_number(self, obj):
        return Favorite.objects.filter(recipe=obj).count()

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'author').prefetch_related('tags', 'ingredients')


admin.site.register(ShoppingCart)
admin.site.register(Favorite)
