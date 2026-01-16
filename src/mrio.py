"""
MRIO 多区域投入产出模型分析脚本
主要目的：分析服装产业的跨国污染转移
"""

import pymrio
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt


def load_and_prepare_mrio(path):
    """
    加载和准备 MRIO 数据
    
    参数：
        path (str): MRIO 数据文件路径
    
    返回：
        io: 准备好的 MRIO 对象
    """
    print(f"正在加载 MRIO 数据：{path}")
    io = pymrio.parse_exiobase3(path)
    io.calc_all()  # 计算系统矩阵（技术系数、Leontief 逆等）
    print("✓ MRIO 数据加载完成")
    return io


def check_mrio_structure(io):
    """
    检查 MRIO 系统结构
    """
    regions = io.get_regions()
    sectors = io.get_sectors()
    extensions = io.extensions
    
    print("\n【系统结构检查】")
    print(f"国家/地区数量：{len(regions)}")
    print(f"前10个国家：{regions[:10]}")
    print(f"\n产业部门数量：{len(sectors)}")
    print(f"前10个部门：{sectors[:10]}")
    print(f"\n拓展账户数量：{len(extensions)}")
    
    return regions, sectors


def analyze_pm25_emissions(io):
    """
    分析 PM2.5 排放数据
    """
    print("\n【PM2.5 排放分析】")
    
    em_ext = io.air_emissions  # 获取空气污染账户
    print(f"污染物类型：\n{em_ext.F.index.tolist()}")
    
    # 筛选 PM2.5 数据
    pm25_mask = em_ext.F.index.str.contains("PM2.5", case=False)
    em_pm25 = em_ext.F.loc[pm25_mask]
    
    print(f"\nPM2.5 排放账户数量：{em_pm25.shape[0]}")
    print(f"PM2.5 矩阵形状：{em_pm25.shape}")
    
    # 计算总排放量
    F_pm25_total = em_pm25.sum(axis=0)
    print(f"\nPM2.5 总排放类型：{type(F_pm25_total)}")
    print(f"PM2.5 总排放形状：{F_pm25_total.shape}")
    
    return em_pm25, F_pm25_total


def plot_top_pm25(F_pm25_total, sectors, textile_core, top_n=20, outpath=None):
    """
    绘制 PM2.5 排放最多的前 N 项（区域-部门组合），并高亮纺织相关部门。
    返回保存的文件路径。
    """
    print(f"\n【绘图】绘制 PM2.5 排放前 {top_n} 项...")

    s = F_pm25_total.copy()
    if s.empty:
        print("✗ 无可用的 PM2.5 排放数据来绘图。")
        return None

    top = s.sort_values(ascending=False).head(top_n)
    # 为了把最大值放到图顶端，翻转顺序
    top_rev = top[::-1]

    def make_label(idx):
        # 支持 MultiIndex 或单一索引
        if hasattr(idx, '__iter__') and not isinstance(idx, str):
            try:
                return " - ".join([str(i) for i in idx])
            except Exception:
                return str(idx)
        return str(idx)

    labels = [make_label(i) for i in top_rev.index]
    values = top_rev.values

    # 设置颜色：纺织相关为红，其他为蓝
    colors = [('#d62728' if any(core in lab for core in textile_core) else '#1f77b4') for lab in labels]

    plt.style.use('seaborn-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))
    y = range(len(labels))
    ax.barh(y, values, color=colors)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel('PM2.5 排放量（总和）')
    ax.set_title(f'Top {top_n} PM2.5 排放（区域-部门）')
    plt.tight_layout()

    if outpath is None:
        outpath = os.path.join(os.getcwd(), 'pm25_top.png')
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"✓ 图已保存：{outpath}")
    return outpath


def define_textile_industry(sectors):
    """
    定义服装产业的核心和完整产业链
    
    参数：
        sectors (list): 所有产业部门列表
    
    返回：
        textile_idx (list): 服装产业在矩阵中的索引
    """
    print("\n【服装产业定义】")
    
    # 核心纺织产业
    textile_core = [
        "Textiles (17)",
        "Wearing apparel; furs (18)",
        "Leather and leather products (19)"
    ]
    
    # 完整产业链（包括废弃物处理）
    textile_full = [
        "Textiles (17)",
        "Wearing apparel; furs (18)",
        "Leather and leather products (19)",
        "Textiles waste for treatment: incineration",
        "Textiles waste for treatment: landfill"
    ]
    
    # 获取部门索引（兼容 pandas Index）
    textile_idx = []
    sectors_list = list(sectors)
    for sector in textile_core:
        if sector in sectors_list:
            idx = sectors_list.index(sector)
            textile_idx.append(idx)
            print(f"✓ {sector} 索引：{idx}")
        else:
            print(f"✗ 未找到部门：{sector}")
    
    return textile_idx, textile_core, textile_full


def main():
    """
    主函数：执行完整的分析流程
    """
    # 配置文件路径
    path = "/home/congxinguan/lige/codeData/data_handle/data/EXIOBASE_3.9.5/IOT_2018_pxp.zip"
    
    try:
        # 1. 加载数据
        io = load_and_prepare_mrio(path)
        
        # 2. 检查系统结构
        regions, sectors = check_mrio_structure(io)
        
        # 3. 分析 PM2.5 排放
        em_pm25, F_pm25_total = analyze_pm25_emissions(io)
        
        # 4. 定义服装产业
        textile_idx, textile_core, textile_full = define_textile_industry(sectors)
        
        # 5. 基本信息汇总
        print("\n【数据维度汇总】")
        print(f"地区数：{len(regions)}")
        print(f"产业数：{len(sectors)}")
        print(f"纺织产业部门数：{len(textile_idx)}")
        
        print("\n✓ 数据加载和分析完成！")
        
    except FileNotFoundError:
        print(f"❌ 错误：找不到文件 {path}")
    except Exception as e:
        print(f"❌ 发生错误：{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
