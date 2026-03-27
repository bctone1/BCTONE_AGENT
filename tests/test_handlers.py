import pytest
from unittest.mock import patch, MagicMock


def _make_event(text, user="U123", channel="C456", ts="1234567890.123", thread_ts=None):
    event = {
        "text": text,
        "user": user,
        "channel": channel,
        "ts": ts,
    }
    if thread_ts:
        event["thread_ts"] = thread_ts
    return event


def _make_say():
    return MagicMock()


def test_handle_mention_calls_chat():
    event = _make_event("<@BOT_ID> FastAPI에서 의존성 주입 어떻게 해?")
    say = _make_say()

    with patch("bctone.handlers.mention.chat", return_value="FastAPI의 Depends를 사용하시면 됩니다.") as mock_chat:
        with patch("bctone.handlers.mention.get_conversation_history", return_value=[]):
            with patch("bctone.handlers.mention.save_conversation"):
                from bctone.handlers.mention import handle_mention
                handle_mention(event, say)

    mock_chat.assert_called_once()
    say.assert_called_once()
    assert "Depends" in say.call_args[1].get("text", say.call_args[0][0] if say.call_args[0] else "")


def test_handle_mention_github_all():
    event = _make_event("<@BOT_ID> 깃허브 변경사항 알려줘")
    say = _make_say()

    with patch("bctone.handlers.mention.summarize_github", return_value="요약 결과") as mock_gh:
        with patch("bctone.handlers.mention.save_conversation"):
            from bctone.handlers.mention import handle_mention
            handle_mention(event, say)

    assert mock_gh.call_count == 3  # backend, frontend, planning
    say.assert_called_once()
    assert "백엔드" in say.call_args.kwargs["text"]


def test_handle_mention_github_backend():
    event = _make_event("<@BOT_ID> 백엔드 깃허브 커밋 알려줘")
    say = _make_say()

    with patch("bctone.handlers.mention.summarize_github", return_value="백엔드 요약") as mock_gh:
        with patch("bctone.handlers.mention.save_conversation"):
            from bctone.handlers.mention import handle_mention
            handle_mention(event, say)

    mock_gh.assert_called_once_with("backend")
    say.assert_called_once()


def test_handle_mention_team_summary():
    event = _make_event("<@BOT_ID> 팀 진행상황 요약해줘")
    say = _make_say()

    with patch("bctone.handlers.mention.summarize_team_progress", return_value="팀 요약 결과") as mock_summary:
        with patch("bctone.handlers.mention.save_conversation"):
            from bctone.handlers.mention import handle_mention
            handle_mention(event, say)

    mock_summary.assert_called_once()
    say.assert_called_once()
    assert "팀 요약" in say.call_args.kwargs["text"]


def test_handle_mention_saves_conversation():
    event = _make_event("<@BOT_ID> 안녕하세요")
    say = _make_say()

    with patch("bctone.handlers.mention.chat", return_value="안녕하세요, 무엇을 도와드릴까요?"):
        with patch("bctone.handlers.mention.get_conversation_history", return_value=[]):
            with patch("bctone.handlers.mention.save_conversation") as mock_save:
                from bctone.handlers.mention import handle_mention
                handle_mention(event, say)

    assert mock_save.call_count == 2  # user message + assistant response


def test_handle_message_saves_progress():
    event = _make_event("로그인 API 구현 완료했습니다")

    with patch("bctone.handlers.message.classify_message", return_value="PROGRESS"):
        with patch("bctone.handlers.message.save_memory") as mock_save:
            with patch("bctone.handlers.message.llm_summarize", return_value="로그인 API 완료"):
                from bctone.handlers.message import handle_message
                handle_message(event)

    mock_save.assert_called_once()
    call_kwargs = mock_save.call_args[1]
    assert call_kwargs["category"] == "progress"
    assert call_kwargs["expiry_days"] == 14


def test_handle_message_saves_decision():
    event = _make_event("JWT 인증 방식으로 확정합니다")

    with patch("bctone.handlers.message.classify_message", return_value="DECISION"):
        with patch("bctone.handlers.message.save_memory") as mock_save:
            with patch("bctone.handlers.message.llm_summarize", return_value="JWT 인증 확정"):
                from bctone.handlers.message import handle_message
                handle_message(event)

    call_kwargs = mock_save.call_args[1]
    assert call_kwargs["category"] == "decision"
    assert call_kwargs.get("expiry_days") is None  # decisions don't expire


def test_handle_message_ignores_none():
    event = _make_event("점심 뭐 먹을까요?")

    with patch("bctone.handlers.message.classify_message", return_value="NONE"):
        with patch("bctone.handlers.message.save_memory") as mock_save:
            from bctone.handlers.message import handle_message
            handle_message(event)

    mock_save.assert_not_called()


def test_handle_message_ignores_bot():
    event = _make_event("봇이 보낸 메시지")
    event["bot_id"] = "B123"

    with patch("bctone.handlers.message.classify_message") as mock_classify:
        from bctone.handlers.message import handle_message
        handle_message(event)

    mock_classify.assert_not_called()


def test_handle_command_summary():
    ack = MagicMock()
    respond = MagicMock()
    command = {"text": "요약", "user_id": "U123", "channel_id": "C456"}

    with patch("bctone.handlers.command.summarize_team_progress", return_value="팀 진행 요약 내용"):
        from bctone.handlers.command import handle_command
        handle_command(ack, respond, command)

    ack.assert_called_once()
    respond.assert_called_once()
    call_text = respond.call_args[1].get("text") or (respond.call_args[0][0] if respond.call_args[0] else "")
    assert "팀 진행 요약" in call_text


def test_handle_command_github():
    ack = MagicMock()
    respond = MagicMock()
    command = {"text": "github backend", "user_id": "U123", "channel_id": "C456"}

    with patch("bctone.handlers.command.summarize_github", return_value="백엔드 GitHub 요약"):
        from bctone.handlers.command import handle_command
        handle_command(ack, respond, command)

    ack.assert_called_once()
    respond.assert_called_once()


def test_handle_message_saves_todo():
    event = _make_event("온보딩 플로우 와이어프레임 금요일까지 완성해야 함")

    with patch("bctone.handlers.message.classify_message", return_value="TODO"):
        with patch("bctone.handlers.message.parse_todo", return_value={
            "content": "온보딩 플로우 와이어프레임 완성",
            "assignee": None,
            "due_date": "2026-03-31",
        }):
            with patch("bctone.handlers.message.save_memory") as mock_save:
                from bctone.handlers.message import handle_message
                handle_message(event)

    call_kwargs = mock_save.call_args[1]
    assert call_kwargs["category"] == "todo"
    assert call_kwargs["due_date"] == "2026-03-31"
    assert call_kwargs["assignee"] == "U123"  # defaults to message sender


def test_handle_message_completes_todo():
    event = _make_event("완료 #5")

    with patch("bctone.handlers.message.complete_todo") as mock_complete:
        from bctone.handlers.message import handle_message
        handle_message(event)

    mock_complete.assert_called_once_with(5)


def test_handle_command_todo_list():
    ack = MagicMock()
    respond = MagicMock()
    command = {"text": "todo", "user_id": "U123", "channel_id": "C456"}

    with patch("bctone.handlers.command.get_todos", return_value=[]):
        from bctone.handlers.command import handle_command
        handle_command(ack, respond, command)

    ack.assert_called_once()
    respond.assert_called_once()
    response_text = respond.call_args[1].get("text") or (respond.call_args[0][0] if respond.call_args[0] else "")
    assert "미완료" in response_text


def test_handle_command_todo_complete():
    ack = MagicMock()
    respond = MagicMock()
    command = {"text": "todo 완료 #3", "user_id": "U123", "channel_id": "C456"}

    with patch("bctone.handlers.command.complete_todo", return_value=True):
        from bctone.handlers.command import handle_command
        handle_command(ack, respond, command)

    ack.assert_called_once()
    respond.assert_called_once()
    response_text = respond.call_args[1].get("text") or (respond.call_args[0][0] if respond.call_args[0] else "")
    assert "#3" in response_text
    assert "완료" in response_text


def test_handle_command_help():
    ack = MagicMock()
    respond = MagicMock()
    command = {"text": "", "user_id": "U123", "channel_id": "C456"}

    from bctone.handlers.command import handle_command
    handle_command(ack, respond, command)

    ack.assert_called_once()
    respond.assert_called_once()
    response_text = respond.call_args[1].get("text") or (respond.call_args[0][0] if respond.call_args[0] else "")
    assert "사용 가능한 명령" in response_text
