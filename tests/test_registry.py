from agent.tools.registry import get_tool, list_schemas


def test_echo_tool_is_registered():
    tool = get_tool("echo")
    assert tool is not None
    assert tool.run(text="hi") == "hi"


def test_unknown_tool_returns_none():
    assert get_tool("does-not-exist") is None


def test_list_schemas_includes_echo():
    names = [schema["name"] for schema in list_schemas()]
    assert "echo" in names
