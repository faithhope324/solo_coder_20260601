from app.feature_extractor import ImageRetrieval
import os

def main():
    print("=" * 50)
    print("构建图像特征索引")
    print("=" * 50)
    
    data_dir = 'data/train'
    if not os.path.exists(data_dir):
        print(f"数据目录不存在: {data_dir}")
        return
    
    retrieval = ImageRetrieval()
    print(f"\n开始索引图片目录: {data_dir}")
    retrieval.build_index(data_dir)
    
    print(f"\n索引构建完成!")
    print(f"索引文件: models/feature_index.json")
    print(f"索引图片数: {len(retrieval.features)}")

if __name__ == '__main__':
    main()
