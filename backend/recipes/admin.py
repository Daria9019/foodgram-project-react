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

    @admin.display(description='В избранном')
    def favorites_number(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


admin.site.register(ShoppingCart)
admin.site.register(Favorite)
