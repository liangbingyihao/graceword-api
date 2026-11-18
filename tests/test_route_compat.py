from main import gw_app
from utils.security import get_user_id


def test_legacy_routes_are_registered():
    routes = {str(rule) for rule in gw_app.url_map.iter_rules()}
    assert '/api/session/message' in routes
    assert '/api/session/<int:session_id>' in routes
    assert '/api/message/<string:msg_id>/retry' in routes
    assert '/api/message/<string:msg_id>/stop' in routes
    assert '/api/bibleart/stories' in routes


def test_legacy_user_id_header_is_supported():
    headers = {
        'Authorization': 'Bearer test-token',
        'X-User-Id': '7',
    }
    assert get_user_id(headers) == '7'
    assert get_user_id({'X-User-Id': '7'}) is None
