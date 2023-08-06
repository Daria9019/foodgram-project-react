from rest_framework import serializers
from recipes.models import Tag, Recipe, RecipeIngredient, Ingredient, Favorite, Shopping_cart
from drf_base64.fields import Base64ImageField
from django.db import transaction



class TagSerializer(serializers.ModelSerializer):
    """Получение списка тегов"""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Список ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Список ингредиентов, включая количество"""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """[GET] Список рецептов."""
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source='recipes')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags',
                  'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image',
                  'text', 'cooking_time')

    def get_is_favorited(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Favorite.objects.filter(user=self.context['request'].user,
                                        recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        return (
            self.context.get('request').user.is_authenticated
            and Shopping_cart.objects.filter(
                user=self.context['request'].user,
                recipe=obj).exists()
        )
    
    def get_ingredients(self, instance):
        return RecipeIngredientSerializer(
            instance.recipe_ingredients.all(),
            many=True
        ).data



class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Создание ингредиента с указанием его количества"""
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """ Создание рецепта."""
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField()
    id = serializers.ReadOnlyField()

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients',
                  'tags', 'image',
                  'name', 'text',
                  'cooking_time')

    def validate(self, data):
        required_fields = ['name', 'text', 'cooking_time', 'tags', 'ingredients']
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(f'{field} - Обязательное поле.')
    
        ingredients = data.get('ingredients', [])
        if len(set(item['id'] for item in ingredients)) != len(ingredients):
            raise serializers.ValidationError('Ингредиенты должны быть уникальны.')
        
        return data
        
    def create(self, validated_data):
        print(validated_data)
        ingredients = validated_data.pop('ingredients')
        instance = super().create(validated_data)

        for ingredient_data in ingredients:
            RecipeIngredient(
                recipe=instance,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            ).save()

        return instance