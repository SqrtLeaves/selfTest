import random
import time
import json
from collections import deque

round_level = 4

# 完整表格数据
tables = {
    'alpha': [
        (-0.15, 1.13), (-0.05, 1.05), (0.05, 0.95),
        (0.15, 0.87), (0.25, 0.8), (0.35, 0.74),
        (0.45, 0.69), (0.55, 0.65), (0.65, 0.61),
        (0.75, 0.57), (0.85, 0.54), (0.95, 0.51)
    ],
    'prime_inverse': [
        (2,0.5),(3,0.33),(5,0.2),(7,0.143),
        (11,0.091),(13,0.077),(17,0.059),(19,0.053),
        (23,0.043),(29,0.034),
        (31,0.032),(37,0.027),
        (41,0.024),(43,0.023),(47,0.021), 
        (53,0.019)
    ],
    'R2': [(2, 1.41), (3, 1.74), (4, 2.00), (5, 2.24),
          (6, 2.45), (7, 2.65), (8, 2.83), (9, 3.00)],
    'R3': [(2, 1.26), (3, 1.44), (4, 1.59), (5, 1.70),
          (6, 1.82), (7, 1.91), (8, 2.00), (9, 2.08)],
    'R4': [(2, 1.19), (3, 1.32), (4, 1.41), (5, 1.50),
          (6, 1.57), (7, 1.63), (8, 1.68), (9, 1.73)],
    'R5': [(2, 1.14), (3, 1.24), (4, 1.31), (5, 1.37),
          (6, 1.43), (7, 1.48), (8, 1.52), (9, 1.55)]
}

# 修改后的显示格式
display_formats = {
    'prime_inverse': {
        'forward': "1/{x}",
        "inverse": "prime(1/{y})"
    },
    'R2': {
        'forward': "{x}^[1/2]",
        'inverse': "{y}^2"
    },
    'R3': {
        'forward': "{x}^[1/3]",
        'inverse': "{y}^3"
    },
    'R4': {
        'forward': "{x}^[1/4]",
        'inverse': "{y}^4"
    },
    'R5': {
        'forward': "{x}^[1/5]",
        'inverse': "{y}^5"
    }
}

# 初始化记录系统
error_records = deque(maxlen=20)
timeout_records = deque(maxlen=20)

def format_question(table, direction, value):
    """生成标准数学表达式"""
    if table in display_formats:
        template = display_formats[table][direction]
        return template.format(x=value, y=value)
    # 默认格式
    return f"{table}({value})" if direction == 'forward' else f"{table}^-1({value})"

def load_notes():
    """加载记录"""
    global error_records, timeout_records
    try:
        with open("note.json", "r") as f:
            data = json.load(f)
            error_records = deque(data.get("errors", []), maxlen=20)
            timeout_records = deque(data.get("timeouts", []), maxlen=20)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

def save_notes():
    """保存记录"""
    with open("note.json", "w") as f:
        json.dump({
            "errors": list(error_records),
            "timeouts": list(timeout_records)
        }, f, indent=2)

def generate_question():
    """生成不重复的问题"""
    used = set()
    
    def _gen():
        # 优先历史记录（60%概率）
        combined = list(error_records) + list(timeout_records)
        if combined and random.random() < 0.6:
            record = random.choice(combined)
            return record["question"], record["correct"], record.get("type", "old")
        
        # 生成新题
        table = random.choice(list(tables.keys()))
        x, y = random.choice(tables[table])
        direction = random.choice(['forward', 'inverse'])
        
        question = f"{format_question(table, direction, x if direction == 'forward' else y)} = ?"
        correct = y if direction == 'forward' else x
        return question, correct, "new"
    
    while True:
        q, a, t = _gen()
        if q not in used:
            used.add(q)
            return q, a, t

def validate_answer(user_input, correct_answer):
    """增强型验证"""
    try:
        # 数值比较（保留两位小数）
        return round(float(user_input), round_level) == round(float(correct_answer), round_level)
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
    
    print("数学函数复习系统 v3.2")
    print("符号说明:")
    print("^[1/2]: 平方根  ^2: 平方")
    print("^[1/3]: 立方根  ^3: 立方")
    print("^[1/4]: 四次方根  ^4: 四次方")
    print("^[1/5]: 五次方根  ^5: 五次方")
    print("其他函数使用默认格式（如alpha(0.5)）")
    print("------------------------------------")
    
    while True:
        results = []
        used_questions = set()
        
        for q_num in range(1, 11):
            while True:
                question, correct, q_type = generate_question()
                if question not in used_questions:
                    used_questions.add(question)
                    break
                    
            print(f"\n问题 {q_num}: {question}")
            start_time = time.time()
            user_input = input("请输入答案：").strip()
            elapsed = time.time() - start_time
            
            is_correct = validate_answer(user_input, correct)
            result = {
                "question": question,
                "correct": correct,
                "user": user_input,
                "time": round(elapsed, 1),
                "is_correct": is_correct
            }
            
            update_records(question, result)
            results.append(result)
        
        # 显示结果
        print("\n" + "="*40)
        print("答题报告：")
        correct_count = sum(1 for r in results if r["is_correct"])
        
        for i, r in enumerate(results, 1):
            status = "✓" if r["is_correct"] else "✗"
            time_flag = "⌛" if r["time"] > 20 else ""
            print(f"{i:2}. {r['question']} {time_flag}")
            print(f"    您的答案: {r['user']} | 正确答案: {r['correct']:.4f} {status}")
            print(f"    耗时: {r['time']}s")
        
        print(f"\n正确率: {correct_count}/10 ({correct_count*10}%)")
        save_notes()
        
        if input("\n是否继续练习？(Y/N): ").upper() != 'Y':
            print("练习结束！记录已保存至note.json")
            break

if __name__ == "__main__":
    quiz()