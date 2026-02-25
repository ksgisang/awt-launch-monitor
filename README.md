# AWT Launch Monitor

AWT(AI Watch Tester)의 멀티 플랫폼 런칭 현황을 한 곳에서 모니터링하는 CLI 도구.

## 모니터링 대상

| 플랫폼 | 방식 | 확인 항목 |
|---------|------|-----------|
| GitHub | REST + GraphQL API | Stars, Issues, Discussions, Forks |
| DEV.to | REST API | 조회수, 리액션, 댓글 |
| Hashnode | GraphQL API | 리액션, 댓글 |
| Velog, Disquiet 등 | 브라우저 열기 | 수동 확인 |

## 설치

```bash
pip install -r requirements.txt
cp config.example.json config.json
# config.json에 API 토큰 입력
```

## 사용법

```bash
python monitor.py                # 전체 확인
python monitor.py --github       # GitHub만
python monitor.py --devto        # DEV.to만
python monitor.py --hashnode     # Hashnode만
python monitor.py --summary      # 요약만 (댓글 미리보기 생략)
python monitor.py --open-browsers # API 없는 사이트 브라우저로 열기
python monitor.py --notify       # 터미널 출력 + 텔레그램 알림
python monitor.py --silent       # 텔레그램만 전송 (cron/CI용)
```

## 텔레그램 알림

`config.json`의 `telegram` 섹션에 봇 토큰과 채팅 ID를 설정하면 알림을 받을 수 있습니다.

## 자동 실행

### GitHub Actions (권장)

하루 3회 (KST 09:00, 15:00, 21:00) 자동 실행됩니다.

Repository Settings → Secrets에 다음을 등록하세요:

- `GITHUB_TOKEN_AWT` — GitHub Personal Access Token
- `DEVTO_API_KEY` — DEV.to API Key
- `HASHNODE_TOKEN` — Hashnode Personal Access Token
- `TELEGRAM_BOT_TOKEN` — Telegram Bot Token
- `TELEGRAM_CHAT_ID` — Telegram Chat ID

### 로컬 cron

```bash
bash setup_cron.sh
```
