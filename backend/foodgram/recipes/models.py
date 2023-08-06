from django.db import models
from django.contrib.auth import get_user_model

from django.core.validators import RegexValidator
from django.core.validators import MinValueValidator


User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name="Название"
    )
    color = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name="Цвет в HEX"
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Уникальный слаг',
        validators=[RegexValidator(regex='^[-a-zA-Z0-9_]+$')])

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
        )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'),
        verbose_name='Ингредиенты'
    )
    image = models.ImageField(
        upload_to='recipes/',
        blank=True,
        verbose_name='Картинка'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название рецепта'
    )
    text = models.TextField(
        verbose_name='Описание рецепта'
    )
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Время приготовления в мин'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date', )

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='ingredients',
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'

    )
    amount = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_combination'
            )
        ]

    def __str__(self):
        return f"{self.recipe.name} - {self.ingredient.name} ({self.amount})"


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_user',
        verbose_name='Добавил в избранное'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
        verbose_name='Избранный рецепт'
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
                )
        ]

    def __str__(self):
        return f'{self.recipe} в избранном у {self.user}'


class Shopping_cart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_user',
        verbose_name='Пользователь: добавить в корзину'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_recipe',
        verbose_name='Рецепт в корзине'
    )

    class Meta:
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.recipe} в корзине у {self.user}'
