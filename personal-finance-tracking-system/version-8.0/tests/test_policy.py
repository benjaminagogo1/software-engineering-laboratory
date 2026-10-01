"""
The username and password rules.

These are asserted against the message as well as the outcome wherever the
message is the point. `password_problem` exists in the shape it does — returning
a reason rather than a boolean — precisely so the refusal can say what is wrong,
and a test that only checked `is not None` would let that sentence rot into
"invalid" without failing.
"""

import pytest

from app.auth import policy
from app.auth.policy import WeakCredentials


# Long enough to clear the length rule, so tests about the *other* rules are not
# accidentally testing this one.
ACCEPTABLE = "correct horse battery"


class TestPasswordProblem:
    def test_a_reasonable_password_is_accepted(self):
        assert policy.password_problem("ben", ACCEPTABLE) is None

    def test_the_exact_minimum_is_accepted(self):
        password = "a" * policy.MIN_LENGTH

        assert policy.password_problem("ben", password) is None

    def test_one_character_under_the_minimum_is_refused(self):
        password = "a" * (policy.MIN_LENGTH - 1)

        assert policy.password_problem("ben", password) == (
            f"Password must be at least {policy.MIN_LENGTH} characters"
        )

    def test_the_exact_maximum_is_accepted(self):
        password = "a" * policy.MAX_LENGTH

        assert policy.password_problem("ben", password) is None

    def test_one_character_over_the_maximum_is_refused(self):
        # The cap is not about strength — it is that argon2 will happily hash a
        # megabyte, so an uncapped field lets one request buy unbounded work.
        password = "a" * (policy.MAX_LENGTH + 1)

        assert policy.password_problem("ben", password) == (
            f"Password must be at most {policy.MAX_LENGTH} characters"
        )

    @pytest.mark.parametrize("password", ["", "   ", "\t\n"])
    def test_an_empty_or_blank_password_is_refused(self, password):
        assert policy.password_problem("ben", password) == "Password must not be empty"

    def test_a_blank_password_is_refused_before_the_length_rule(self):
        # Ordering, not just outcome: "must not be empty" is the useful sentence
        # for someone who typed a space, and they would not get it if the length
        # rule ran first.
        assert policy.password_problem("ben", " ") == "Password must not be empty"

    def test_a_known_common_password_is_refused(self):
        assert policy.password_problem("ben", "password1234") == "Password is too common"

    def test_common_is_case_insensitive(self):
        assert policy.password_problem("ben", "PassWord1234") == "Password is too common"

    def test_a_password_containing_the_username_is_refused(self):
        assert policy.password_problem(
            "benjamin", "benjamin-is-my-password"
        ) == "Password must not contain your username"

    def test_the_username_check_is_case_insensitive(self):
        assert policy.password_problem(
            "Benjamin", "benjamin-is-my-password"
        ) == "Password must not contain your username"

    def test_a_two_character_username_is_not_looked_for_inside_the_password(self):
        # "jo" appears inside ordinary words. Flagging it would refuse an honest
        # password for a coincidence, so the check is skipped below the minimum
        # username length.
        assert policy.password_problem("jo", "majority rules ok") is None

    def test_the_length_rule_is_measured_on_the_raw_string(self):
        # Leading and trailing spaces are valid password characters (NIST is
        # explicit) and are hashed as given. Stripping before measuring would
        # accept this 7-character password.
        assert policy.password_problem("ben", " short ") == (
            f"Password must be at least {policy.MIN_LENGTH} characters"
        )

    def test_spaces_inside_a_password_count_towards_its_length(self):
        # The other half of the same rule: the spaces are real characters, so
        # they buy length like anything else.
        assert policy.password_problem("ben", "a b c d e f g h") is None

    def test_a_non_string_password_is_refused_rather_than_crashing(self):
        # The service is called from a Pydantic route today, so this cannot
        # arrive — but the CLI and any future caller reach the same method, and
        # an AttributeError on `None` would be a 500 rather than a refusal.
        assert policy.password_problem("ben", None) == "Password must not be empty"


class TestUsernameProblem:
    @pytest.mark.parametrize("username", ["ben", "benjamin", "a" * policy.MAX_USERNAME_LENGTH])
    def test_an_acceptable_username_is_accepted(self, username):
        assert policy.username_problem(username) is None

    def test_the_exact_minimum_is_accepted(self):
        assert policy.username_problem("a" * policy.MIN_USERNAME_LENGTH) is None

    def test_one_character_under_the_minimum_is_refused(self):
        assert policy.username_problem("ab") == (
            f"Username must be at least {policy.MIN_USERNAME_LENGTH} characters"
        )

    def test_the_exact_maximum_is_accepted(self):
        assert policy.username_problem("a" * policy.MAX_USERNAME_LENGTH) is None

    def test_one_character_over_the_maximum_is_refused(self):
        assert policy.username_problem("a" * (policy.MAX_USERNAME_LENGTH + 1)) == (
            f"Username must be at most {policy.MAX_USERNAME_LENGTH} characters"
        )

    @pytest.mark.parametrize("username", ["", "   "])
    def test_an_empty_username_is_refused(self, username):
        assert policy.username_problem(username) == "Username must not be empty"

    def test_a_padded_username_is_accepted_for_what_it_is(self):
        # Registration trims before storing, and the length is judged on the
        # trimmed value — otherwise "  ben  " would be refused while "ben" is
        # fine, despite the two being the same account.
        assert policy.username_problem("  ben  ") is None

    @pytest.mark.parametrize("username", ["ben jamin", "ben\tjamin", "ben\njamin"])
    def test_interior_whitespace_is_refused(self, username):
        # Trimming removes the ends only, so interior whitespace would be stored
        # as part of the name.
        assert policy.username_problem(username) == "Username must not contain spaces"

    def test_a_non_string_username_is_refused_rather_than_crashing(self):
        assert policy.username_problem(None) == "Username must not be empty"


class TestCheck:
    def test_a_good_pair_does_not_raise(self):
        policy.check("benjamin", ACCEPTABLE)

    def test_a_bad_pair_raises_weak_credentials(self):
        with pytest.raises(WeakCredentials):
            policy.check("benjamin", "short")

    def test_weak_credentials_is_a_value_error(self):
        # A caller that does not catch it specifically still fails loudly at the
        # point of the bad argument, rather than proceeding with a username that
        # was rejected.
        assert issubclass(WeakCredentials, ValueError)

    def test_the_username_is_judged_first(self):
        # Two things wrong; the person should hear about the one they got to
        # first rather than about a password they have not finished choosing.
        with pytest.raises(WeakCredentials, match="Username"):
            policy.check("ab", "short")

    def test_the_message_is_the_reason_and_not_the_type(self):
        # The API turns this straight into a 400 body, so it has to be a
        # sentence for a person.
        with pytest.raises(WeakCredentials) as refused:
            policy.check("benjamin", "short")

        assert str(refused.value) == (
            f"Password must be at least {policy.MIN_LENGTH} characters"
        )


class TestThePolicyItself:
    def test_the_minimum_is_above_the_nist_floor(self):
        # NIST's floor is 8. This is a deliberate choice to sit above it, and
        # pinning it stops a future edit quietly lowering it to the floor.
        assert policy.MIN_LENGTH > 8

    def test_the_maximum_is_high_enough_not_to_bite_a_password_manager(self):
        # A cap that a generated password trips is a cap that pushes people
        # towards shorter ones, which is the opposite of the point.
        assert policy.MAX_LENGTH >= 64

    def test_every_common_password_clears_the_length_rule(self):
        # The list is a shape check, not a substitute for the length rule: an
        # entry shorter than the minimum would be refused by length first and
        # the "too common" sentence would never be seen.
        too_short = {
            word for word in policy.COMMON_PASSWORDS if len(word) < policy.MIN_LENGTH
        }

        assert too_short == set()
