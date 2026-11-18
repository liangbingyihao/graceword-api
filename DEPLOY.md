# Grace Word Web 部署流程

BibleArt API 規格：[docs/BIBLEART-API.md](docs/BIBLEART-API.md)

## 目標

- 正式 image 來源是 `graceword-api`，不是 `graceword-web`。
- 本機負責修改程式與內容。
- 建置與 image push 只在測試主機執行。
- 正式主機只負責 pull、up 與內容 volume 更新。
- 不在正式主機 build 或 push image。
- 文件與腳本不寫入任何主機 IP；執行前只設定 `REMOTE_HOST`。

## 主機角色

| 角色 | 工作 |
| --- | --- |
| 本機 | 修改 `graceword-api`、產生 BibleArt catalog |
| 測試主機 | build image、smoke test、push image |
| 正式主機 | pull image、restart、更新 BibleArt content volume |

測試主機與正式主機都是 `linux/amd64`；本機可能是 arm64，不在本機 build 正式 image。

## 一次性設定

複製環境範例：

```bash
cp deploy/env.example deploy/env
```

`deploy/env` 已被 git 忽略，不進 repo。內容只有非敏感設定：

```bash
REMOTE_HOST=
IMAGE_REPO=bliang0623/graceword-api
REMOTE_BUILD_DIR=/tmp/graceword-api-build
REMOTE_CONTENT_DIR=/opt/graceword/graceword-py/bibleart
REMOTE_COMPOSE_DIR=/opt/graceword
DOCKER_CONFIG_DIR=/root/.docker-bliang
SMOKE_PORT=18080
```

執行每個腳本前，先設定 `REMOTE_HOST`：

```bash
export REMOTE_HOST=root@<host>
```

或直接修改 `deploy/env`。

### 測試主機 Docker Hub

測試主機使用獨立 Docker config，避免覆蓋原本帳號：

```bash
ssh "$REMOTE_HOST" \
  "mkdir -p /root/.docker-bliang && chmod 700 /root/.docker-bliang"

ssh "$REMOTE_HOST" \
  "DOCKER_CONFIG=/root/.docker-bliang docker login -u <dockerhub-user>"
```

`IMAGE_REPO` 必須是該 Docker Hub 帳號有 push 權限的 repo。

### BibleArt catalog volume

測試主機與正式主機都要有：

```text
/opt/graceword/graceword-py/bibleart/manifest.json
/opt/graceword/graceword-py/bibleart/stories/*.json
```

正式機 compose 的 `graceword-py` 第一次要加：

```yaml
image: bliang0623/graceword-api:${GRACEWORD_PY_IMAGE_TAG:-2026060101}
volumes:
  - ./graceword-py/bibleart:/app/app/data/bibleart:ro
environment:
  BIBLEART_CATALOG_ROOT: /app/app/data/bibleart
```

image repo 若改成其他帳號，這行也要同步調整。

## 修改 Web 程式後

### 1. Build 與 push

`REMOTE_HOST` 設為測試主機：

```bash
export REMOTE_HOST=root@<test-host>
./deploy/build-and-push.sh
```

腳本會：

1. 從本機 rsync 程式到測試主機。
2. 排除 `.git`、`app/data/bibleart`、`tests`、`deploy/env`。
3. 在測試主機 build `linux/amd64` image。
4. 用測試主機的獨立 Docker config push。
5. 輸出完整 image tag 與 digest。

Image tag 格式：

```text
YYYYMMDD-HHMMSS-<git-short-sha>
```

工作目錄有未提交變更時會加 `-dirty`。

### 2. Smoke test

```bash
export REMOTE_HOST=root@<test-host>
./deploy/smoke-test.sh bliang0623/graceword-api:<tag>
```

腳本會用測試主機上的 BibleArt catalog volume 啟動臨時容器，驗證：

- 無 JWT `GET /api/bibleart/stories` → 401
- 有效 JWT → 200
- `GET /api/bibleart/stories/birth` → 3 題
- 舊 API route 必須存在：
  - `/api/session/message`
  - `/api/session/<id>` GET
  - `/api/message/<id>/retry`
  - `/api/message/<id>/stop`
- `X-User-Id` + Bearer 仍會被舊 API 接受

### 3. 正式部署 image

`REMOTE_HOST` 改為正式主機：

```bash
export REMOTE_HOST=root@<prod-host>
./deploy/deploy-image.sh <tag>
```

腳本會：

1. 備份正式主機 compose 到 `/tmp`。
2. 使用 `GRACEWORD_PY_IMAGE_TAG=<tag>` 執行 pull。
3. `docker compose up -d graceword-py`。
4. 檢查執行中的 image 是否為指定 tag。

不要在正式主機 build 或 push。

## 更新 BibleArt 內容

先在 BibleArt repo 產生 catalog：

```bash
cd biblegame
PATH=/opt/homebrew/opt/node@22/bin:$PATH npm run build:app-catalog
```

預設輸出：

```text
biblegame/build/bibleart-app/
```

部署內容：

```bash
export REMOTE_HOST=root@<prod-host>
./deploy/deploy-bibleart-content.sh /path/to/biblegame/build/bibleart-app
```

腳本會：

1. 驗證本機 manifest 與 stories JSON。
2. 備份正式主機目前內容到 `/tmp/graceword-bibleart-content-*.tgz`。
3. 上傳到 `bibleart.next`。
4. 驗證遠端 JSON 與 `contentVersion`。
5. 原子切換 `bibleart` 與 `bibleart.next`。
6. restart `graceword-py`。
7. 失敗時嘗試還原上一版。

內容更新不需要 rebuild image。

## Rollback

### Image

```bash
export REMOTE_HOST=root@<prod-host>
./deploy/deploy-image.sh <previous-tag>
```

### Content

從 `/tmp/graceword-bibleart-content-*.tgz` 解回 volume，再 restart：

```bash
ssh "$REMOTE_HOST" \
  "cd /opt/graceword/graceword-py && tar xzf /tmp/graceword-bibleart-content-<stamp>.tgz"

ssh "$REMOTE_HOST" \
  "cd /opt/graceword && docker compose restart graceword-py"
```

## 日誌

App 與 uWSGI 只輸出到 container stdout/stderr，不寫入容器內檔案。

正式 compose 需要為 `graceword-py` 加上 rotation：

```yaml
logging:
  driver: json-file
  options:
    max-size: "20m"
    max-file: "5"
```

環境變數：

```text
LOG_LEVEL=INFO
LOG_BODY=0
```

- `LOG_BODY=0` 時 400 request body 不寫入 log。
- `Authorization`、`Cookie`、`Set-Cookie` 會遮罩。
- 不使用 `app.log`、`coze.log`。
- 不掛載 log volume。
- 查看日誌：
  ```bash
  docker logs --tail 200 graceword-py
  ```

檢查清單：
- 容器內沒有 `/app/app.log`、`/app/coze.log`。
- `docker logs` 同時看得到 uWSGI request log 與 app log。
- 400 log 不含 token／cookie。

## 檢查清單

- [ ] `REMOTE_HOST` 是正確角色：測試主機 build、正式主機 deploy
- [ ] Image tag 是新的 immutable tag
- [ ] Smoke test 通過
- [ ] 正式機 compose 已使用 `GRACEWORD_PY_IMAGE_TAG`
- [ ] 正式機 volume 已掛載
- [ ] Content `contentVersion` 一致
- [ ] 備份在 `/tmp`
- [ ] 部署後 API 無 JWT 回 401
