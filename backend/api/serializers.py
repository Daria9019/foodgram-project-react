import base64

from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile

from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag,
)
from users.models import CustomUser, Follow


class CustomUserCreateSerializer(UserCreateSerializer):
    """User сreate Serializer."""

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        if value == 'me':
            raise ValidationError(
                'Error creating user by this name'
            )
        return value


class CustomUserSerializer(UserSerializer):
    """User Serializer."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return False if (request is None or request.user.is_anonymous) \
            else Follow.objects.filter(
            follower=obj,
            following=request.user
        ).exists()


class ChangePasswordSerializer(serializers.ModelSerializer):
    """Serializer for changing password."""

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    class Meta:
        model = CustomUser
        fields = ('current_password',
                  'new_password')

    def validate_new_password(self, value):
        validate_password(value)
        return value


class FollowSerializer(serializers.ModelSerializer):
    """Follow сreate Serializer."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    email = serializers.ReadOnlyField(source='following.email')
    id = serializers.ReadOnlyField(source='following.id')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    username = serializers.ReadOnlyField(source='following.username')

    class Meta:
        model = CustomUser
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = ('all',)
        validators = (
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('follower', 'following',),
                message='You have already followed this author.'
            ),
        )

    def validate_following(self, value):
        if self.context['request'].user == value:
            raise serializers.ValidationError('Can not '
                                              'follow yourself.')
        return value

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit_recipes = request.query_params.get('recipes_limit')
        recipe = Recipe.objects.filter(author=obj.following)
        if limit_recipes is not None:
            recipes = recipe.all()[:(int(limit_recipes))]
        else:
            recipes = recipe.all()
        context = {'request': request}
        return RecipeInfoSerializer(
            recipes,
            many=True,
            context=context).data

    def get_is_subscribed(self, obj):
        if not obj.following:
            return False
        return Follow.objects.filter(
            following=obj.follower,
            follower=obj.following
        ).exists()

    @staticmethod
    def get_recipes_count(obj):
        return Recipe.objects.filter(author=obj.following).count()


class Base64ImageField(serializers.ImageField):
    """Convert ing to base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    """Tag serialize."""

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug'
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Ingredient Serializer."""

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Add Ingredient Serializer."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Recipe Serializer."""

    ingredients = RecipeIngredientSerializer(
        many=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        error_messages={'does_not_exist': 'Tag does not exist!'}
    )
    image = Base64ImageField(max_length=None)
    author = CustomUserSerializer(read_only=True)
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'cooking_time',
            'ingredients',
            'author',
            'image',
            'name',
            'text',
            'tags',
            'id'
        )

    def get_ingredients(self, recipe, ingredients):
        ingredient_list = [
            RecipeIngredient(
                ingredient=ingredient_data.pop('id'),
                amount=ingredient_data.pop('amount'),
                recipe=recipe,
            )
            for ingredient_data in ingredients
        ]
        RecipeIngredient.objects.bulk_create(ingredient_list)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.get_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        instance.ingredients.clear()
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        self.get_ingredients(instance, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return GetRecipeSerializer(instance, context=self.context).data


class GetRecipeSerializer(serializers.ModelSerializer):
    """Recipe Serializer."""

    ingredients = RecipeIngredientSerializer(many=True,
                                             read_only=True,
                                             source='recipe_ingredient')
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True, many=False)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class FavoriteSerializer(serializers.ModelSerializer):
    """Favorite Serializer."""

    class Meta:
        model = Favorite
        fields = '__all__'

    def validate(self, data):
        user = data['user']
        if user.favorites.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже был добавлен в Избранное!'
            )
        return data

    def to_representation(self, instance):
        return RecipeInfoSerializer(instance.recipe,
                                    context=self.context).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Cart Serializer."""

    class Meta:
        model = ShoppingCart
        fields = '__all__'

    def to_representation(self, instance):
        return RecipeInfoSerializer(instance.recipe,
                                    context=self.context).data

    def validate(self, data):
        user = data['user']
        if user.shopping_list.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в Список покупок!'
            )
        return data


class RecipeInfoSerializer(serializers.ModelSerializer):
    """Info Serializer."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = 'id', 'name', 'image', 'cooking_time'
        read_only_fields = ('__all__',)
