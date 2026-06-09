import csv
import random
from datetime import datetime, timedelta

dishes = [
    {"id": "D001", "name": "红烧肉", "category": "主食", "price": 48},
    {"id": "D002", "name": "宫保鸡丁", "category": "主食", "price": 38},
    {"id": "D003", "name": "鱼香肉丝", "category": "主食", "price": 32},
    {"id": "D004", "name": "麻婆豆腐", "category": "主食", "price": 22},
    {"id": "D005", "name": "糖醋里脊", "category": "主食", "price": 42},
    {"id": "D006", "name": "回锅肉", "category": "主食", "price": 36},
    {"id": "D007", "name": "炒饭", "category": "主食", "price": 18},
    {"id": "D008", "name": "牛肉面", "category": "主食", "price": 28},
    {"id": "D009", "name": "小笼包", "category": "小吃", "price": 16},
    {"id": "D010", "name": "春卷", "category": "小吃", "price": 12},
    {"id": "D011", "name": "炸鸡翅", "category": "小吃", "price": 24},
    {"id": "D012", "name": "椒盐排骨", "category": "小吃", "price": 36},
    {"id": "D013", "name": "奶茶", "category": "饮品", "price": 15},
    {"id": "D014", "name": "咖啡", "category": "饮品", "price": 20},
    {"id": "D015", "name": "鲜榨果汁", "category": "饮品", "price": 22},
    {"id": "D016", "name": "可乐", "category": "饮品", "price": 8},
    {"id": "D017", "name": "抹茶蛋糕", "category": "甜点", "price": 28},
    {"id": "D018", "name": "提拉米苏", "category": "甜点", "price": 32},
    {"id": "D019", "name": "芒果布丁", "category": "甜点", "price": 18},
    {"id": "D020", "name": "水果沙拉", "category": "甜点", "price": 24},
]

time_slot_weights = {
    "breakfast": 0.15,
    "lunch": 0.30,
    "afternoon_tea": 0.15,
    "dinner": 0.30,
    "supper": 0.10,
}

category_time_preference = {
    "breakfast": {"主食": 0.7, "小吃": 0.1, "饮品": 0.2, "甜点": 0.0},
    "lunch": {"主食": 0.7, "小吃": 0.1, "饮品": 0.15, "甜点": 0.05},
    "afternoon_tea": {"主食": 0.1, "小吃": 0.3, "饮品": 0.4, "甜点": 0.2},
    "dinner": {"主食": 0.65, "小吃": 0.1, "饮品": 0.15, "甜点": 0.1},
    "supper": {"主食": 0.3, "小吃": 0.35, "饮品": 0.25, "甜点": 0.1},
}


def get_time_range(slot):
    if slot == "breakfast":
        return 6, 10
    elif slot == "lunch":
        return 11, 14
    elif slot == "afternoon_tea":
        return 14, 17
    elif slot == "dinner":
        return 17, 21
    elif slot == "supper":
        return 21, 26
    return 0, 0


def generate_random_time(base_date, slot):
    start_h, end_h = get_time_range(slot)
    hour = random.randint(start_h, end_h - 1)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    days_to_add = hour // 24
    actual_hour = hour % 24
    return base_date + timedelta(
        days=days_to_add, hours=actual_hour, minutes=minute, seconds=second
    )


def weighted_random_choice(items, weights):
    total = sum(weights)
    r = random.uniform(0, total)
    cumulative = 0
    for item, w in zip(items, weights):
        cumulative += w
        if r <= cumulative:
            return item
    return items[-1]


def main():
    with open("data/dishes.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["菜品ID", "菜品名称", "类别", "价格"])
        for dish in dishes:
            writer.writerow([dish["id"], dish["name"], dish["category"], dish["price"]])

    orders = []
    start_date = datetime(2026, 5, 10)

    for day_offset in range(30):
        current_date = start_date + timedelta(days=day_offset)
        day_of_week = current_date.weekday()
        weekend_multiplier = 1.3 if day_of_week >= 5 else 1.0

        daily_orders = int(random.randint(80, 120) * weekend_multiplier)

        for _ in range(daily_orders):
            slot = weighted_random_choice(
                list(time_slot_weights.keys()), list(time_slot_weights.values())
            )
            order_time = generate_random_time(current_date, slot)

            table = random.randint(1, 20)

            prefs = category_time_preference[slot]
            categories = list(prefs.keys())
            cat_weights = list(prefs.values())

            num_dishes = random.randint(1, 4)
            for _ in range(num_dishes):
                selected_cat = weighted_random_choice(categories, cat_weights)
                cat_dishes = [d for d in dishes if d["category"] == selected_cat]
                dish = random.choice(cat_dishes)
                quantity = random.randint(1, 3)
                amount = dish["price"] * quantity

                orders.append(
                    [
                        order_time.strftime("%Y-%m-%d %H:%M:%S"),
                        round(amount, 2),
                        table,
                        dish["id"],
                        quantity,
                    ]
                )

    with open("data/orders.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["订单时间", "订单金额", "桌号", "菜品ID", "菜品数量"])
        for order in orders:
            writer.writerow(order)

    print(f"生成菜品数据: {len(dishes)} 条")
    print(f"生成订单数据: {len(orders)} 条")
    print("数据文件已保存到 data/ 目录")


if __name__ == "__main__":
    main()
