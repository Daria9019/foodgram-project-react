from django.contrib import admin

from .models import CustomUser, Follow


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
    )
    search_fields = ('username',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'following',
        'follower',
    )
    search_fields = ('follower',)
