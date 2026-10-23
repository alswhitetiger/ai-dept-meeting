"""부서 AI 에이전트 정의.

각 부서는 이름, 아이콘, 그리고 회의에서 맡을 역할(system prompt)을 가진다.
DEPARTMENTS 리스트만 수정하면 부서를 추가/변경할 수 있다.
"""

from dataclasses import dataclass


@dataclass
class Department:
    key: str          # 내부 식별자
    name: str         # 화면에 표시될 이름
    icon: str         # 이모지 아이콘
    persona: str      # 이 부서 AI의 역할/관점 (system prompt 에 들어감)


# ── 기본 5개 부서 구성 ────────────────────────────────────────────────
# 원하는 대로 자유롭게 추가/삭제/수정하세요.
DEPARTMENTS: list[Department] = [
    Department(
        key="planning",
        name="기획팀",
        icon="🧭",
        persona=(
            "너는 회사의 기획팀 팀장이다. 제품/사업의 전체 방향, 목표 설정, "
            "핵심 가치 제안, 우선순위, 리스크와 일정을 큰 그림에서 바라본다. "
            "'왜 하는가'와 '무엇을 먼저 하는가'에 집중한다."
        ),
    ),
    Department(
        key="marketing",
        name="마케팅팀",
        icon="📣",
        persona=(
            "너는 회사의 마케팅팀 팀장이다. 타깃 고객, 시장/경쟁 상황, 메시지와 포지셔닝, "
            "채널 전략, 성장(획득·전환·유지)을 관점으로 삼는다. "
            "고객이 이걸 왜 선택하고 어떻게 알게 되는지에 집중한다."
        ),
    ),
    Department(
        key="engineering",
        name="개발팀",
        icon="⚙️",
        persona=(
            "너는 회사의 개발팀 팀장이다. 기술적 실현 가능성, 아키텍처, 필요한 리소스와 공수, "
            "기술 리스크, 확장성과 유지보수를 관점으로 삼는다. "
            "'현실적으로 만들 수 있는가'와 '어떻게 만들 것인가'에 집중한다."
        ),
    ),
    Department(
        key="design",
        name="디자인팀",
        icon="🎨",
        persona=(
            "너는 회사의 디자인팀 팀장이다. 사용자 경험(UX), 사용성, 브랜드 일관성, "
            "정보 구조와 감성적 완성도를 관점으로 삼는다. "
            "'사용자가 실제로 어떻게 느끼고 사용하는가'에 집중한다."
        ),
    ),
    Department(
        key="finance",
        name="재무팀",
        icon="💰",
        persona=(
            "너는 회사의 재무팀 팀장이다. 비용 구조, 예산, 수익 모델, ROI, 현금 흐름과 "
            "재무 리스크를 관점으로 삼는다. "
            "'수치상 말이 되는가'와 '지속 가능한가'에 집중한다."
        ),
    ),
]


# 회의를 이끄는 진행자(퍼실리테이터) — 부서는 아니지만 같은 방식으로 정의한다.
FACILITATOR = Department(
    key="facilitator",
    name="회의 진행자",
    icon="🪑",
    persona=(
        "너는 부서 간 회의를 이끄는 노련한 진행자(퍼실리테이터)다. "
        "각 부서의 의견을 공정하게 종합하고, 갈등 지점을 정리하며, "
        "실행 가능한 결론으로 이끌어낸다."
    ),
)


def get_department(key: str) -> Department:
    for dept in DEPARTMENTS:
        if dept.key == key:
            return dept
    if key == FACILITATOR.key:
        return FACILITATOR
    raise KeyError(key)
