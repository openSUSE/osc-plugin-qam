from unittest import TestCase

from oscqam.fields import levenshtein, InvalidFieldsError


class AlgorithmTests(TestCase):
    def test_insertion_levenshtein(self):
        self.assertEqual(1, levenshtein("a", "ab"))

    def test_deletion_levenshtein(self):
        self.assertEqual(1, levenshtein("ab", "a"))

    def test_modification_levenshtein(self):
        self.assertEqual(1, levenshtein("ab", "ac"))

    def test_equal_levenshtein(self):
        self.assertEqual(0, levenshtein("a", "a"))

    def test_mismatched_casing(self):
        self.assertEqual(2, levenshtein("RequestReviewId",
                                        "Requestreviewid"))

    def test_long_mismatch(self):
        self.assertEqual(12, levenshtein("RequestReviewId",
                                         "Assigned Roles"))

    def test_suggestions(self):
        error = InvalidFieldsError(['ReviewRequest'])
        suggestions = error._get_suggestions()
        self.assertEqual(suggestions, set(["ReviewRequestID"]))
        error = InvalidFieldsError(['ReviewRequest', 'Bugz'])
        suggestions = error._get_suggestions()
        self.assertEqual(suggestions, set(["ReviewRequestID", "Bugs"]))
