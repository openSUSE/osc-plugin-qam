from oscqam.fields import InvalidFieldsError, levenshtein


def test_insertion_levenshtein():
    assert 1 == levenshtein("a", "ab")


def test_deletion_levenshtein():
    assert 1 == levenshtein("ab", "a")


def test_modification_levenshtein():
    assert 1 == levenshtein("ab", "ac")


def test_equal_levenshtein():
    assert 0 == levenshtein("a", "a")


def test_mismatched_casing():
    assert 2 == levenshtein("RequestReviewId", "Requestreviewid")


def test_long_mismatch():
    assert 12 == levenshtein("RequestReviewId", "Assigned Roles")


def test_suggestions():
    fields = ["ReviewRequest"]
    error = InvalidFieldsError(fields)
    suggestions = error._get_suggestions(fields)
    assert suggestions == set(["ReviewRequestID"])
    fields = ["ReviewRequest", "Bugz"]
    error = InvalidFieldsError(fields)
    suggestions = error._get_suggestions(fields)
    assert suggestions == set(["ReviewRequestID", "Bugs"])
