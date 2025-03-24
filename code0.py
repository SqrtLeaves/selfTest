import random
import time
import json
from collections import deque

# 完整表格数据（已修正0.05）
tables = {
    'alpha': [
        (-0.15, 1.13), (-0.05, 1.05), (0.05, 0.95),
        (0.15, 0.87), (0.25, 0.8), (0.35, 0.74),
        (0.45, 0.69), (0.55, 0.65), (0.65, 0.61),
        (0.75, 0.57), (0.85, 0.54), (0.95, 0.51)
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

# 初始化独立记录队列
error_records = deque(maxlen=20)  # 错误记录
timeout_records = deque(maxlen=20)  # 超时记录


def load_notes():
    """加载分开的记录"""
    global error_records, timeout_records
    try:
        with open("note.json", "r") as f:
            data = json.load(f)
            error_records = deque(data.get("errors", []), maxlen=20)
            timeout_records = deque(data.get("timeouts", []), maxlen=20)
    except (FileNotFoundError, json.JSONDecodeError):
        pass


def save_notes():
    """分开保存两种记录"""
    with open("note.json", "w") as f:
        json.dump({
            "errors": list(error_records),
            "timeouts": list(timeout_records)
        }, f, indent=2)


def generate_question():
    """生成不重复的问题"""
    used = set()

    def _gen():
        # 合并两类记录并优先出题（60%概率）
        combined = list(error_records) + list(timeout_records)
        if combined and random.random() < 0.6:
            record = random.choice(combined)
            return record["question"], record["correct"], record.get("type", "old")

        # 生成新题
        table = random.choice(list(tables.keys()))
        x, y = random.choice(tables[table])
        if isinstance(x, str) or random.choice([True, False]):
            return f"{table}({json.dumps(x)}) = ?", y, "new"
        return f"{table}^-1({json.dumps(y)}) = ?", x, "new"

    while True:
        q, a, t = _gen()
        if q not in used:
            used.add(q)
            return q, a, t


def validate_answer(user_input, correct_answer):
    """增强型验证（支持字符串和数字）"""
    try:
        # 数字比较（保留两位小数）
        return round(float(user_input), 2) == round(float(correct_answer), 2)
    except:
        # 字符串比较（不区分大小写）
        return str(user_input).strip().lower() == str(correct_answer).strip().lower()


def update_records(question, result):
    """更新记录系统"""
    global error_records, timeout_records

    # 错误记录
    if not result["is_correct"]:
        error_records = deque(
            [r for r in error_records if r["question"] != question],
            maxlen=20
        )
        error_records.append({
            "question": question,
            "correct": result["correct"],
            "user": result["user"],
            "time": result["time"],
            "type": "error"
        })

    # 超时记录
    if result["time"] > 20:
        timeout_records = deque(
            [r for r in timeout_records if r["question"] != question],
            maxlen=20
        )
        timeout_records.append({
            "question": question,
            "correct": result["correct"],
            "user": result["user"],
            "time": result["time"],
            "type": "timeout"
        })

    # 移除正确回答的历史记录
    if result["is_correct"]:
        error_records = deque(
            [r for r in error_records if r["question"] != question],
            maxlen=20
        )
        timeout_records = deque(
            [r for r in timeout_records if r["question"] != question],
            maxlen=20
        )


def quiz():
    global error_records, timeout_records
    load_notes()

    while True:
        results = []
        used_questions = set()

        # 生成一组题目
        for q_num in range(1, 11):
            while True:
                question, correct, q_type = generate_question()
                if question not in used_questions:
                    used_questions.add(question)
                    break

            # 答题流程
            print(f"\n问题 {q_num}: {question}")
            start_time = time.time()
            user_input = input("请输入答案：").strip()
            elapsed = time.time() - start_time

            # 验证结果
            is_correct = validate_answer(user_input, correct)
            result = {
                "question": question,
                "correct": correct,
                "user": user_input,
                "time": round(elapsed, 1),
                "is_correct": is_correct
            }

            # 更新记录系统
            update_records(question, result)
            results.append(result)

        # 显示结果
        print("\n" + "=" * 40)
        print("答题报告：")
        correct_count = sum(1 for r in results if r["is_correct"])

        # 详细结果
        for i, r in enumerate(results, 1):
            status = "✓" if r["is_correct"] else "✗"
            time_flag = "⌛" if r["time"] > 20 else ""
            print(f"{i:2}. {r['question']} {time_flag}")
            print(f"    您的答案: {r['user']} | 正确答案: {r['correct']} {status}")
            print(f"    耗时: {r['time']}s")

        # 统计信息
        print(f"\n正确率: {correct_count}/10 ({correct_count * 10}%)")
        print(f"新增错题: {len([r for r in results if not r['is_correct']])}")
        print(f"新增超时: {len([r for r in results if r['time'] > 20])}")

        # 保存并询问
        save_notes()
        if input("\n是否继续练习？(Y/N): ").upper() != 'Y':
            print("练习结束！记录已更新")
            break


if __name__ == "__main__":
    print("数学函数复习系统 v2.0")
    print("功能特性：")
    print("- 独立错题/超时记录系统")
    print("- 智能题目生成算法")
    print("- 自动数据持久化")
    print("------------------------------------")
    quiz()