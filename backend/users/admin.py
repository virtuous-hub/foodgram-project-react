from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


class UserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'first_name', 'last_name',
                    'email',)
    ordering = ('email',)


admin.site.register(User, UserAdmin)
