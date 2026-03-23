def execution_accuracy(expected: str, actual: str) -> bool:
    """
    Checks whether expected SQL fragments appear in generated SQL.
    """
    if not actual:
        return False

    return expected.lower() in actual.lower()
