from migrate_eval.prompts import initial


def test_initial_prompt_contains_java_code():
    java_code = """
    public static int add(int a, int b) {
        return a + b;
    }
    """

    prompt = initial(
        java_code=java_code,
        go_signature="func Add(a int, b int) int {",
    )

    assert "public static int add" in prompt
    assert "return a + b;" in prompt


def test_initial_prompt_contains_go_signature():
    prompt = initial(
        java_code="public static int add(int a, int b) { return a + b; }",
        go_signature="func Add(a int, b int) int {",
    )

    assert "func Add(a int, b int) int {" in prompt


def test_initial_prompt_instructs_code_only_output():
    prompt = initial(
        java_code="public static int add(int a, int b) { return a + b; }",
        go_signature="func Add(a int, b int) int {",
    )

    assert "Return only one Go code block." in prompt
    assert "Do not include tests." in prompt
    assert "Do not include a main function." in prompt


def test_initial_prompt_requires_package_main():
    prompt = initial(
        java_code="public static int add(int a, int b) { return a + b; }",
        go_signature="func Add(a int, b int) int {",
    )

    assert "Use package main." in prompt