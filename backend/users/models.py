from rest_framework.exceptions import ValidationError

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from recipes.constants import EMAIL_MAX_LENGTH, NAME_MAX_LENGTH


class CustomUser(AbstractUser):
    """CustomUser model."""

    email = models.EmailField(_('Email'),
                              max_length=EMAIL_MAX_LENGTH, unique=True)
    username = models.CharField(
        verbose_name='Username',
        max_length=NAME_MAX_LENGTH,
        unique=True,
        validators=(UnicodeUsernameValidator(), ),
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=NAME_MAX_LENGTH,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=NAME_MAX_LENGTH,
    )
    password = models.CharField(
        verbose_name='Пароль',
        max_length=NAME_MAX_LENGTH,
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name'
    )
    USER = 'user'
    ADMIN = 'admin'
    ROLES_CHOICES = [
        (USER, 'user'),
        (ADMIN, 'admin'),
    ]

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=('username', 'email'),
                name='unique_user'
            )
        ]

    def __str__(self):
        return self.username

    def validate_username(self, value):
        """Validate the username."""
        if value == 'me':
            raise ValidationError('Пользователь с таким именем уже существует!')
        return value


class Follow(models.Model):
    """Follow model."""

    follower = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='follower',
        verbose_name='Подписчик')
    following = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='following',
        verbose_name='Автор')

    class Meta:
        ordering = ['follower']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'following'],
                name='unique_follow',
            )
        ]

    def __str__(self):
        return f'Author: {self.following}, follower: {self.follower}'
