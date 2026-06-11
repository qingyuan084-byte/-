"""
豆瓣电影数据清洗脚本

功能：读取原始 CSV → 去重 → 缺失值处理 → 日期/类型转换 → 输出清洗后数据
"""

import re
from pathlib import Path

import pandas as pd

# pandas 2.x Copy-on-Write 兼容：使用赋值而非 inplace
pd.set_option("future.no_silent_downcasting", True)


# ======================== 路径配置 ========================

INPUT_PATH = Path("data/raw/douban_all_movies.csv")
OUTPUT_PATH = Path("data/processed/douban_movies_cleaned.csv")


# ======================== 工具函数 ========================

def detect_encoding(filepath: Path) -> str:
    """自动检测 CSV 文件编码，返回 'utf-8' 或 'gbk'。"""
    for enc in ("utf-8", "gbk", "utf-8-sig", "gb18030"):
        try:
            with open(filepath, encoding=enc) as f:
                f.read(1024)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    return "utf-8"  # 兜底


def parse_year(date_val) -> int | None:
    """
    从多种格式中提取年份：
      '2018-07-05' → 2018
      '2018'       → 2018
      2018.0       → 2018
      空值         → None
    """
    if pd.isna(date_val):
        return None
    if isinstance(date_val, (int, float)):
        return int(date_val)
    # 字符串：匹配开头 4 位数字
    match = re.search(r"(\d{4})", str(date_val))
    return int(match.group(1)) if match else None


def split_genres(genre_val) -> list[str]:
    """将 '剧情, 喜剧, 犯罪' 拆成 ['剧情', '喜剧', '犯罪']。"""
    if pd.isna(genre_val) or str(genre_val).strip() == "":
        return []
    return [g.strip() for g in str(genre_val).split(",") if g.strip()]


# ======================== 主流程 ========================

def preprocess(input_path: Path = INPUT_PATH, output_path: Path = OUTPUT_PATH):
    """读取、清洗、输出 CSV。"""

    # 1. 读取 CSV（自动检测编码）
    enc = detect_encoding(input_path)
    print(f"[编码] 检测到: {enc}")
    df = pd.read_csv(input_path, encoding=enc, dtype={"movie_id": str})
    total_raw = len(df)

    # --- 清洗前统计 ---
    print(f"\n{'='*50}")
    print(f"清洗前记录数: {total_raw}")
    print(f"列名: {list(df.columns)}")
    print(f"\n缺失值统计 (清洗前):")
    missing_before = df.isnull().sum()
    missing_before = missing_before[missing_before > 0]
    if missing_before.empty:
        print("  无缺失值")
    else:
        for col, cnt in missing_before.items():
            print(f"  {col}: {cnt} ({cnt/len(df)*100:.1f}%)")

    # 2. 删除完全重复的行
    df = df.drop_duplicates()
    dup_removed = total_raw - len(df)
    if dup_removed > 0:
        print(f"\n[去重] 删除完全重复行: {dup_removed} 条")

    # 3. 处理缺失值
    # 3a. 评分 → 中位数
    if df["rating"].isnull().any():
        median_rating = df["rating"].median()
        df["rating"] = df["rating"].fillna(median_rating)
        print(f"[填充] rating 缺失值 → 中位数 {median_rating:.1f}")

    # 3b. 简介/剧情 → "暂无简介"
    if "summary" in df.columns:
        df["summary"] = df["summary"].fillna("暂无简介")
        df.loc[df["summary"] == "", "summary"] = "暂无简介"

    # 3c. 导演 → "未知"
    if "directors" in df.columns:
        df["directors"] = df["directors"].fillna("未知")
        df.loc[df["directors"] == "", "directors"] = "未知"

    # 3d. 演员 → "未知"
    if "actors" in df.columns:
        df["actors"] = df["actors"].fillna("未知")
        df.loc[df["actors"] == "", "actors"] = "未知"

    # 3e. 编剧 → "未知"（如有空）
    if "screenwriters" in df.columns:
        df["screenwriters"] = df["screenwriters"].fillna("未知")
        df.loc[df["screenwriters"] == "", "screenwriters"] = "未知"

    # 3f. 国家/地区 → "未知"
    if "countries" in df.columns:
        df["countries"] = df["countries"].fillna("未知")
        df.loc[df["countries"] == "", "countries"] = "未知"

    # 4. 上映日期 → 年份（整型）
    if "release_date" in df.columns:
        df["release_year"] = df["release_date"].apply(parse_year)
        null_years = df["release_year"].isnull().sum()
        if null_years > 0:
            print(f"[警告] {null_years} 条记录的年份无法解析，已置为 NaN")

    # 5. 类型 → 拆分为列表列
    if "genres" in df.columns:
        df["genre_list"] = df["genres"].apply(split_genres)
        # 保留原始 genres 列作为字符串

    # --- 清洗后统计 ---
    print(f"\n{'='*50}")
    print(f"清洗后记录数: {len(df)}")
    print(f"删除记录数: {total_raw - len(df)}")

    print(f"\n缺失值统计 (清洗后):")
    missing_after = df.isnull().sum()
    missing_after = missing_after[missing_after > 0]
    if missing_after.empty:
        print("  无缺失值")
    else:
        for col, cnt in missing_after.items():
            print(f"  {col}: {cnt} ({cnt/len(df)*100:.1f}%)")

    # 6. 输出
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n[输出] 已保存至 {output_path.resolve()}")
    print(f"[文件大小] {output_path.stat().st_size / 1024:.1f} KB")

    return df


if __name__ == "__main__":
    preprocess()
