from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Project

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'status', 'created_at', 'participants_count')
    list_filter = ('status', 'created_at', 'owner')
    search_fields = ('name', 'description', 'owner__email', 'owner__name', 'owner__surname')
    ordering = ('-created_at',)
    filter_horizontal = ('participants',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'owner', 'status')
        }),
        (_('Links'), {
            'fields': ('github_url',)
        }),
        (_('Participants'), {
            'fields': ('participants',)
        }),
        (_('Dates'), {
            'fields': ('created_at',)
        }),
    )
    
    def participants_count(self, obj):
        return obj.participants.count()
    participants_count.short_description = 'Количество участников'
    
    def save_model(self, request, obj, form, change):
        if not change:
            super().save_model(request, obj, form, change)
            if obj.owner not in obj.participants.all():
                obj.participants.add(obj.owner)
        else:
            super().save_model(request, obj, form, change)

admin.site.register(Project, ProjectAdmin)