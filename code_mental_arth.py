import sys
import random
import re
import os
import json
from collections import OrderedDict

MISTAKE_FILE = "math_train_note.json"


def parse_range_spec(spec):
    """Parse individual range specification component"""
    if '~' in spec:
        parts = spec.split('~', 1)
        try:
            start = int(parts[0])
            end = int(parts[1])
            return ('range', (min(start, end), max(start, end)))
        except ValueError:
            return None
    else:
        try:
            return ('value', int(spec))
        except ValueError:
            return None


def validate_spec(spec_str):
    """Validate and parse a full specification string"""
    spec_str = spec_str.strip('()')
    components = []
    for part in spec_str.split(','):
        parsed = parse_range_spec(part.strip())
        if not parsed:
            return None
        components.append(parsed)
    return components


def spec_contains_non1(components):
    """Check if specification contains possible non-1 values"""
    for comp in components:
        type_, data = comp
        if type_ == 'value':
            if data != 1:
                return True
        else:
            start, end = data
            if not (start == 1 and end == 1):
                return True
    return False


def generate_from_spec(components):
    """Generate number from specification with 1 exclusion"""
    while True:
        comp_type, comp_data = random.choice(components)
        if comp_type == 'value':
            num = comp_data
        else:
            start, end = comp_data
            num = random.randint(start, end)
        if num != 1:
            return num


def validate_args():
    """Validate command line arguments"""
    if len(sys.argv) != 3 and not (len(sys.argv) == 2 and sys.argv[1].lower() == 'c'):
        print("Usage: python math_train.py '<multiplicand_spec>' '<multiplier_spec>'")
        print("Example 1: python math_train.py '(0~999,123)' '(5,6,7,8,9)'")
        print("Example 2: python math_train.py '(10~20)' '(100~200)'")
        print("Review mode: python math_train.py c")
        sys.exit(1)

    if len(sys.argv) == 2 and sys.argv[1].lower() == 'c':
        return None, None

    spec1 = validate_spec(sys.argv[1])
    spec2 = validate_spec(sys.argv[2])

    if not spec1 or not spec2:
        print("Error: Invalid specification format")
        print("Valid formats: '(start~end)' or '(num1,num2,...)' or combinations")
        sys.exit(1)

    if not spec_contains_non1(spec1):
        print("Error: First operand specification must contain non-1 values")
        sys.exit(1)

    if not spec_contains_non1(spec2):
        print("Error: Second operand specification must contain non-1 values")
        sys.exit(1)

    return spec1, spec2


def parse_input(user_input):
    """Parse user input with reverse format support"""
    if user_input.startswith('r'):
        cleaned = re.sub(r'\D', '', user_input[1:])
        return int(cleaned[::-1]) if cleaned else 0
    else:
        cleaned = re.sub(r'\D', '', user_input)
        return int(cleaned) if cleaned else 0


def load_mistakes():
    """Load mistakes from JSON file with validation"""
    if not os.path.exists(MISTAKE_FILE):
        return []

    try:
        with open(MISTAKE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        validated = []
        for entry in data:
            try:
                validated.append((
                    int(entry['num1']),
                    int(entry['num2']),
                    int(entry['answer'])
                ))
            except (KeyError, ValueError):
                continue
        return validated

    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_mistakes(mistakes):
    """Save mistakes to JSON file with deduplication"""
    seen = OrderedDict()
    for m in mistakes:
        key = f"{m[0]}_{m[1]}_{m[2]}"
        if key not in seen:
            seen[key] = {
                'num1': m[0],
                'num2': m[1],
                'answer': m[2]
            }

    temp_file = MISTAKE_FILE + ".tmp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(list(seen.values()), f, indent=2, ensure_ascii=False)

    if os.path.exists(temp_file):
        os.replace(temp_file, MISTAKE_FILE)


def review_mode():
    """Handle mistake review sessions"""
    mistakes = load_mistakes()
    if not mistakes:
        print("No mistakes to review!")
        return

    print(f"\n▶ Entering mistake review mode ({len(mistakes)} questions available)")
    session_mistakes = random.sample(mistakes, min(10, len(mistakes)))
    remaining = [m for m in mistakes if m not in session_mistakes]
    correct_count = 0

    for i, (num1, num2, answer) in enumerate(session_mistakes, 1):
        print(f"\nReview Question {i}: {num1} × {num2} = ?")
        user_input = input("Answer: ")
        user_answer = parse_input(user_input)

        if user_answer == answer:
            print("✅ Correct! Removing from mistake list.")
            correct_count += 1
        else:
            print(f"❌ Wrong. Correct answer: {answer:_}")
            remaining.append((num1, num2, answer))

    save_mistakes(remaining)
    print(f"\n—— Review Summary ——")
    print(f"Correct answers: {correct_count}/{len(session_mistakes)}")
    print(f"Remaining mistakes: {len(remaining)}")


def normal_mode(spec1, spec2):
    """Handle normal practice sessions"""
    correct_count = 0
    round_num = 1
    new_mistakes = []

    print("\n▶ Starting normal practice mode")
    print("First operand spec:", sys.argv[1])
    print("Second operand spec:", sys.argv[2] if len(sys.argv) > 2 else '')
    print("Tip: Use reverse format starting with 'r' (e.g. r12.34 → 4321)")

    while True:
        for q in range(1, 11):
            num1 = generate_from_spec(spec1)
            num2 = generate_from_spec(spec2)
            answer = num1 * num2

            print(f"\nRound {round_num}-Question {q}: {num1} × {num2} = ?")
            user_input = input("Answer: ")
            user_answer = parse_input(user_input)

            if user_answer == answer:
                print("✅ Correct!")
                correct_count += 1
            else:
                print(f"❌ Wrong. Correct answer: {answer:_}")
                new_mistakes.append((num1, num2, answer))

        if new_mistakes:
            existing = load_mistakes()
            save_mistakes(existing + new_mistakes)
            new_mistakes.clear()

        print(f"\n—— Round {round_num} Summary ——")
        print(f"Accuracy: {correct_count}/10 ({correct_count * 10}%)")
        correct_count = 0

        if input("\nContinue practice? (Y/N): ").upper() != 'Y':
            print("\n✧ Training session ended. Goodbye!")
            break

        round_num += 1


def main():
    if len(sys.argv) == 2 and sys.argv[1].lower() == 'c':
        review_mode()
    else:
        spec1, spec2 = validate_args()
        if spec1 and spec2:
            normal_mode(spec1, spec2)


if __name__ == "__main__":
    main()