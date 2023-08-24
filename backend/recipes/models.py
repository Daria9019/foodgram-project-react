from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from users.models import CustomUser
from .constants import NAME_MAX_LENGTH, COLOR_MAX_LENGTH
from django.conf import settings


class Ingredient(models.Model):
    name = models.CharField(max_length=NAME_MAX_LENGTH,
                            verbose_name='Ingredient')
    measurement_unit = models.CharField(max_length=NAME_MAX_LENGTH,
                                        verbose_name='Mesure')

    class Meta:
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'
        ordering = ['name']
        constraints = [
            UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(max_length=NAME_MAX_LENGTH, verbose_name='Name',
                            unique=True)
    color = models.CharField(max_length=COLOR_MAX_LENGTH, unique=True,
                             verbose_name='Color')
    slug = models.SlugField(unique=True, max_length=NAME_MAX_LENGTH)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (цвет: {self.color})"


class Recipe(models.Model):
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'),
        verbose_name='Ingredients'
    )
    image = models.ImageField(
        'Pic',
        upload_to=settings.IMAGE_UPLOAD_PATH
    )
    name = models.CharField(max_length=NAME_MAX_LENGTH,
                            verbose_name='Name')
    text = models.TextField(verbose_name='Description',
                            help_text='Write something!')
    cooking_time = models.PositiveIntegerField(
        'Time to prepare',
        validators=[MinValueValidator(1,
                                      message='Need '
                                              'to '
                                              'be '
                                              'more '
                                              'than '
                                              '1 min!')]
    )
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                               verbose_name='Author')
    tags = models.ManyToManyField(
        Tag,
        related_name='tags',
        verbose_name='Tags'
    )
    pub_date = models.DateTimeField(
        verbose_name='Date',
        auto_now_add=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'

    def __str__(self):
        return f' {self.name}. Recipe author: {self.author}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipe_ingredient',
                               verbose_name='Recipe')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   verbose_name='Ingredient')
    amount = models.PositiveIntegerField(
        verbose_name='Number',
        validators=[
            MinValueValidator(1, message='More '
                                         'than '
                                         'zero!')]
    )

    class Meta:
        ordering = ['ingredient']
        verbose_name = 'Ingredient count'
        verbose_name_plural = 'Ingredients count'
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='ingredient_unique_amount_in_recipe'
            )
        ]

    def __str__(self):
        return f"{self.amount} {self.ingredient}"


class Favorite(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='User',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Recipes',
    )

    class Meta:
        verbose_name = 'Fav recipe'
        verbose_name_plural = 'Fav recipes'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_favorite')
        ]

    def __str__(self):
        return f'{self.recipe} in fav {self.user}!'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='User',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Recipes',
    )

    class Meta:
        verbose_name = 'Recipe in cart'
        verbose_name_plural = 'Recipes in cart'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_shopping_cart')
        ]

    def __str__(self):
        return f'{self.recipe} in cart {self.user}!'

