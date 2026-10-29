# 🏢 AI 부서 회의 (ai-dept-meeting)

주제를 하나 던지면 **기획·마케팅·개발·디자인·재무** 5개 부서 AI가 회의를 하고,
진행자 AI가 종합해 **실행 가능한 결과물**을 만들어내는 웹앱입니다.

회의 과정(개회 → 부서별 의견 → 부서 간 토론 → 결론)이 채팅처럼 **실시간으로** 흐릅니다.

## ✨ 특징

- **API 키 불필요.** [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk)가
  Claude Code CLI를 통해 **당신의 Claude 구독 로그인**으로 인증합니다 → 토큰 과금 없음.
- 부서 구성은 `app/agents.py` 의 `DEPARTMENTS` 리스트만 고치면 자유롭게 바꿀 수 있습니다.
- 웹 화면에서 회의 진행이 실시간 스트리밍으로 보입니다.

## 🔧 준비 (한 번만)

1. **Node.js** 설치 후 Claude Code CLI 설치 & 구독 로그인:
   ```bash
   npm install -g @anthropic-ai/claude-code
   claude            # 실행 후 /login 으로 Claude 구독(Pro/Max) 로그인
   ```
2. **Python 3.10+** 에서 의존성 설치:
   ```bash
   pip install -r requirements.txt
   ```
3. (선택) 모델 지정:
   ```bash
   cp .env.example .env      # MODEL=sonnet | opus | haiku
   ```

## ▶️ 실행

```bash
python run.py
```

브라우저에서 **http://localhost:8000** 접속 → 주제 입력 → **회의 시작**.

## 🗂️ 구조

```
app/
├── agents.py      # 부서 정의 (이름·아이콘·역할). 여기만 고치면 부서 변경 가능
├── meeting.py     # 회의 오케스트레이션 (Agent SDK 호출 + 이벤트 스트림)
├── main.py        # FastAPI 서버 (SSE 스트리밍 엔드포인트)
└── static/
    └── index.html # 단일 페이지 프론트엔드
```

## ⚙️ 동작 방식

1. 진행자 AI가 주제를 소개하고 핵심 논점을 정리 (개회)
2. 5개 부서 AI가 각자의 관점에서 초기 의견 제시
3. 각 부서가 다른 부서 의견에 반응 (토론)
4. 진행자 AI가 전체를 종합해 최종 결과물(핵심 결론·실행 계획·리스크·성공 지표) 작성

각 단계는 이전까지의 회의록을 컨텍스트로 받아 실제로 "이어지는 회의"가 됩니다.

## 📝 부서 바꾸기

`app/agents.py` 의 `DEPARTMENTS` 에서 `Department(...)` 항목을 추가/삭제/수정하세요.
`persona` 가 그 부서 AI의 관점(system prompt)이 됩니다.

## ⚠️ 참고

- 구독 로그인 인증은 Claude Code CLI를 통해 이뤄지므로, 이 앱을 돌리는 머신에
  Claude Code가 설치·로그인되어 있어야 합니다.
- 회의는 모델을 12번가량 순차 호출하므로 주제당 1~3분 정도 걸릴 수 있습니다.
  (Max 구독 + `MODEL=opus` 는 품질이 좋고, `sonnet` 은 더 빠릅니다.)
