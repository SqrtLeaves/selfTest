import sys
import random
import re


def validate_args():
    """参数校验逻辑（参考Linux命令行工具的参数校验规范）"""
    if len(sys.argv) != 3:
        print("用法: python math_train.py <被乘数位数n> <乘数位数m>")
        print("示例: python math_train.py 2 3")
        sys.exit(1)

    try:
        n = int(sys.argv[1])
        m = int(sys.argv[2])
    except ValueError:
        print("错误：参数必须是正整数")
        sys.exit(1)

    if n < 1 or m < 1:
        print("错误：参数必须是大于0的整数")
        sys.exit(1)

    return n, m


def generate_problem(n, m):
    """生成数学题（包含动态位数验证）"""
    num1 = random.randint(10 ** (n - 1), 10 ** n - 1)
    num2 = random.randint(10 ** (m - 1), 10 ** m - 1)
    return num1, num2, num1 * num2


def parse_input(user_input):
    """解析用户输入（支持反向输入和格式清洗）"""
    if user_input.startswith('r'):
        cleaned = re.sub(r'\D', '', user_input[1:])
        return int(cleaned[::-1]) if cleaned else 0
    else:
        cleaned = re.sub(r'\D', '', user_input)
        return int(cleaned) if cleaned else 0


def main():
    n, m = validate_args()
    correct_count = 0
    round_num = 1

    print(f"\n▶ 开始速算训练：{n}位数 × {m}位数")
    print("提示：输入答案时可使用r开头反向输入（例如r12.34 → 4321）")

    while True:
        for q in range(1, 11):
            num1, num2, answer = generate_problem(n, m)
            print(f"\n第{round_num}轮-第{q}题：{num1} × {num2} = ?")

            user_input = input("答案：")
            user_answer = parse_input(user_input)

            if user_answer == answer:
                print("✅ 正确！")
                correct_count += 1
            else:
                print(f"❌ 错误，正确答案：{answer:_}")

        print(f"\n—— 第{round_num}轮统计 ——")
        print(f"正确率：{correct_count}/10 ({correct_count * 10}%)")
        correct_count = 0

        if input("\n继续练习？ (Y/N)：").upper() != 'Y':
            print("\n✧ 训练结束，再见！")
            break

        round_num += 1


if __name__ == "__main__":
    main()