from io import StringIO

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import CustomUser, Follow

from .filters import IngredientFilter, RecipeFilter
from .paginations import LimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    ChangePasswordSerializer, CustomUserCreateSerializer, CustomUserSerializer,
    FollowSerializer, GetRecipeSerializer, IngredientSerializer,
    RecipeInfoSerializer, RecipeSerializer, TagSerializer,
)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Ingredient view."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)
    permission_classes = (AllowAny,)
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Tag view."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Recipe view."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = LimitPagination

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return GetRecipeSerializer
        return RecipeSerializer

    def get_queryset(self):
        recipes = Recipe.objects.select_related(
            'author').prefetch_related('tags', 'ingredients')
        return recipes

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_obj(self, model, user, pk):
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response({
                'errors': 'You have already add this recipe!'
            }, status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeInfoSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_obj(self, model, user, pk):
        entries = model.objects.filter(user=user, recipe__id=pk).delete()
        if entries[0] == 1:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'You '
                                   'have already '
                                   'delete this recipe!'
                         },
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        if request.method != 'POST':
            return self.delete_obj(Favorite, request.user, pk)
        return self.get_obj(Favorite, request.user, pk)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        if request.method != 'POST':
            return self.delete_obj(ShoppingCart, request.user, pk)
        return self.get_obj(ShoppingCart, request.user, pk)

    @action(detail=False)
    def download_shopping_cart(self, request):
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename=shopping_cart.txt'
        )

        response.write(self.generate_text_file(request.user))

        return response

    def generate_text_file(self, request_user):
        file = StringIO()
        file.write('Shopping list\n\n')

        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request_user).values_list(
            'ingredient__name', 'amount', 'ingredient__measurement_unit')

        ingredient_list = {}
        for name, amount, unit in ingredients:
            if name not in ingredient_list:
                ingredient_list[name] = {'amount': amount, 'unit': unit}
            else:
                ingredient_list[name]['amount'] += amount
        for i, (name, data) in enumerate(ingredient_list.items(), start=1):
            file.write(f"{i}. {name} – {data['amount']} {data['unit']}\n")
        return file.getvalue()


class CustomUserViewSet(UserViewSet):
    """User view."""

    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return CustomUserSerializer
        return CustomUserCreateSerializer

    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request, id=None):
        user = self.request.user
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'status': 'password set'})
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request, id=None):
        serializer = CustomUserSerializer(
            CustomUser.objects.filter(username=self.request.user),
            many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        following = get_object_or_404(CustomUser, id=id)
        follower = self.request.user
        if request.method == 'POST':
            if request.user == following:
                return Response({
                    'errors': 'Can not subscribe yourself!'
                }, status=status.HTTP_400_BAD_REQUEST)

            if Follow.objects.filter(following=following,
                                     follower=follower).exists():
                return Response({
                    'errors': f'You have already subscribed {following}!'
                }, status=status.HTTP_400_BAD_REQUEST)

            new_follow = Follow.objects.create(
                following=following,
                follower=follower
            )
            serializer = FollowSerializer(
                new_follow,
                context={'request': request}
            )
            return Response(serializer.data)
        if request.method == 'DELETE':
            entries = Follow.objects.filter(
                following=following,
                follower=follower).delete()
            if entries[0] == 1:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'errors': 'You '
                                       'are not '
                                       'subscribed on'
                                       'this '
                                       'author!'
                             },
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        follower = request.user
        queryset = Follow.objects.filter(follower=follower)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
