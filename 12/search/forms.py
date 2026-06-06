from django import forms
from .models import Document


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入文档标题（可选，默认使用文件名）'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.txt,.pdf,.doc,.docx'
            }),
        }
        labels = {
            'title': '文档标题',
            'file': '选择文件',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = False
