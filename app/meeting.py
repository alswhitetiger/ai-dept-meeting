"""회의 오케스트레이션 (Claude Agent SDK 버전).

Anthropic API 대신 Claude Agent SDK 를 사용한다.
Agent SDK 는 Claude Code CLI 를 감싸며, API 키가 아니라
사용자의 Claude 구독 로그인으로 인증한다. → 토큰 과금 없음.

주제를 받아서 진행자 → 각 부서 초기 의견 → 부서 간 토론 → 최종 결과물
순서로 Claude 를 여러 번 호출하고, 그 과정을 이벤트 스트림으로 흘려보낸다.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncIterator
from dataclasses import dataclass

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    query,
)
from claude_agent_sdk.types import StreamEvent

from .agents import DEPARTMENTS, FACILITATOR, Department

# 구독으로 쓰는 모델 별칭. Max 는 "opus" 도 가능, Pro 는 "sonnet" 권장.
MODEL = os.environ.get("MODEL", "sonnet")

# 각 에이전트를 깨끗한 빈 폴더에서 실행해 프로젝트 파일 컨텍스트가 섞이지 않게 한다.
_NEUTRAL_CWD = tempfile.mkdtemp(prefix="ai-dept-meeting-")

# 부서 AI 가 파일/셸 같은 도구를 쓰지 못하게 막는다(순수 텍스트 회의만).
_NO_TOOLS = [
    "Bash", "Read", "Write", "Edit", "Glob", "Grep",
    "WebFetch", "WebSearch", "Task", "NotebookEdit", "TodoWrite",
]


@dataclass
class Turn:
    """회의록에 쌓이는 한 명의 발언."""

    speaker: str
    text: str


def _transcript(turns: list[Turn]) -> str:
    if not turns:
        return "(아직 발언 없음)"
    return "\n\n".join(f"[{t.speaker}]\n{t.text}" for t in turns)


def _extract_delta(event: StreamEvent) -> str | None:
    """StreamEvent 에서 스트리밍 텍스트 조각을 최대한 견고하게 뽑아낸다.

    SDK 버전에 따라 event 모양이 조금씩 다를 수 있어 두 형태를 모두 처리한다.
    """
    raw = getattr(event, "event", None)
    if isinstance(raw, dict):
        if raw.get("type") == "content_block_delta":
            delta = raw.get("delta") or {}
            if delta.get("type") == "text_delta":
                return delta.get("text")
        return None
    # 단순화된 형태(.delta 가 문자열)인 경우
    d = getattr(event, "delta", None)
    return d if isinstance(d, str) else None


async def _stream_agent(dept: Department, instruction: str) -> AsyncIterator[str]:
    """한 에이전트를 Agent SDK 로 스트리밍 호출하고 텍스트 조각을 내보낸다."""
    system = (
        f"{dept.persona}\n\n"
        "발언은 한국어로, 핵심만 간결하게 한다. "
        "장황한 서론 없이 바로 요점부터 말한다. "
        "다른 부서가 이해할 수 있게 명확한 문장으로 쓴다. "
        "너는 회의 참석자이므로 파일을 만들거나 도구를 쓰지 말고, 의견만 말로 표현한다."
    )
    options = ClaudeAgentOptions(
        system_prompt=system,       # 평범한 문자열 → Claude Code 프리셋/CLAUDE.md 미로딩
        model=MODEL,
        max_turns=1,                # 한 번 발언하고 종료
        include_partial_messages=True,  # 토큰 단위 스트리밍
        setting_sources=[],         # 로컬 settings 무시
        allowed_tools=[],
        disallowed_tools=_NO_TOOLS,
        cwd=_NEUTRAL_CWD,
    )

    got_delta = False
    fallback: list[str] = []
    async for message in query(prompt=instruction, options=options):
        if isinstance(message, StreamEvent):
            text = _extract_delta(message)
            if text:
                got_delta = True
                yield text
        elif isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    fallback.append(block.text)

    # 스트리밍 조각을 못 받았으면 완성된 메시지 텍스트로 대체.
    if not got_delta and fallback:
        yield "".join(fallback)


async def _run_agent(
    dept: Department,
    role: str,
    instruction: str,
    turns: list[Turn],
) -> AsyncIterator[dict]:
    """에이전트 하나를 스트리밍 실행하며 이벤트를 yield 하고 회의록에 기록한다."""
    yield {
        "type": "agent_start",
        "speaker": dept.name,
        "icon": dept.icon,
        "role": role,
    }
    collected: list[str] = []
    async for text in _stream_agent(dept, instruction):
        collected.append(text)
        yield {"type": "token", "text": text}
    turns.append(Turn(speaker=dept.name, text="".join(collected).strip()))
    yield {"type": "agent_end"}


async def run_meeting(topic: str) -> AsyncIterator[dict]:
    """회의를 진행하며 이벤트(dict)를 yield 한다.

    이벤트 종류:
      {"type": "phase", "name": ...}                         단계 시작
      {"type": "agent_start", "speaker","icon","role": ...}  발언자 시작
      {"type": "token", "text": ...}                         스트리밍 텍스트 조각
      {"type": "agent_end"}                                  발언자 종료
      {"type": "done"}                                       회의 종료
      {"type": "error", "message": ...}                      오류
    """
    turns: list[Turn] = []

    try:
        # ── 1단계: 진행자가 회의를 연다 ───────────────────────────
        yield {"type": "phase", "name": "회의 개회 · 안건 정리"}
        opening = (
            f"오늘 회의 주제는 다음과 같다:\n\n\"{topic}\"\n\n"
            "진행자로서 이 주제를 팀에게 소개하고, 각 부서가 무엇을 검토해야 하는지 "
            "2~4개의 핵심 논점으로 정리해 회의를 열어라."
        )
        async for ev in _run_agent(FACILITATOR, "개회 · 안건 제시", opening, turns):
            yield ev

        # ── 2단계: 각 부서 초기 의견 ─────────────────────────────
        yield {"type": "phase", "name": "부서별 초기 의견"}
        for dept in DEPARTMENTS:
            instruction = (
                f"회의 주제: \"{topic}\"\n\n"
                f"지금까지의 회의 내용:\n{_transcript(turns)}\n\n"
                f"{dept.name}의 관점에서 이 주제에 대한 초기 의견을 제시하라. "
                "기회, 우려, 그리고 이 주제가 성공하려면 반드시 챙겨야 할 점을 담아라."
            )
            async for ev in _run_agent(dept, "초기 의견", instruction, turns):
                yield ev

        # ── 3단계: 부서 간 토론 ─────────────────────────────────
        yield {"type": "phase", "name": "부서 간 토론"}
        for dept in DEPARTMENTS:
            instruction = (
                f"회의 주제: \"{topic}\"\n\n"
                f"지금까지의 회의 내용(다른 부서 의견 포함):\n{_transcript(turns)}\n\n"
                f"{dept.name}으로서 다른 부서의 의견에 반응하라. "
                "동의하는 점, 반박하거나 조율이 필요한 점, 그리고 부서 간 협업이 필요한 "
                "구체적인 지점을 짚어라. 반복하지 말고 새로운 관점만 더하라."
            )
            async for ev in _run_agent(dept, "토론", instruction, turns):
                yield ev

        # ── 4단계: 진행자가 최종 결과물 작성 ─────────────────────
        yield {"type": "phase", "name": "결론 · 최종 결과물"}
        final = (
            f"회의 주제: \"{topic}\"\n\n"
            f"전체 회의 내용:\n{_transcript(turns)}\n\n"
            "진행자로서 이 회의를 종합해 실행 가능한 최종 결과물을 작성하라. "
            "마크다운으로 다음 구조를 따르라:\n"
            "## 📌 핵심 결론\n"
            "## ✅ 실행 계획 (담당 부서와 함께 단계별로)\n"
            "## ⚠️ 주요 리스크와 대응\n"
            "## 📊 성공 지표\n"
            "각 부서 의견이 결과물에 실제로 반영되게 하라."
        )
        async for ev in _run_agent(FACILITATOR, "최종 결과물", final, turns):
            yield ev

        yield {"type": "done"}

    except Exception as exc:  # noqa: BLE001 - 프런트에 오류를 그대로 전달
        yield {"type": "error", "message": f"{type(exc).__name__}: {exc}"}
