import warnings
from django.conf import settings
from datetime import datetime


class ElasticsearchManager:
    def __init__(self):
        es_config = getattr(settings, 'ELASTICSEARCH_DSL', {})
        default_config = es_config.get('default', {})
        self._client_kwargs = dict(default_config)
        self.index_name = getattr(settings, 'ES_INDEX_NAME', 'documents')
        self._es = None
        warnings.filterwarnings('ignore', category=Warning,
                                message='.*Unverified HTTPS.*')

    @property
    def es(self):
        if self._es is None:
            from elasticsearch import Elasticsearch
            kwargs = dict(self._client_kwargs)
            hosts = kwargs.pop('hosts', 'https://localhost:9200')
            if 'http_auth' in kwargs:
                auth = kwargs.pop('http_auth')
                if isinstance(auth, (tuple, list)) and len(auth) == 2:
                    kwargs['basic_auth'] = (str(auth[0]), str(auth[1]))
            if isinstance(hosts, str):
                hosts = [hosts]
            self._es = Elasticsearch(hosts, **kwargs)
        return self._es

    def _health_check(self):
        try:
            return self.es.ping()
        except Exception:
            return False

    def create_index(self):
        try:
            if self.es.indices.exists(index=self.index_name):
                return True
        except Exception:
            pass
        mappings = {
            'settings': {
                'number_of_shards': 1,
                'number_of_replicas': 0,
                'analysis': {
                    'analyzer': {
                        'ik_max_word': {
                            'type': 'custom',
                            'tokenizer': 'standard',
                            'filter': ['lowercase']
                        },
                        'ik_smart': {
                            'type': 'custom',
                            'tokenizer': 'standard',
                            'filter': ['lowercase']
                        }
                    }
                }
            },
            'mappings': {
                'properties': {
                    'doc_id': {'type': 'integer'},
                    'title': {
                        'type': 'text',
                        'analyzer': 'ik_max_word',
                        'search_analyzer': 'ik_smart',
                        'boost': 3.0
                    },
                    'content': {
                        'type': 'text',
                        'analyzer': 'ik_max_word',
                        'search_analyzer': 'ik_smart'
                    },
                    'file_type': {'type': 'keyword'},
                    'file_path': {'type': 'keyword'},
                    'file_size': {'type': 'long'},
                    'uploaded_at': {'type': 'date'},
                }
            }
        }
        try:
            self.es.indices.create(index=self.index_name,
                                   settings=mappings['settings'],
                                   mappings=mappings['mappings'])
            return True
        except Exception as e:
            if 'resource_already_exists' in str(e):
                return True
            raise

    def delete_index(self):
        try:
            if self.es.indices.exists(index=self.index_name):
                self.es.indices.delete(index=self.index_name)
                return True
        except Exception:
            pass
        return False

    def index_document(self, doc_id: int, title: str, content: str,
                       file_type: str, file_path: str, file_size: int,
                       uploaded_at: datetime):
        self.create_index()
        document = {
            'doc_id': doc_id,
            'title': title,
            'content': content,
            'file_type': file_type,
            'file_path': file_path,
            'file_size': file_size,
            'uploaded_at': uploaded_at,
        }
        self.es.index(index=self.index_name, id=str(doc_id), document=document)
        return True

    def update_document(self, doc_id: int, **kwargs):
        self.es.update(index=self.index_name, id=str(doc_id), doc=kwargs)
        return True

    def delete_document(self, doc_id: int):
        try:
            if self.es.exists(index=self.index_name, id=str(doc_id)):
                self.es.delete(index=self.index_name, id=str(doc_id))
                return True
        except Exception:
            pass
        return False

    def search(self, query: str, page: int = 1, page_size: int = 10):
        self.create_index()
        from_ = (page - 1) * page_size
        search_kwargs = {
            'index': self.index_name,
            'query': {
                'multi_match': {
                    'query': query,
                    'fields': ['title^3', 'content'],
                    'type': 'best_fields',
                    'operator': 'or'
                }
            },
            'highlight': {
                'fields': {
                    'title': {
                        'pre_tags': ['<em class="highlight">'],
                        'post_tags': ['</em>'],
                        'number_of_fragments': 0
                    },
                    'content': {
                        'pre_tags': ['<em class="highlight">'],
                        'post_tags': ['</em>'],
                        'fragment_size': 200,
                        'number_of_fragments': 3,
                        'no_match_size': 200
                    }
                }
            },
            'sort': [
                {'_score': {'order': 'desc'}},
                {'uploaded_at': {'order': 'desc'}}
            ],
            'from_': from_,
            'size': page_size,
        }
        response = self.es.search(**search_kwargs)
        total_info = response.get('hits', {}).get('total', {})
        if isinstance(total_info, dict):
            total = total_info.get('value', 0)
        else:
            total = total_info or 0
        results = []
        for hit in response.get('hits', {}).get('hits', []):
            source = hit.get('_source', {})
            highlights = hit.get('highlight', {})
            title_highlight = highlights.get('title')
            if title_highlight:
                title = title_highlight[0]
            else:
                title = source.get('title', '')
            content_fragments = highlights.get('content', [])
            if content_fragments:
                content_snippet = ' ... '.join(content_fragments)
            else:
                content_snippet = (source.get('content', '') or '')[:200]
            results.append({
                'doc_id': source.get('doc_id'),
                'title': title,
                'raw_title': source.get('title', ''),
                'content_snippet': content_snippet,
                'file_type': source.get('file_type'),
                'file_path': source.get('file_path'),
                'file_size': source.get('file_size'),
                'uploaded_at': source.get('uploaded_at'),
                'score': hit.get('_score', 0),
            })
        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0,
            'results': results,
        }

    def bulk_index(self, documents):
        from elasticsearch import helpers
        self.create_index()
        actions = []
        for doc in documents:
            actions.append({
                '_index': self.index_name,
                '_id': str(doc['doc_id']),
                '_source': doc,
            })
        helpers.bulk(self.es, actions)
        return True

    def count(self):
        try:
            resp = self.es.count(index=self.index_name)
            return resp.get('count', 0)
        except Exception:
            return 0
