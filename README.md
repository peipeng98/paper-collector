# Paper Collector

自动追踪 2026、2025 年 ICML、ICLR、NeurIPS、ACL、CVPR、ICCV 顶会论文，并保留每日 arXiv 论文流。项目使用 GitHub Actions 抓取 DBLP 顶会题录，用 arXiv / OpenAlex / Crossref / Google Scholar SerpApi 回填摘要，用 DeepSeek 或 OpenAI 兼容 API 生成中文论文摘要，用 GitHub Pages 展示网页。

当前研究方向：

- 多模态大模型长文本幻觉
- 因果推断在多模态大模型中的应用
- 视频多模态大模型
- Agent 记忆系统
- CLIP training 与图文对比预训练

来源策略：

- `Conference` 页面追踪全部 5 条方向，结果按 topic 均衡控制数量。
- `Daily` 页面只追踪前三条方向，避免每日 arXiv 被 Agent memory 和 CLIP training 泛化结果淹没。
- 手动运行 GitHub Actions 时可把 `lookback_days` 改成 `1`、`7` 或 `30`，分别对应日/周/月窗口。
- arXiv 论文会用 OpenAlex 补机构信息，命中头部企业、顶尖高校或研究院时优先排序，但不会硬过滤其他论文。

https://peipeng98.github.io/paper-collector/
