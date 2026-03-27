import pytest
from unittest.mock import patch, MagicMock, AsyncMock


def test_classify_message_progress():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="PROGRESS")]
    mock_client.messages.create.return_value = mock_response

    with patch("bctone.services.llm.get_client", return_value=mock_client):
        from bctone.services.llm import classify_message
        result = classify_message("로그인 API 구현 완료했습니다")

    assert result == "PROGRESS"


def test_classify_message_none():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="NONE")]
    mock_client.messages.create.return_value = mock_response

    with patch("bctone.services.llm.get_client", return_value=mock_client):
        from bctone.services.llm import classify_message
        result = classify_message("점심 뭐 먹을까요?")

    assert result == "NONE"


def test_should_escalate_simple():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="SIMPLE")]
    mock_client.messages.create.return_value = mock_response

    with patch("bctone.services.llm.get_client", return_value=mock_client):
        from bctone.services.llm import should_escalate
        result = should_escalate("오늘 PR 몇 개 머지됐어?")

    assert result is False


def test_should_escalate_complex():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="COMPLEX")]
    mock_client.messages.create.return_value = mock_response

    with patch("bctone.services.llm.get_client", return_value=mock_client):
        from bctone.services.llm import should_escalate
        result = should_escalate("PR #42와 #43의 diff를 비교 분석해줘")

    assert result is True


def test_chat_uses_sonnet_by_default():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="답변입니다")]
    mock_client.messages.create.return_value = mock_response

    with patch("bctone.services.llm.get_client", return_value=mock_client):
        with patch("bctone.services.llm.should_escalate", return_value=False):
            from bctone.services.llm import chat
            result = chat("안녕하세요", [])

    call_kwargs = mock_client.messages.create.call_args_list[-1][1]
    assert "sonnet" in call_kwargs["model"]
    assert result == "답변입니다"


def test_chat_escalates_to_opus():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="상세 분석 결과")]
    mock_client.messages.create.return_value = mock_response

    with patch("bctone.services.llm.get_client", return_value=mock_client):
        with patch("bctone.services.llm.should_escalate", return_value=True):
            from bctone.services.llm import chat
            result = chat("아키텍처 전반을 분석해줘", [])

    call_kwargs = mock_client.messages.create.call_args_list[-1][1]
    assert "opus" in call_kwargs["model"]
