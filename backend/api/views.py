from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS, AllowAny

from recipes.models import Tag, Recipe, Ingredient, \
    RecipeIngredient, ShoppingCart, Favorite
from users.models import Follow, CustomUser
from .filters import RecipeFilter, IngredientFilter
from .serializers import TagSerializer, GetRecipeSerializer, \
    IngredientSerializer, RecipeInfoSerializer, \
    RecipeSerializer, CustomUserSerializer, \
    CustomUserCreateSerializer, FollowSerializer, ChangePasswordSerializer
from .permissions import IsAuthorOrReadOnly
from .paginations import LimitPagination


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
        recipes = Recipe.objects.prefetch_related(
            'recipe_ingredient__ingredient', 'tags'
        )
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
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({
            'errors': 'You have already delete this recipe!'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.get_obj(Favorite, request.user, pk)
        else:
            return self.delete_obj(Favorite, request.user, pk)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self.get_obj(ShoppingCart, request.user, pk)
        else:
            return self.delete_obj(ShoppingCart, request.user, pk)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(quantity=Sum('amount'))
        shopping = 'Shopping list\n'
        shopping += '\n'.join([
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["quantity"]}'
            for ingredient in ingredients
        ])
        response = HttpResponse(shopping,
                                'Content-Type: application/pdf')
        response[
            "Content-Disposition"
        ] = 'attachment; filename="shopping.pdf"'
        return response


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
            subscription = get_object_or_404(Follow,
                                             following=following,
                                             follower=follower)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

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
