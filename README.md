# Top Conference Hallucination Radar

自动追踪 2026、2025 年 ICML、ICLR、NeurIPS、ACL、CVPR 顶会论文，筛选与多模态大模型幻觉相关的工作，并生成中文论文摘要。项目使用 GitHub Actions 抓取 DBLP 顶会题录，用 arXiv / OpenAlex / Crossref / Google Scholar SerpApi 回填摘要，用 GitHub Pages 展示网页。

同时保留每日 arXiv 论文流：默认按最近 7 天抓取，数量自动控制为周级上限；手动运行时可把 `lookback_days` 改成 `1`、`7` 或 `30`，分别对应日/周/月窗口。arXiv 论文会用 OpenAlex 补机构信息，命中头部企业、顶尖高校或研究院时优先排序。

https://peipeng98.github.io/paper-collector/
