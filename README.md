# 語音 / 影片轉字幕工具（FastAPI + Whisper）

這是一個可直接上 GitHub 的完整專案，支援上傳音訊或影片檔，透過 OpenAI Audio Transcriptions API（`whisper-1`）產生逐段時間戳字幕，並自動輸出 `.srt` 檔案。

## 功能

- 後端：Python + FastAPI
- 前端：原生 HTML/CSS/JavaScript
- 支援格式：`mp3`、`wav`、`m4a`、`mp4`、`mov`
- 使用 `response_format=verbose_json` 取得 segment 級別 `start/end/text`
- 自動生成 SRT：
  - 正確序號
  - `00:00:00,000 --> 00:00:03,500` 時間軸格式
  - 字幕內容
- 自動分行與拆段：
  - 中文每行約 16 字
  - 英文每行約 42 字元
  - 每個字幕 block 最多 2 行
  - 優先在標點符號斷行
  - 句子過長時自動拆成多個 block
  - 依文字長度比例重新分配 start/end

## 專案結構

```text
.
├── app/
│   ├── main.py
│   └── srt_utils.py
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── uploads/
│   └── .gitkeep
├── outputs/
│   └── .gitkeep
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 安裝

```bash
pip install -r requirements.txt
```

## 設定 OPENAI_API_KEY

1. 複製環境變數範本：

```bash
cp .env.example .env
```

2. 編輯 `.env`，填入你的 API key：

```env
OPENAI_API_KEY=your_real_key
```

## 啟動

```bash
uvicorn app.main:app --reload
```

啟動後開啟瀏覽器：

- <http://127.0.0.1:8000>

## 如何上傳並產生 SRT

1. 點擊「選擇檔案」，上傳 `mp3/wav/m4a/mp4/mov`。
2. 點擊「開始轉字幕」。
3. 等待狀態顯示完成。
4. 下載 `.srt` 檔案，或直接在下方預覽區查看內容。

## 檔案儲存路徑

- 上傳暫存：`uploads/`
- 產生字幕：`outputs/`

## API 說明

- `POST /api/transcribe`
  - form-data: `file`
  - 回傳：`download_url`、`preview`
- `GET /api/download/{filename}`
  - 下載對應的 `.srt` 檔案
