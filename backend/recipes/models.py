from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from users.models import CustomUser

from .constants import COLOR_MAX_LENGTH, NAME_MAX_LENGTH


class Ingredient(models.Model):
    """Ingredient model."""

    name = models.CharField(max_length=NAME_MAX_LENGTH,
                            verbose_name='Ингредиент')
    measurement_unit = models.CharField(max_length=NAME_MAX_LENGTH,
                                        verbose_name='Мера')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
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
    """Tag model."""

    name = models.CharField(max_length=NAME_MAX_LENGTH, verbose_name='Тэг',
                            unique=True)
    color = models.CharField(max_length=COLOR_MAX_LENGTH, unique=True,
                             verbose_name='Цвет тэга')
    slug = models.SlugField(unique=True, max_length=NAME_MAX_LENGTH)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} (цвет: {self.color})'


class Recipe(models.Model):
    """Recipe model."""

    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'),
        verbose_name='Ингредиенты'
    )
    image = models.ImageField(
        'Картинка',
        upload_to=settings.IMAGE_UPLOAD_PATH
    )
    name = models.CharField(max_length=NAME_MAX_LENGTH,
                            verbose_name='Название рецепта')
    text = models.TextField(verbose_name='Описание рецепта',
                            help_text='Напишите что-нибудь!')
    cooking_time = models.PositiveIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(1,
                                      message='Время '
                                              'приготовления '
                                              'должно '
                                              'быть '
                                              'больше '
                                              '1 '
                                              'минуты!')]
    )
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                               verbose_name='Автор')
    tags = models.ManyToManyField(
        Tag,
        related_name='tags',
        verbose_name='Тэги'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f' {self.name}. Recipe author: {self.author}'


class RecipeIngredient(models.Model):
    """RecipeIngredient model."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='recipe_ingredient',
                               verbose_name='Рецепт')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   verbose_name='Ингредиент')
    amount = models.PositiveIntegerField(
        verbose_name='Количество ингредиентов',
        validators=[
            MinValueValidator(1, message='Количество '
                                         'ингредиентов '
                                         'должно '
                                         'быть '
                                         'больше 0!')]
    )

    class Meta:
        ordering = ['ingredient']
        verbose_name = 'Количество ингредиентов'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='ingredient_unique_amount_in_recipe'
            )
        ]

    def __str__(self):
        return f'{self.amount} {self.ingredient}'


class Favorite(models.Model):
    """Favorite model."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепты',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_favorite')
        ]

    def __str__(self):
        return f'{self.recipe} in fav {self.user}!'


class ShoppingCart(models.Model):
    """ShoppingCart model."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепты',
    )

    class Meta:
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_shopping_cart')
        ]

    def __str__(self):
        return f'{self.recipe} in cart {self.user}!'
