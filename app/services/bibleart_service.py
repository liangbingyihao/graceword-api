import hashlib
import json
import re
import threading
from datetime import date
from pathlib import Path

from flask import current_app


class BibleArtError(Exception):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class BibleArtService:
    SUPPORTED_LANGUAGES = ("zh-Hant", "en")
    _cache = {}
    _lock = threading.Lock()

    @classmethod
    def _root(cls):
        return Path(current_app.config["BIBLEART_CATALOG_ROOT"])

    @classmethod
    def _language(cls, language):
        value = language or "zh-Hant"
        if value not in cls.SUPPORTED_LANGUAGES:
            raise BibleArtError("Unsupported language", 400)
        return value

    @classmethod
    def _load_json(cls, path):
        try:
            stat = path.stat()
        except OSError as error:
            raise BibleArtError("BibleArt catalog unavailable", 503) from error

        cache_key = str(path)
        version = (stat.st_mtime_ns, stat.st_size)
        with cls._lock:
            cached = cls._cache.get(cache_key)
            if cached and cached[0] == version:
                return cached[1]

        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError) as error:
            raise BibleArtError("BibleArt catalog unavailable", 503) from error

        with cls._lock:
            cls._cache[cache_key] = (version, data)
        return data

    @classmethod
    def _manifest(cls):
        return cls._load_json(cls._root() / "manifest.json")

    @classmethod
    def _story(cls, story_id, language):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", story_id or ""):
            raise BibleArtError("Story not found", 404)
        path = cls._root() / "stories" / f"{story_id}.json"
        if not path.is_file():
            raise BibleArtError("Story not found", 404)
        data = cls._load_json(path)
        story = (data.get("story") or {}).get(language)
        questions = (data.get("questions") or {}).get(language)
        if story is None or not isinstance(questions, list):
            raise BibleArtError("BibleArt catalog unavailable", 503)
        return story, questions

    @classmethod
    def list_stories(cls, language, page=1, page_size=None):
        language = cls._language(language)
        manifest = cls._manifest()
        locale_data = (manifest.get("locales") or {}).get(language)
        if not locale_data or not isinstance(locale_data.get("stories"), list):
            raise BibleArtError("BibleArt catalog unavailable", 503)

        stories = locale_data["stories"]
        total = len(stories)
        if page_size:
            start = max(0, (max(1, page) - 1) * page_size)
            stories = stories[start : start + page_size]

        return {
            "contentVersion": manifest.get("contentVersion", ""),
            "publishedAt": manifest.get("publishedAt", ""),
            "total": total,
            "page": max(1, page),
            "pageSize": page_size or total,
            "stories": stories,
        }

    @classmethod
    def get_story(cls, story_id, language):
        language = cls._language(language)
        story, questions = cls._story(story_id, language)
        manifest = cls._manifest()
        return {
            "contentVersion": manifest.get("contentVersion", ""),
            "story": story,
            "questions": questions,
        }

    @classmethod
    def get_questions(cls, ids, language):
        language = cls._language(language)
        manifest = cls._manifest()
        locale_data = (manifest.get("locales") or {}).get(language)
        question_story = (locale_data or {}).get("questionStory") or {}

        unique_ids = []
        for question_id in ids:
            if question_id and question_id not in unique_ids:
                unique_ids.append(question_id)

        questions_by_id = {}
        for story_id in {
            question_story[question_id]
            for question_id in unique_ids
            if question_id in question_story
        }:
            _, story_questions = cls._story(story_id, language)
            for question in story_questions:
                questions_by_id[question["id"]] = question

        questions = [
            questions_by_id[question_id]
            for question_id in unique_ids
            if question_id in questions_by_id
        ]
        return {
            "contentVersion": manifest.get("contentVersion", ""),
            "questions": questions,
            "missing": [
                question_id
                for question_id in unique_ids
                if question_id not in questions_by_id
            ],
        }

    @classmethod
    def daily(cls, language, day=None):
        language = cls._language(language)
        try:
            selected_day = date.fromisoformat(day) if day else date.today()
        except ValueError as error:
            raise BibleArtError("Invalid date", 400) from error

        manifest = cls._manifest()
        locale_data = (manifest.get("locales") or {}).get(language)
        if not locale_data or not isinstance(locale_data.get("stories"), list):
            raise BibleArtError("BibleArt catalog unavailable", 503)

        stories = locale_data["stories"]
        if not stories:
            raise BibleArtError("BibleArt catalog unavailable", 503)

        day_key = selected_day.isoformat()
        weekday = selected_day.weekday()

        if weekday != 6:
            seed = int(hashlib.sha256(day_key.encode()).hexdigest()[:8], 16)
            story = stories[(seed + weekday) % len(stories)]
            story_data, questions = cls._story(story["id"], language)
            return {
                "contentVersion": manifest.get("contentVersion", ""),
                "date": day_key,
                "type": "story",
                "story": story_data,
                "questions": questions,
            }

        all_questions = []
        for story in stories:
            _, story_questions = cls._story(story["id"], language)
            all_questions.extend(story_questions)

        selected_questions = sorted(
            all_questions,
            key=lambda question: hashlib.sha256(
                f"{day_key}:{question['id']}".encode()
            ).hexdigest(),
        )[:3]
        return {
            "contentVersion": manifest.get("contentVersion", ""),
            "date": day_key,
            "type": "mixed",
            "story": None,
            "questions": selected_questions,
        }
