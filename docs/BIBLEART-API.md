# BibleArt API

BibleArt 完整內容 API 供 App WebView 使用，公網 preview 不呼叫此 API。

## 基本資訊

```text
Base path: /api/bibleart
Auth: Authorization: Bearer <JWT>
Content-Type: application/json
```

- 所有 endpoint 都需要 JWT。
- 只支援 `zh-Hant`、`en`。
- 預設語言為 `zh-Hant`。
- 回傳內容來自 runtime catalog volume，不會打包進 image。
- 不像舊 API，BibleArt 不讀 `X-User-Id`，只使用 JWT identity。

## App 開啟方式

Native App 開啟：

```text
https://<host>/bibleart/app/#token=<JWT>
```

前端讀取 fragment 後應立即清除，呼叫 API 時改放 header：

```http
Authorization: Bearer <JWT>
```

JWT 過期時 API 回 `401`，App 應重新帶新 token 開啟。

## 共通回應

成功：

```json
{
  "success": true,
  "data": {}
}
```

應用錯誤：

```json
{
  "success": false,
  "message": "Story not found"
}
```

JWT 錯誤由 Flask-JWT-Extended 回傳，例如：

```json
{
  "msg": "Missing Authorization Header"
}
```

## 狀態碼

| 狀態碼 | 說明 |
| --- | --- |
| 200 | 成功 |
| 304 | ETag 未變 |
| 400 | 不支援語言、日期格式錯誤、缺少 ids |
| 401 | 缺少或無效 JWT |
| 404 | 故事不存在 |
| 503 | catalog 缺失或格式錯誤 |

## 內容版本與快取

`contentVersion` 是 catalog 版本，內容更新後會改變。

- `/stories`：`ETag = contentVersion`
- `/stories/:id`：`ETag = contentVersion-storyId`
- `/questions`：`ETag = contentVersion-questions-ids`
- `/daily`：`Cache-Control: private, no-store`

一般內容 API：

```http
Cache-Control: private, max-age=300
```

可帶：

```http
If-None-Match: "<etag>"
```

未變更時回 `304`。

---

## 1. 故事列表

```http
GET /api/bibleart/stories
```

### Query

| 參數 | 必填 | 說明 |
| --- | --- | --- |
| `lang` | 否 | `zh-Hant` 或 `en`，預設 `zh-Hant` |
| `page` | 否 | 頁碼，預設 `1` |
| `page_size` | 否 | 每頁數量，最大 `200`；不給則回全部 metadata |

### 範例

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://<host>/api/bibleart/stories?lang=zh-Hant&page=1&page_size=20"
```

### Response

```json
{
  "success": true,
  "data": {
    "contentVersion": "4863674b49d9",
    "publishedAt": "2026-11-18T03:06:46.173Z",
    "total": 27,
    "page": 1,
    "pageSize": 20,
    "stories": [
      {
        "id": "birth",
        "title": "降生與童年",
        "intro": "從天使報喜到逃往埃及，跟隨耶穌降生的最初幾幕。",
        "outro": "道成了肉身，住在我們中間。",
        "era": "nt",
        "section": "jesus-life",
        "themes": ["birth", "people"],
        "order": 1,
        "questionIds": ["annunciation", "nativity", "flight_egypt"],
        "questionCount": 3,
        "anchorQuestionId": "nativity",
        "coverImage": "/images/nativity.jpg",
        "coverTitle": "耶穌降生"
      }
    ]
  }
}
```

故事列表**不包含**完整題目、答案或提示。

---

## 2. 單一故事詳情

```http
GET /api/bibleart/stories/:story_id
```

### Path

| 參數 | 必填 | 說明 |
| --- | --- | --- |
| `story_id` | 是 | 故事 ID，例如 `birth` |

### Query

| 參數 | 必填 | 說明 |
| --- | --- | --- |
| `lang` | 否 | `zh-Hant` 或 `en`，預設 `zh-Hant` |

### 範例

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://<host>/api/bibleart/stories/birth?lang=zh-Hant"
```

### Response

```json
{
  "success": true,
  "data": {
    "contentVersion": "4863674b49d9",
    "story": {
      "id": "birth",
      "title": "降生與童年",
      "intro": "從天使報喜到逃往埃及，跟隨耶穌降生的最初幾幕。",
      "outro": "道成了肉身，住在我們中間。",
      "era": "nt",
      "section": "jesus-life",
      "themes": ["birth", "people"],
      "order": 1,
      "questionIds": ["annunciation", "nativity", "flight_egypt"],
      "questionCount": 3,
      "anchorQuestionId": "nativity",
      "coverImage": "/images/nativity.jpg",
      "coverTitle": "耶穌降生"
    },
    "questions": []
  }
}
```

`questions` 為該故事完整 3 題，包含：

- `id`
- `answer`
- `options`
- `hints`
- `scripture`
- `event`
- `image`
- `summary`
- `artNote`
- `verseHints`
- `keyVerse`
- `storyId`
- `regionId`
- `regionName`
- `modernName`
- `geoNote`

錯誤：

- 不存在的 story：`404`
- 不支援語言：`400`
- catalog 缺失：`503`

---

## 3. 每日挑戰

```http
GET /api/bibleart/daily
```

### Query

| 參數 | 必填 | 說明 |
| --- | --- | --- |
| `lang` | 否 | `zh-Hant` 或 `en`，預設 `zh-Hant` |
| `date` | 否 | `YYYY-MM-DD`；不給則用伺服器當天 |

### 範例

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://<host>/api/bibleart/daily?lang=zh-Hant&date=2026-11-17"
```

### Response：故事日

```json
{
  "success": true,
  "data": {
    "contentVersion": "4863674b49d9",
    "date": "2026-11-17",
    "type": "story",
    "story": {},
    "questions": []
  }
}
```

### Response：週日混合

```json
{
  "success": true,
  "data": {
    "contentVersion": "4863674b49d9",
    "date": "2026-11-22",
    "type": "mixed",
    "story": null,
    "questions": []
  }
}
```

- 週一到週六回 `type: "story"`。
- 週日回 `type: "mixed"`，3 題由全部題目池抽取。
- 此 endpoint 不使用 ETag，使用 `private, no-store`。
- 日期格式錯誤回 `400`。

---

## 4. 依 IDs 取題目

```http
GET /api/bibleart/questions
```

主要供 challenge 連結使用。

### Query

| 參數 | 必填 | 說明 |
| --- | --- | --- |
| `ids` | 是 | 逗號分隔的 question IDs，最多取前 50 個 |
| `lang` | 否 | `zh-Hant` 或 `en`，預設 `zh-Hant` |

### 範例

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://<host>/api/bibleart/questions?lang=zh-Hant&ids=annunciation,nativity,missing"
```

### Response

```json
{
  "success": true,
  "data": {
    "contentVersion": "4863674b49d9",
    "questions": [],
    "missing": ["missing"]
  }
}
```

- 回傳順序依 `ids` 傳入順序。
- 重複 ID 會去重。
- 找不到的 ID 放在 `missing`，不直接讓整個 request 失敗。
- 缺少 `ids` 回 `400`。

---

## 內容檔案格式

正式站 volume：

```text
/opt/graceword/graceword-py/bibleart/
  manifest.json
  stories/
    birth.json
    passion.json
    ...
```

`manifest.json`：

```json
{
  "contentVersion": "4863674b49d9",
  "publishedAt": "2026-11-18T03:06:46.173Z",
  "locales": {
    "zh-Hant": {
      "stories": [],
      "questionStory": {}
    },
    "en": {
      "stories": [],
      "questionStory": {}
    }
  }
}
```

`stories/<id>.json`：

```json
{
  "contentVersion": "4863674b49d9",
  "storyId": "birth",
  "story": {
    "zh-Hant": {},
    "en": {}
  },
  "questions": {
    "zh-Hant": [],
    "en": []
  }
}
```

## 安全與限制

- API 需要有效 JWT，不提供公開 anonymous access。
- Public `/bibleart/` static preview 不得呼叫此 API。
- 使用者可將已取得內容保存在本機；JWT 只控制 API 存取，不是 DRM。
- 不把 catalog 放在 `app/static/`。
- 不將 token 放在 query string；App 使用 URL fragment。
- 正式站 Nginx／gateway 必須將 `/api/bibleart/` 轉到 `graceword-py:8080`。

## 目前未提供

```text
/api/bibleart/catalog
/api/bibleart/challenge/:token
/api/bibleart/session
/api/bibleart/handoff
```

第一版只有上述 4 個 endpoint。
