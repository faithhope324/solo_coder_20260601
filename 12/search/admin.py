from django.contrib import admin
from .models import Document, SearchHistory


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'file_type', 'file_size', 'uploaded_at', 'indexed')
    list_filter = ('file_type', 'indexed', 'uploaded_at')
    search_fields = ('title', 'content')
    readonly_fields = ('uploaded_at', 'file_size', 'file_type')


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('query', 'search_count', 'last_searched')
    search_fields = ('query',)
    readonly_fields = ('search_count', 'last_searched')
