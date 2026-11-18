from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from services.bibleart_service import BibleArtError, BibleArtService

bibleart_bp = Blueprint('bibleart', __name__)


def _error(error):
    return jsonify({
        'success': False,
        'message': error.message,
    }), error.status_code


def _json_response(data, etag=None, no_store=False):
    response = jsonify({
        'success': True,
        'data': data,
    })
    if no_store:
        response.headers['Cache-Control'] = 'private, no-store'
    else:
        response.headers['Cache-Control'] = 'private, max-age=300'
    if etag:
        response.set_etag(etag)
        response = response.make_conditional(request)
    return response


@bibleart_bp.route('/stories', methods=['GET'])
@jwt_required()
def list_stories():
    language = request.args.get('lang', 'zh-Hant')
    page = request.args.get('page', 1, type=int) or 1
    page_size = request.args.get('page_size', type=int)
    if page_size is not None and page_size <= 0:
        page_size = None
    if page_size is not None:
        page_size = min(page_size, 200)

    try:
        data = BibleArtService.list_stories(language, page, page_size)
    except BibleArtError as error:
        return _error(error)

    return _json_response(data, etag=data['contentVersion'])


@bibleart_bp.route('/stories/<story_id>', methods=['GET'])
@jwt_required()
def get_story(story_id):
    language = request.args.get('lang', 'zh-Hant')
    try:
        data = BibleArtService.get_story(story_id, language)
    except BibleArtError as error:
        return _error(error)

    etag = f"{data['contentVersion']}-{story_id}"
    return _json_response(data, etag=etag)


@bibleart_bp.route('/daily', methods=['GET'])
@jwt_required()
def daily():
    language = request.args.get('lang', 'zh-Hant')
    day = request.args.get('date')
    try:
        data = BibleArtService.daily(language, day)
    except BibleArtError as error:
        return _error(error)

    return _json_response(data, no_store=True)


@bibleart_bp.route('/questions', methods=['GET'])
@jwt_required()
def questions():
    language = request.args.get('lang', 'zh-Hant')
    ids = [
        item.strip()
        for item in (request.args.get('ids') or '').split(',')
        if item.strip()
    ]
    if not ids:
        return jsonify({
            'success': False,
            'message': 'ids is required',
        }), 400

    try:
        data = BibleArtService.get_questions(ids[:50], language)
    except BibleArtError as error:
        return _error(error)

    etag = f"{data['contentVersion']}-questions-{','.join(ids[:50])}"
    return _json_response(data, etag=etag)
