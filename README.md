# Top Conference Hallucination Radar

自动追踪 2026、2025 年 ICML、ICLR、NeurIPS、ACL、CVPR 顶会论文，筛选与多模态大模型幻觉相关的工作，并生成中文论文摘要。项目使用 GitHub Actions 抓取 DBLP 顶会题录，用 arXiv / OpenAlex / Crossref 回填摘要，用 GitHub Pages 展示网页。


## 本地预览

如果你想在自己电脑上预览页面：

```bash
python -m http.server 8000 --directory web
```

浏览器打开：

```text
http://localhost:8000
```
