from app.config import Settings
import app.decisions as decisions

QUESTIONS = [
    {"type": "predicate", "name": "is_refund", "instructions": "Is the customer asking for a refund?"},
]


class FakeDecisionsResponse:
    def model_dump(self, **kwargs: object) -> dict[str, object]:
        assert kwargs == {"exclude_none": True}
        return {
            "model": "gpt-6-luna",
            "answers": [{"type": "predicate", "name": "is_refund", "probability": 1.0}],
        }


class FakeDecisions:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] | None = None

    def create(self, **kwargs: object) -> FakeDecisionsResponse:
        self.kwargs = kwargs
        return FakeDecisionsResponse()


class FakeOpenAI:
    instances: list["FakeOpenAI"] = []

    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        self.decisions = FakeDecisions()
        self.instances.append(self)


def test_make_decisions_uses_decisions_model(monkeypatch) -> None:
    FakeOpenAI.instances.clear()
    monkeypatch.setattr(decisions.openai, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(
        decisions,
        "get_settings",
        lambda: Settings(
            openai_api_key="test-key",
            openai_base_url="https://litellm.example.com",
            openai_decisions_model="gpt-6-luna-openai",
        ),
    )

    result = decisions.make_decisions(text="My order arrived broken, refund please.", questions=QUESTIONS)

    assert result["answers"][0]["probability"] == 1.0
    assert FakeOpenAI.instances[0].kwargs == {
        "api_key": "test-key",
        "base_url": "https://litellm.example.com/",
    }
    assert FakeOpenAI.instances[0].decisions.kwargs == {
        "model": "gpt-6-luna-openai",
        "input": "My order arrived broken, refund please.",
        "questions": QUESTIONS,
    }
