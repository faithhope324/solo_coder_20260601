import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

DATA_PATH = 'd:/y/project/20260601/8/data/hr_data.csv'

def load_data():
    df = pd.read_csv(DATA_PATH, encoding='utf-8-sig')
    return df

def preprocess_data(df):
    X = df.drop('left', axis=1)
    y = df['left']
    return X, y

def split_data(X, y, test_size=0.2, random_state=42):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    return X_train, X_test, y_train, y_test

def get_data_summary(df):
    summary = {
        'total_samples': len(df),
        'left_count': df['left'].sum(),
        'stayed_count': len(df) - df['left'].sum(),
        'left_rate': df['left'].mean(),
        'features': list(df.columns[:-1])
    }
    return summary

if __name__ == '__main__':
    df = load_data()
    print("数据形状:", df.shape)
    print("\n数据概览:")
    print(df.head())
    print("\n描述统计:")
    print(df.describe())
    X, y = preprocess_data(df)
    print("\n特征矩阵形状:", X.shape)
    print("标签分布:")
    print(y.value_counts())
