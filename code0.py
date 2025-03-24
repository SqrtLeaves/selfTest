import random
import time
import json
from collections import deque

# 初始化数据结构
tables = {
    'alpha': [
        (-0.15, 1.13),
        (-0.05, 1.05),
        (0.05, 0.95),
        (0.15, 0.87),
        (0.25, 0.8),
        (0.35, 0.74),
        (0.45, 0.69),
        (0.55, 0.65),
        (0.65, 0.61),
        (0.75, 0.57),
        (0.85, 0.54),
        (0.95, 0.51)
    ],
    'R2': [
        (2, 1.41), (3, 1.74), (4, 2.00), (5, 2.24),
        (6, 2.45), (7, 2.65), (8, 2.83), (9, 3.00)
    ],
    'R3': [
        (2, 1.26), (3, 1.44), (4, 1.59), (5, 1.70),
        (6, 1.82), (7, 1.91), (8, 2.00), (9, 2.08)
    ],
    'R4': [
        (2, 1.19), (3, 1.32), (4, 1.41), (5, 1.50),
        (6, 1.57), (7, 1.63), (8, 1.68), (9, 1.73)
    ],
    'R5': [
        (2, 1.14), (3, 1.24), (4, 1.31), (5, 1.37),
        (6, 1.43), (7, 1.48), (8, 1.52), (9, 1.55)
    ]
}

# 错题记录队列（最大保存20条）
error_records = deque(maxlen=20)


def load_notes():
    """加载错题记录"""
    try:
        with open("note.json", "r") as f:
            records = json.load(f)
            error_records.extend(records)
    except (FileNotFoundError, json.JSONDecodeError):
        pass


def save_notes():
    """保存错题记录"""
    with open("note.json", "w") as f:
        json.dump(list(error_records), f, indent=2)


def generate_question():
    """生成不重复的问题"""
    used = set()

    def _gen():
        # 优先从错题集选择（50%概率）
        if error_records and random.random() < 0.5:
            record = random.choice(error_records)
            question = record["question"]
            answer = record["correct"]
            source = "error"
        else:
            # 随机生成新题
            table = random.choice(list(tables.keys()))
            x, y = random.choice(tables[table])
            if random.choice([True, False]):
                question = f"{table}({json.dumps(x)}) = ?"
                answer = y
            else:
                question = f"{table}^-1({json.dumps(y)}) = ?"
                answer = x
            source = "new"
        return question, answer, source

    while True:
        q, a, s = _gen()
        if q not in used:
            used.add(q)
            return q, a, s


def validate_answer(user_input, correct_answer):
    """验证答案（支持数字和字符串）"""
    try:
        # 尝试数字比较
        user_num = round(float(user_input), 2)
        correct_num = round(float(correct_answer), 2)
        return user_num == correct_num
    except (ValueError, TypeError):
        # 字符串比较（不区分大小写和首尾空格）
        return str(user_input).strip().lower() == str(correct_answer).strip().lower()


def quiz():
    load_notes()
    while True:
        results = []
        used_questions = set()

        for q_num in range(1, 11):
            # 生成不重复的问题
            while True:
                question, correct, source = generate_question()
                if question not in used_questions:
                    used_questions.add(question)
                    break

            # 开始答题
            print(f"\n问题 {q_num}: {question}")
            start_time = time.time()
            user_input = input("请输入答案：").strip()
            elapsed = time.time() - start_time

            # 验证答案
            is_correct = validate_answer(user_input, correct)

            # 记录结果
            result = {
                "question": question,
                "correct": correct,
                "user": user_input,
                "time": round(elapsed, 1),
                "source": source
            }
            results.append(result)

            # 更新错题集
            if not is_correct or elapsed > 20:
                # 检查是否已存在相同记录
                if not any(r["question"] == question for r in error_records):
                    error_records.append(result)
            elif source == "error":
                # 从错题集中移除已正确回答的题目
                error_records[:] = [r for r in error_records if r["question"] != question]

        # 显示结果
        print("\n" + "=" * 40)
        print("答题结果：")
        correct_count = 0
        for i, r in enumerate(results, 1):
            status = "✓" if validate_answer(r["user"], r["correct"]) else "✗"
            print(f"{i:2}. {r['question']}")
            print(f"    您的答案: {r['user']} | 正确答案: {r['correct']}")
            print(f"    耗时: {r['time']}s {status}")
            if status == "✓":
                correct_count += 1

        print(f"\n正确率: {correct_count}/10 ({correct_count * 10}%)")
        save_notes()

        if input("\n是否继续练习？(Y/N): ").upper() != 'Y':
            print("练习结束！错题已保存至note.json")
            break


if __name__ == "__main__":
    print("函数复习程序（增强版）")
    print("功能说明：")
    print("- 每组10题保证不重复")
    print("- 优先从错题集出题（答对自动移除）")
    print("- 支持数字和字符串类型答案")
    print("- 自动记录错题和超时题目")
    print("------------------------------------")
    quiz()