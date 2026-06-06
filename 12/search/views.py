import os
import json
import base64
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F
from django.core.paginator import Paginator
from django.conf import settings

from .models import Document, SearchHistory
from .forms import DocumentUploadForm
from .parser import DocumentParser
from .es_manager import ElasticsearchManager

es_manager = ElasticsearchManager()
parser = DocumentParser()


def home(request):
    total_docs = Document.objects.filter(indexed=True).count()
    recent_docs = Document.objects.filter(indexed=True).order_by('-uploaded_at')[:5]
    hot_keywords = SearchHistory.objects.order_by('-search_count')[:10]
    context = {
        'total_docs': total_docs,
        'recent_docs': recent_docs,
        'hot_keywords': hot_keywords,
    }
    return render(request, 'search/home.html', context)


@require_http_methods(['GET', 'POST'])
def upload_document(request):
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            uploaded_file = request.FILES.get('file')
            if uploaded_file:
                if not doc.title:
                    doc.title = os.path.splitext(uploaded_file.name)[0]
                doc.file_size = uploaded_file.size
            doc.save()

            try:
                file_path = doc.file.path
                file_type = parser.get_file_type(file_path)
                doc.file_type = file_type

                content = parser.parse(file_path)
                doc.content = content or ''
                doc.save()

                es_manager.index_document(
                    doc_id=doc.id,
                    title=doc.title,
                    content=doc.content,
                    file_type=doc.file_type,
                    file_path=doc.file.url if doc.file else '',
                    file_size=doc.file_size,
                    uploaded_at=doc.uploaded_at,
                )
                doc.indexed = True
                doc.save()
                success = True
                message = '文档上传并索引成功！'
            except Exception as e:
                success = False
                message = f'文档处理失败: {str(e)}'

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': success,
                    'message': message,
                    'doc_id': doc.id if success else None,
                })
            context = {
                'form': form,
                'success': success,
                'message': message,
            }
            return render(request, 'search/upload.html', context)
    else:
        form = DocumentUploadForm()
    return render(request, 'search/upload.html', {'form': form})


@require_http_methods(['GET'])
def search_document(request):
    query = request.GET.get('q', '').strip()
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))

    context = {
        'query': query,
        'results': [],
        'total': 0,
        'page': page,
        'page_size': page_size,
        'total_pages': 0,
        'hot_keywords': SearchHistory.objects.order_by('-search_count')[:15],
        'search_history': SearchHistory.objects.order_by('-last_searched')[:10],
    }

    if not query:
        return render(request, 'search/search.html', context)

    history, created = SearchHistory.objects.get_or_create(
        query=query,
        defaults={'search_count': 1}
    )
    if not created:
        SearchHistory.objects.filter(pk=history.pk).update(
            search_count=F('search_count') + 1
        )

    try:
        search_result = es_manager.search(query, page, page_size)
        context.update(search_result)
        total_pages = context.get('total_pages', 0)
        if total_pages > 0:
            window = 2
            start = max(1, page - window)
            end = min(total_pages, page + window)
            page_range = []
            if start > 1:
                page_range.append(1)
                if start > 2:
                    page_range.append('...')
            page_range.extend(range(start, end + 1))
            if end < total_pages:
                if end < total_pages - 1:
                    page_range.append('...')
                page_range.append(total_pages)
            context['page_range'] = page_range
    except Exception as e:
        context['error'] = f'搜索出错: {str(e)}'

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'total': context['total'],
            'page': context['page'],
            'page_size': context['page_size'],
            'total_pages': context['total_pages'],
            'results': context.get('results', []),
        })
    return render(request, 'search/search.html', context)


@require_http_methods(['GET'])
def document_detail(request, doc_id):
    doc = get_object_or_404(Document, pk=doc_id)
    query = request.GET.get('q', '')
    context = {
        'doc': doc,
        'query': query,
    }
    return render(request, 'search/detail.html', context)


@require_http_methods(['GET'])
def document_list(request):
    docs = Document.objects.all().order_by('-uploaded_at')
    paginator = Paginator(docs, 20)
    page = int(request.GET.get('page', 1))
    page_obj = paginator.get_page(page)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'search/document_list.html', context)


@require_http_methods(['POST'])
def delete_document(request, doc_id):
    doc = get_object_or_404(Document, pk=doc_id)
    try:
        es_manager.delete_document(doc_id)
    except Exception:
        pass
    doc.delete()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('search:document_list')


@require_http_methods(['GET'])
def hot_keywords_api(request):
    limit = int(request.GET.get('limit', 50))
    keywords = SearchHistory.objects.order_by('-search_count')[:limit]
    data = [{'word': kw.query, 'count': kw.search_count} for kw in keywords]
    return JsonResponse({'keywords': data})


@require_http_methods(['GET'])
def wordcloud_image(request):
    try:
        from wordcloud import WordCloud
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        limit = int(request.GET.get('limit', 100))
        keywords = SearchHistory.objects.order_by('-search_count')[:limit]
        freq_dict = {kw.query: kw.search_count for kw in keywords}

        if not freq_dict:
            return HttpResponse(status=204)

        font_path = None
        possible_fonts = [
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simhei.ttf',
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/System/Library/Fonts/PingFang.ttc',
        ]
        for fp in possible_fonts:
            if os.path.exists(fp):
                font_path = fp
                break

        wc = WordCloud(
            width=800,
            height=400,
            background_color='white',
            font_path=font_path,
            max_words=200,
            collocations=False,
            colormap='viridis',
        )
        wc.generate_from_frequencies(freq_dict)

        img_buffer = BytesIO()
        plt.figure(figsize=(10, 5))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.savefig(img_buffer, format='PNG', dpi=100, bbox_inches='tight', pad_inches=0)
        plt.close()
        img_buffer.seek(0)

        return HttpResponse(img_buffer.getvalue(), content_type='image/png')
    except ImportError as e:
        return JsonResponse({'error': f'缺少依赖: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['GET'])
def wordcloud_data(request):
    limit = int(request.GET.get('limit', 100))
    keywords = SearchHistory.objects.order_by('-search_count')[:limit]
    data = [{'name': kw.query, 'value': kw.search_count} for kw in keywords]
    return JsonResponse(data, safe=False)
