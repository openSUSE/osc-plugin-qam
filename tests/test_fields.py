from oscqam.fields import InvalidFieldsError, levenshtein


def test_insertion_levenshtein():
    assert levenshtein("a", "ab") == 1


def test_deletion_levenshtein():
    assert levenshtein("ab", "a") == 1


def test_modification_levenshtein():
    assert levenshtein("ab", "ac") == 1


def test_equal_levenshtein():
    assert levenshtein("a", "a") == 0


def test_mismatched_casing():
    assert levenshtein("RequestReviewId", "Requestreviewid") == 2


def test_long_mismatch():
    assert levenshtein("RequestReviewId", "Assigned Roles") == 12


def test_suggestions():
    fields = ["ReviewRequest"]
    error = InvalidFieldsError(fields)
    suggestions = error._get_suggestions(fields)
    assert suggestions == {"ReviewRequestID"}
    fields = ["ReviewRequest", "Bugz"]
    error = InvalidFieldsError(fields)
    suggestions = error._get_suggestions(fields)
    assert suggestions == {"ReviewRequestID", "Bugs"}
