from django.contrib import admin

from enhydris_synoptic.models import View


@admin.register(View)
class ViewAdmin(admin.ModelAdmin):
    pass
