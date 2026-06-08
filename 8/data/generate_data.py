import pandas as pd
import numpy as np

np.random.seed(42)
n_samples = 1500

satisfaction = np.random.uniform(0.1, 1.0, n_samples)
evaluation = np.random.uniform(0.3, 1.0, n_samples)
project_count = np.random.randint(2, 8, n_samples)
tenure = np.random.randint(1, 11, n_samples)

left_prob = (
    0.6 * (1 - satisfaction) +
    0.3 * (tenure > 5).astype(float) +
    0.2 * (project_count > 5).astype(float) +
    0.1 * (1 - evaluation)
)
left_prob = np.clip(left_prob, 0, 1)
left = np.random.binomial(1, left_prob * 0.5, n_samples)

df = pd.DataFrame({
    'satisfaction': satisfaction.round(2),
    'evaluation': evaluation.round(2),
    'project_count': project_count,
    'tenure': tenure,
    'left': left
})

df.to_csv('d:/y/project/20260601/8/data/hr_data.csv', index=False, encoding='utf-8-sig')

print(f"数据集已生成，共 {len(df)} 条记录")
print(f"离职率: {df['left'].mean():.2%}")
print("\n数据样例:")
print(df.head())
