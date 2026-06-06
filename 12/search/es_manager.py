from django.conf import settings
from datetime import datetime


class ElasticsearchManager:
    def __init__(self):
        es_config = getattr(settings, 'ELASTICSEARCH_DSL', {})
        default_config = es_config.get('default', {})
        self.hosts = default_config.get('hosts', 'localhost:9200')
        self.timeout = default_config.get('timeout', 30)
        self.index_name = getattr(settings, 'ES_INDEX_NAME', 'documents')
        self._es = None

    @property
    def es(self):
        if self._es is None:
            from elasticsearch import Elasticsearch
            self._es = Elasticsearch(self.hosts, timeout=self.timeout)
        return self._es

    def create_index(self):
        if self.es.indices.exists(index=self.index_name):
            return True
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
        self.es.indices.create(index=self.index_name, body=mappings)
        return True

    def delete_index(self):
        if self.es.indices.exists(index=self.index_name):
            self.es.indices.delete(index=self.index_name)
            return True
        return False

    def index_document(self, doc_id: int, title: str, content: str,
                       file_type: str, file_path: str, file_size: int,
                       uploaded_at: datetime):
        self.create_index()
        body = {
            'doc_id': doc_id,
            'title': title,
            'content': content,
            'file_type': file_type,
            'file_path': file_path,
            'file_size': file_size,
            'uploaded_at': uploaded_at,
        }
        self.es.index(index=self.index_name, id=str(doc_id), body=body)
        return True

    def update_document(self, doc_id: int, **kwargs):
        self.es.update(index=self.index_name, id=str(doc_id), body={'doc': kwargs})
        return True

    def delete_document(self, doc_id: int):
        if self.es.exists(index=self.index_name, id=str(doc_id)):
            self.es.delete(index=self.index_name, id=str(doc_id))
            return True
        return False

    def search(self, query: str, page: int = 1, page_size: int = 10):
        self.create_index()
        from_ = (page - 1) * page_size
        search_body = {
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
            'from': from_,
            'size': page_size,
        }
        response = self.es.search(index=self.index_name, body=search_body)
        total = response['hits']['total']['value'] if isinstance(
            response['hits']['total'], dict) else response['hits']['total']
        results = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            highlights = hit.get('highlight', {})
            title = highlights.get('title', [source.get('title', '')])[0]
            content_fragments = highlights.get('content', [])
            if content_fragments:
                content_snippet = ' ... '.join(content_fragments)
            else:
                content_snippet = source.get('content', '')[:200]
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
            return self.es.count(index=self.index_name)['count']
        except Exception:
            return 0
