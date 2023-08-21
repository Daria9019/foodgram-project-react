from api.filters import IngredientFilter, RecipeFilter
from api.paginations import LimitPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers.recipes import (FavoriteSerializer, IngredientSerializer,
                                     RecipeSerializer, ShoppingCartSerializer,
                                     TagSerializer)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Ingredient view
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
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

    queryset = (Recipe.objects
                .select_related('author')
                .prefetch_related('tags', 'ingredients')
                .all())
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = LimitPagination

    def make_action_post_delete(self, pk, serializer_class):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        object = serializer_class.Meta.model.objects.filter(
            user=user, recipe=recipe
        )

        if self.request.method == 'POST':
            serializer = serializer_class(
                data={'user': user.id, 'recipe': pk},
                context={'request': self.request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            if Recipe.objects.filter(user=user, recipe=recipe).delete():
                return Response(status=status.HTTP_204_NO_CONTENT)
            # if object.exists():
            #     object.delete()
            #     return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'error': 'Recipe not in list'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST', 'DELETE'], detail=True)
    def favorite(self, request, pk):
        return self.make_action_post_delete(pk, FavoriteSerializer)

    @action(methods=['POST', 'DELETE'], detail=True)
    def shopping_cart(self, request, pk):
        return self.make_action_post_delete(pk, ShoppingCartSerializer)

    @action(detail=False)
    def download_shopping_cart(self, request):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            "attachment; filename='shopping_cart.pdf'"
        )

        self.make_pdf(response, request.user)

        return response

    def make_pdf(self, response, request_user):
        pdf_canvas = canvas.Canvas(response)
        arial = ttfonts.TTFont('Arial', 'data/arial.ttf')
        pdfmetrics.registerFont(arial)
        pdf_canvas.setFont('Arial', 14)

        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request_user).values_list(
            'ingredient__name', 'amount', 'ingredient__measurement_unit')

        ingr_list = {}
        for name, amount, unit in ingredients:
            if name not in ingr_list:
                ingr_list[name] = {'amount': amount, 'unit': unit}
            else:
                ingr_list[name]['amount'] += amount
        height = 700

        pdf_canvas.drawString(100, 750, 'Shoping list')
        for i, (name, data) in enumerate(ingr_list.items(), start=1):
            pdf_canvas.drawString(
                80, height,
                f"{i}. {name} – {data['amount']} {data['unit']}")
            height -= 25
        pdf_canvas.showPage()
        pdf_canvas.save()
