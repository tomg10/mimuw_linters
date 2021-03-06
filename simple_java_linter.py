from schema import LinterResponse, LinterRequest


def is_whitespace(ch: str):
    return ch == ' ' or ch == '\n' or ch == '\n'


def lint(request: LinterRequest) -> LinterResponse:
    program = request.code
    prev1 = ' '
    prev2 = ' '
    char_number = 0
    line_number = 1
    errors = []

    for ch in program:
        char_number += 1

        if prev1 == '=':
            if not is_whitespace(prev2):
                errors.append(f"Missing space around = at line {line_number}, column {char_number} - before symbol =!")

            if not is_whitespace(ch):
                errors.append(f"Missing space around = at line {line_number}, column {char_number} - after symbol =!")

        prev2 = prev1
        prev1 = ch

        if ch == '\n':
            line_number += 1
            char_number = 0

    if "class" not in program:
        errors.append("Missing class keyword in the program!")

    return LinterResponse(result='ok' if len(errors) == 0 else 'fail', errors=errors, test_logging=[])
