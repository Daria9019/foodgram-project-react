from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Ingredient',
        max_length=100
    )
    measurement_unit = models.CharField(
        verbose_name='Mesure',
        max_length=15
    )

    class Meta:
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Name',
        max_length=16,
        unique=True
    )
    color = models.CharField(
        max_length=16,
        verbose_name='Color'
    )
    slug = models.SlugField(
        max_length=16,
        verbose_name='Slug',
        unique=True
    )

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def __str__(self):
        return f'{self.name}'


class Recipe(models.Model):
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ingredients',
        through='RecipeIngredient',
        related_name='recipe'
    )
    image = models.ImageField(
        verbose_name='Pic',
        upload_to='recipes/'
    )
    name = models.CharField(
        verbose_name='Name',
        max_length=200
    )
    text = models.TextField(
        verbose_name='Description'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Tiem to prepare',
        validators=(MinValueValidator(
            limit_value=1,
            message='Need to be more than 1 min'),
        )
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Tags',
        related_name='recipes'
    )
    pub_date = models.DateTimeField(
        auto_now=True,
        verbose_name='Date'
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'

    def __str__(self):
        return f'{self.name[:50]}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Recipe',
        related_name='recipe_ingredient'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ingredient',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Number',
        validators=(MinValueValidator(
            limit_value=0.01,
            message='More than zero'),
        )
    )

    class Meta:
        verbose_name = 'Ingredient count'
        verbose_name_plural = 'Ingredients count'
        constraints = [
            UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique ingredient for recipe'
            )
        ]

    def __str__(self):
        return (f'{self.recipe}: {self.ingredient.name},'
                f' {self.amount}, {self.ingredient.measurement_unit}')


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='User',
        related_name='favorite'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Recipes',
        related_name='favorite'
    )

    class Meta:
        verbose_name = 'Fav recipe'
        verbose_name_plural = 'Fav recipes'
        constraints = (
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique favorite'
            ),
        )

    def __str__(self):
        return f'{self.recipe} in fav {self.user}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='User',
        related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Recipes',
        related_name='shopping_cart'
    )

    class Meta:
        verbose_name = 'Recipe in cart'
        verbose_name_plural = 'РRecipe in cart'
        constraints = (
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique recipe in shopping cart'
            ),
        )

    def __str__(self):
        return f'{self.recipe} in cart {self.user}'
