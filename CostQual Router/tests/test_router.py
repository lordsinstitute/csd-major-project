from router import route


def test_simple_question_routes_small():
    assert route("What is the capital of France?") == "small"


def test_define_question_routes_small():
    assert route("Define gravity.") == "small"


def test_reasoning_keyword_routes_large():
    assert route("Explain why the sky is blue.") == "large"


def test_long_query_routes_large():
    long_query = "Tell me everything you know about the history of the internet " * 3
    assert route(long_query) == "large"


def test_middling_query_routes_medium():
    assert route("Tell me about the history of computers.") == "medium"
