from pathlib import Path

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from api.bibleart import bibleart_bp


ROOT = Path(__file__).resolve().parents[1]


def make_client():
    app = Flask(__name__)
    app.config.update({
        'TESTING': True,
        'JWT_SECRET_KEY': 'test-secret',
        'BIBLEART_CATALOG_ROOT': str(ROOT / 'app' / 'data' / 'bibleart'),
    })
    JWTManager(app)
    app.register_blueprint(bibleart_bp, url_prefix='/api/bibleart')
    with app.app_context():
        token = create_access_token(identity=1)
    return app.test_client(), {'Authorization': f'Bearer {token}'}


def test_catalog_requires_authentication():
    client, _ = make_client()
    response = client.get('/api/bibleart/stories')
    assert response.status_code == 401


def test_story_list_returns_metadata_without_questions():
    client, headers = make_client()
    response = client.get('/api/bibleart/stories?lang=zh-Hant', headers=headers)
    assert response.status_code == 200
    data = response.get_json()['data']
    assert data['total'] == 27
    assert data['stories'][0]['id'] == 'birth'
    assert 'questions' not in data['stories'][0]


def test_story_detail_returns_three_questions():
    client, headers = make_client()
    response = client.get('/api/bibleart/stories/birth?lang=zh-Hant', headers=headers)
    assert response.status_code == 200
    data = response.get_json()['data']
    assert data['story']['title'] == '降生與童年'
    assert len(data['questions']) == 3
    assert data['questions'][0]['id'] == 'annunciation'


def test_daily_is_deterministic_and_sunday_is_mixed():
    client, headers = make_client()
    first = client.get(
        '/api/bibleart/daily?lang=zh-Hant&date=2026-11-17',
        headers=headers,
    )
    second = client.get(
        '/api/bibleart/daily?lang=zh-Hant&date=2026-11-17',
        headers=headers,
    )
    assert first.status_code == 200
    assert first.get_json()['data']['type'] == 'story'
    assert first.get_json()['data'] == second.get_json()['data']

    sunday = client.get(
        '/api/bibleart/daily?lang=zh-Hant&date=2026-11-22',
        headers=headers,
    )
    assert sunday.status_code == 200
    assert sunday.get_json()['data']['type'] == 'mixed'
    assert len(sunday.get_json()['data']['questions']) == 3


def test_questions_by_ids_preserves_order_and_reports_missing():
    client, headers = make_client()
    response = client.get(
        '/api/bibleart/questions?lang=en&ids=nativity,annunciation,missing',
        headers=headers,
    )
    assert response.status_code == 200
    data = response.get_json()['data']
    assert [question['id'] for question in data['questions']] == [
        'nativity',
        'annunciation',
    ]
    assert data['missing'] == ['missing']


def test_validation_and_missing_story_errors():
    client, headers = make_client()
    assert client.get(
        '/api/bibleart/stories?lang=zh-Hans',
        headers=headers,
    ).status_code == 400
    assert client.get(
        '/api/bibleart/stories/missing?lang=zh-Hant',
        headers=headers,
    ).status_code == 404
    assert client.get('/api/bibleart/questions', headers=headers).status_code == 400


def test_etag_returns_304():
    client, headers = make_client()
    first = client.get('/api/bibleart/stories?lang=zh-Hant', headers=headers)
    etag = first.headers['ETag']
    second = client.get(
        '/api/bibleart/stories?lang=zh-Hant',
        headers={**headers, 'If-None-Match': etag},
    )
    assert second.status_code == 304
