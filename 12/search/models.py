import os
from django.db import models
from django.conf import settings


def upload_to(instance, filename):
    return os.path.join('documents', filename)


class Document(models.Model):
    FILE_TYPE_CHOICES = [
        ('txt', 'TXT'),
        ('pdf', 'PDF'),
        ('doc', 'DOC'),
        ('docx', 'DOCX'),
        ('unknown', '未知'),
    ]

    title = models.CharField(max_length=500, verbose_name='文档标题')
    file = models.FileField(upload_to=upload_to, verbose_name='文件')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES,
                                default='unknown', verbose_name='文件类型')
    file_size = models.BigIntegerField(default=0, verbose_name='文件大小(字节)')
    content = models.TextField(blank=True, default='', verbose_name='文档内容')
    indexed = models.BooleanField(default=False, verbose_name='是否已索引')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')

    class Meta:
        db_table = 'document'
        ordering = ['-uploaded_at']
        verbose_name = '文档'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.file and os.path.isfile(self.file.path):
            try:
                os.remove(self.file.path)
            except Exception:
                pass
        super().delete(*args, **kwargs)


class SearchHistory(models.Model):
    query = models.CharField(max_length=500, unique=True, verbose_name='搜索词')
    search_count = models.PositiveIntegerField(default=1, verbose_name='搜索次数')
    last_searched = models.DateTimeField(auto_now=True, verbose_name='最后搜索时间')

    class Meta:
        db_table = 'search_history'
        ordering = ['-search_count', '-last_searched']
        verbose_name = '搜索历史'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.query} ({self.search_count})'
