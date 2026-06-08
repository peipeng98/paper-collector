# Top Conference Hallucination Radar

自动追踪 2026、2025 年 ICML、ICLR、NeurIPS、ACL、CVPR 顶会论文，筛选与多模态大模型幻觉相关的工作，并生成中文论文摘要。项目使用 GitHub Actions 抓取 DBLP 顶会题录，用 arXiv / OpenAlex / Crossref 回填摘要，用 GitHub Pages 展示网页。

## 你需要配置什么

| 配置 | 必须吗 | 说明 |
| --- | --- | --- |
| GitHub Pages | 必须 | 不开启就看不到网页 |
| 研究方向 | 已配置 | 默认追踪多模态幻觉、视觉证据、因果干预、长生成幻觉和训练缓解方法 |
| 模型 API Key | 可选但推荐 | 不配置也能抓论文，但摘要会比较基础 |
| 其他运行参数 | 可不配置 | 默认值已经可以直接使用 |

## 第 1 步：Fork 或上传项目

把这个项目 Fork 到你的 GitHub 账号，或者上传到你自己的仓库。

下面假设你的仓库地址是：

```text
https://github.com/你的用户名/你的仓库名
```

## 第 2 步：开启 GitHub Pages

进入你的仓库页面，依次打开：

```text
Settings -> Pages -> Build and deployment -> Source
```

把 `Source` 选择为：

```text
GitHub Actions
```

保存后，网页会由 Actions 自动发布。

运行成功后，你可以在这里看到访问链接：

```text
Settings -> Pages
```

链接通常长这样：

```text
https://你的用户名.github.io/你的仓库名/
```

例如这个仓库对应的形式是：

```text
https://peipeng98.github.io/paper-collector/
```

## 手动清空论文缓存

如果之前已经积累了很多低质量或缺少摘要的论文，可以手动清缓存重新跑一次：

1. 打开仓库的 `Actions`。
2. 进入左侧的 `Paper Daily` workflow。
3. 点击右侧 `Run workflow`。
4. 把 `clear_cache` 填成 `true`。
5. 点击绿色的 `Run workflow` 按钮。

这会让本次运行忽略 `web/data/papers.json` 和 `web/data/conference_papers.json` 里的历史论文，重新按当前配置抓取顶会论文。第一次运行建议设置为 `true`，避免旧研究方向缓存混入页面。

## 数据保存方式

GitHub Actions 运行后不会再把 `web/data/*.json` commit 回 `main` 分支。最新论文数据会随 GitHub Pages artifact 发布到网页，同时保存一份到 GitHub Actions cache，下一次运行会先恢复这份缓存再增量更新。

这样可以避免自动更新产生提交、减少 rebase 冲突，也不会让论文数据反复改写仓库历史。注意：Actions cache 属于 GitHub 云端缓存，不适合作为永久数据库；如果你手动清理 Actions cache，下一次运行会从仓库现有数据重新初始化。

## 第 3 步：配置研究方向

默认配置已经写在 `config/interests.json`，可以直接运行。后续如果想在 GitHub 网页上改方向，也可以用 Issue 配置覆盖仓库默认配置。

1. 打开仓库的 `Issues`。
2. 点击 `New issue`。
3. 选择 `Research Interests` 模板。
4. 修改 JSON 里的 `name`、`description`、`keywords`、`arxiv_categories`。
5. Issue 标题保持为 `Research Interests`。
6. 点击提交。

一个方向大概长这样：

```json
{
  "id": "mllm_visual_object_hallucination",
  "name": "多模态视觉与对象幻觉",
  "description": "关注 MLLM/LVLM 的 visual hallucination、object hallucination、grounding failure 和 vision-language alignment failure。",
  "keywords": [
    "MLLM hallucination",
    "LVLM hallucination",
    "visual hallucination",
    "object hallucination",
    "visual grounding",
    "language prior"
  ],
  "arxiv_categories": ["cs.CV", "cs.CL", "cs.AI", "cs.LG"]
}
```

新手建议：

- `keywords` 尽量写英文，因为 arXiv 论文标题和摘要主要是英文。
- 每个方向先写 5 到 10 个关键词即可。
- 不确定分类时，可以先用 `cs.CL`、`cs.LG`、`cs.AI`。

### 当前论文来源

默认只抓顶会题录，不抓普通 arXiv 每日流：

- ICML 2026 / 2025
- ICLR 2026 / 2025
- NeurIPS 2026 / 2025
- ACL 2026 / 2025
- CVPR 2026 / 2025

顶会题录来自 DBLP。系统会按标题尝试用 arXiv、OpenAlex 和 Crossref 回填摘要、PDF 链接和分类；没有可靠摘要时，不会让模型只凭标题猜论文内容。

当前配置中 `sources` 被显式禁用，避免普通 arXiv / OpenAlex 论文作为每日论文流进入页面：

```json
{
  "sources": [
    { "type": "arxiv", "name": "arXiv", "enabled": false }
  ]
}
```

如果以后要扩展普通论文来源，可以按需启用这些可选来源：

- `openalex`：OpenAlex Works API，覆盖论文、会议、期刊和机构元数据。
- `crossref`：Crossref Works API，适合 DOI 和期刊/会议元数据。
- `semantic_scholar`：Semantic Scholar Graph API，适合补充摘要、开放 PDF 和引用相关元数据。
- `google_scholar_serpapi`：通过 SerpApi 的 Google Scholar API 搜索，需要 `SERPAPI_API_KEY`。
- `feed`：RSS/Atom，自定义期刊、实验室主页或代理服务。

### 当前顶会配置

当前只保留 main proceedings，不包含 Findings、workshops 或 demo track：

- ICML：`db/conf/icml/icml{year}.bht`
- ICLR：`db/conf/iclr/iclr{year}.bht`
- NeurIPS：`db/conf/nips/nips{year}.bht`，并兼容 `db/conf/neurips/neurips{year}.bht`
- ACL：`db/conf/acl/acl{year}-1.bht` 和 `db/conf/acl/acl{year}-2.bht`
- CVPR：`db/conf/cvpr/cvpr{year}.bht`

默认年份是 2026 和 2025。会议论文通常一年更新一次，DBLP 录入可能比官网发布时间晚一些；如果某个会议年份还没有 DBLP 题录，workflow 会记录 warning，并继续处理其他会议。

如果当前缓存里已经有某个会议某一年的论文，后续运行会直接复用缓存，不会重复请求这一年的 DBLP 题录；超过当前年份窗口的旧会议缓存会被清理。

会议源会先从 DBLP 获取题录、作者、DBLP 链接以及可用的 DOI/出版社链接。对筛选后的会议论文，系统会再按标题依次查询 arXiv、OpenAlex 和 Crossref；如果标题能可靠匹配且来源提供摘要，就回填摘要、PDF 链接和分类，再进入中文分析流程。没有找到摘要的会议论文不会默认让模型凭标题猜创新点。Semantic Scholar 默认不再参与自动搜索，避免频繁 429；如确实需要，可显式开启。

网页默认展示“顶会精品”，读取 `web/data/conference_papers.json`。`web/data/papers.json` 保留为空的 daily 数据文件，方便以后重新启用普通每日论文流。

如果你想在 Issue 里继续追加自己的会议，可以在 JSON 里加 `conference_sources.additional_venues`，默认会议不会被覆盖：

```json
{
  "conference_sources": {
    "additional_venues": [
      {
        "id": "pldi",
        "name": "PLDI",
        "group": "programming languages",
        "dblp_toc_patterns": ["db/conf/pldi/pldi{year}.bht"]
      }
    ]
  },
  "topics": [
    {
      "id": "compiler_systems",
      "name": "编译器系统",
      "description": "关注编译器优化、运行时系统和机器学习系统编译。",
      "keywords": ["compiler optimization", "runtime system", "machine learning compiler"],
      "arxiv_categories": ["cs.PL", "cs.DC"]
    }
  ]
}
```

如果你只想使用自己定义的会议源，可以设置：

```json
{
  "conference_sources": {
    "include_default_venues": false,
    "venues": [
      {
        "id": "pldi",
        "name": "PLDI",
        "group": "programming languages",
        "dblp_toc_patterns": ["db/conf/pldi/pldi{year}.bht"],
        "years": [2026, 2025]
      }
    ]
  },
  "topics": []
}
```

注意：`topics` 不能留空，实际使用时至少保留一个研究方向。

#### 自定义论文网站或期刊网站

推荐优先使用网站提供的 RSS、Atom、OAI、API 或“最新文章订阅”链接，然后配置成 `feed`：

```json
{
  "sources": [
    {
      "type": "feed",
      "name": "Nature Machine Intelligence",
      "url": "https://www.nature.com/natmachintell.rss"
    },
    {
      "type": "feed",
      "name": "自定义实验室论文",
      "url": "https://example.edu/lab/publications.atom"
    }
  ],
  "topics": []
}
```

`feed` 支持 RSS 和 Atom。它适合：

- 期刊 RSS/Atom。
- 会议或 workshop 的 accepted papers feed。
- 实验室、个人主页、机构仓库的论文订阅源。
- 你自己搭建的中转服务，把任意论文网站转换成 RSS/Atom。

如果目标网站只有普通 HTML 页面、需要浏览器渲染、验证码、搜索表单或复杂分页，当前采集器不会直接爬网页。更稳妥的做法是：用网站官方 API/RSS；或自己写一个小的代理服务，把它转换成 RSS/Atom 后再接入 `feed`。

#### 需要登录或 Token 的网站

不要把账号、密码、Cookie、Token 直接写进 Issue JSON 或 `config/interests.json`。这些配置会进入仓库历史或 Issue 页面，不安全。

对于需要认证的 RSS/Atom/API 代理，先在仓库中添加 Secrets：

```text
Settings -> Secrets and variables -> Actions -> Secrets -> New repository secret
```

常用两种方式：

1. Bearer Token：

添加 Secret：

| Name | Secret |
| --- | --- |
| `CUSTOM_FEED_BEARER_TOKEN` | 你的访问 Token |

然后在 `sources` 中引用这个 Secret 的环境变量名：

```json
{
  "sources": [
    {
      "type": "feed",
      "name": "Private Paper Feed",
      "url": "https://example.com/private/feed.xml",
      "bearer_token_env": "CUSTOM_FEED_BEARER_TOKEN"
    }
  ],
  "topics": []
}
```

采集器请求时会自动加：

```text
Authorization: Bearer <CUSTOM_FEED_BEARER_TOKEN>
```

2. 自定义 HTTP Headers：

添加 Secret：

| Name | Secret |
| --- | --- |
| `CUSTOM_FEED_HEADERS` | `{"X-API-Key":"你的 key"}` |

然后配置：

```json
{
  "sources": [
    {
      "type": "feed",
      "name": "Authenticated Journal Feed",
      "url": "https://example.com/feed.xml",
      "headers_env": "CUSTOM_FEED_HEADERS"
    }
  ],
  "topics": []
}
```

`CUSTOM_FEED_HEADERS` 必须是 JSON object。也可以包含 Cookie，但不推荐长期依赖 Cookie；Cookie 容易过期，也可能违反目标网站规则。更建议使用官方 API Token 或你自己的代理服务。

#### Google Scholar

Google Scholar 没有稳定官方公开 API，不建议直接爬网页。直接爬 Google Scholar 往往会遇到验证码、封 IP、HTML 结构变化和服务条款风险。

如果确实需要 Google Scholar，有两个推荐方式：

1. 使用 SerpApi：

添加 Secret：

| Name | Secret |
| --- | --- |
| `SERPAPI_API_KEY` | 你的 SerpApi Key |

然后在 `sources` 中启用：

```json
{
  "sources": [
    {
      "type": "google_scholar_serpapi",
      "name": "Google Scholar"
    }
  ],
  "topics": []
}
```

2. 使用第三方或自建服务转成 RSS/Atom：

```json
{
  "sources": [
    {
      "type": "feed",
      "name": "Google Scholar Proxy Feed",
      "url": "https://example.com/google-scholar-feed.xml"
    }
  ],
  "topics": []
}
```

#### 访问失败时的行为

每个来源独立运行。某个来源出现超时、429、503、认证失败或格式错误时，会记录 warning 和 `stats.source_stats`，但不会让整个采集流程崩溃。

如果所有来源都失败，并且已有历史论文数据，系统会保留已有数据，避免网页被清空。

可选的 Actions Variables / Secrets：

| Name | 示例 | 说明 |
| --- | --- | --- |
| `PAPER_SOURCES` | `arxiv,openalex,crossref` | 未在 JSON 配置 `sources` 时使用的默认来源 |
| `CONTACT_EMAIL` | `you@example.com` | 提供给 OpenAlex/Crossref 的联系邮箱，进入 polite pool |
| `CROSSREF_EMAIL` | `you@example.com` | 只给 Crossref 使用的邮箱 |
| `OPENALEX_EMAIL` | `you@example.com` | 只给 OpenAlex 使用的邮箱 |
| `SEMANTIC_SCHOLAR_API_KEY` | `...` | Semantic Scholar API Key；默认不会使用，需同时设置 `ENABLE_SEMANTIC_SCHOLAR=true` |
| `SERPAPI_API_KEY` | `...` | 启用 `google_scholar_serpapi` 时需要 |
| `CUSTOM_FEED_HEADERS` | `{"X-API-Key":"..."}` | 自定义 feed/API 代理需要额外 HTTP headers 时使用，建议配置为 Secret |
| `CUSTOM_FEED_BEARER_TOKEN` | `...` | 自定义 feed/API 代理需要 Bearer Token 时使用，建议配置为 Secret |
| `MAX_NEW_PAPERS` | `50` | 每次运行最多新增展示的论文数，避免每天论文过多 |
| `MAX_STORED_PAPERS` | `50` | 网页数据文件最多保留的论文总数 |
| `MAX_NEW_CONFERENCE_PAPERS` | `50` | 每次运行最多新增进入顶会精品库的会议论文数 |
| `MAX_STORED_CONFERENCE_PAPERS` | `300` | 顶会精品库最多保留的论文总数，独立于每日论文 |
| `MAX_SUMMARIES` | `20` | 每次最多调用模型生成中文摘要的论文数 |
| `CLEAR_PAPER_CACHE` | `false` | 设为 `true` 时忽略历史缓存，重新生成论文列表 |
| `MIN_PAPER_SCORE` | `0.08` | 有摘要论文的最低相关性分数 |
| `MIN_TITLE_ONLY_SCORE` | `0.18` | 只有标题、缺少摘要论文的最低相关性分数 |
| `MIN_CONFERENCE_SCORE` | `0.18` | 会议题录没有关键词命中时的最低相关性分数 |
| `LLM_SUMMARIZE_CONFERENCE` | `true` | 是否对已有摘要的会议论文调用模型；缺摘要的 DBLP 题录仍不会默认调用 |
| `LLM_SUMMARIZE_TITLE_ONLY` | `false` | 是否对缺少摘要的论文调用模型；默认关闭，避免标题猜测 |
| `SOURCE_DELAY_SECONDS` | `3` | 非 arXiv 来源的 topic 请求间隔 |
| `DBLP_DELAY_SECONDS` | `5` | 不同 DBLP 会议源之间的请求间隔 |
| `DBLP_PATTERN_DELAY_SECONDS` | `3` | 同一会议不同 DBLP TOC pattern 之间的请求间隔 |
| `DBLP_RETRIES` | `3` | DBLP 临时错误的最大尝试次数 |
| `MAX_PER_CONFERENCE` | `1000` | 每个 DBLP TOC 最多读取的题录数 |
| `ARXIV_QUERY_MODE` | `keyword` | `keyword` 默认只按关键词抓取，避免分类宽搜淹没相关论文；`broad` 用关键词或分类的单次宽查询；`strict` 使用关键词和分类同时匹配 |
| `ARXIV_SORT_BY` | `lastUpdatedDate` | arXiv 排序字段，默认按最近更新，能捕获当天修订的论文 |
| `ARXIV_EXPAND_CATEGORY_SEARCH` | `false` | 是否在主查询之外再按相关分类追加一次查询；默认关闭以降低 arXiv 429 风险 |
| `ARXIV_CATEGORY_MAX_RESULTS` | `10` | 每个方向额外按 arXiv 分类抓取的最大数量 |
| `MIN_DAILY_PAPERS` | `8` | 当当天时间窗内 arXiv 论文不足时，至少从最近候选中补足的每日论文数量；设为 `0` 可关闭 |
| `DAILY_BACKFILL_DAYS` | `14` | arXiv 每日不足时允许回看最近多少天的候选论文 |
| `MAX_CONFERENCE_ABSTRACT_ENRICHMENTS` | `50` | 每次最多对多少篇会议候选论文按标题补摘要 |
| `CONFERENCE_ABSTRACT_SOURCES` | `arxiv,openalex,crossref` | 顶会论文摘要回填来源顺序；默认不使用 Semantic Scholar |
| `ENABLE_SEMANTIC_SCHOLAR` | `false` | 是否允许 `semantic_scholar` 出现在论文/会议摘要搜索链路中 |
| `CONFERENCE_ABSTRACT_DELAY_SECONDS` | `3` | 会议论文标题查询之间的间隔，避免请求过密 |
| `CONFERENCE_ABSTRACT_SEARCH_RESULTS` | `5` | 每个外部来源按标题返回的候选数量 |
| `MAX_CONFERENCE_ARXIV_ENRICHMENTS` | `50` | 旧变量名，未设置 `MAX_CONFERENCE_ABSTRACT_ENRICHMENTS` 时作为兼容值 |
| `CONFERENCE_ARXIV_DELAY_SECONDS` | `3` | 旧变量名，未设置 `CONFERENCE_ABSTRACT_DELAY_SECONDS` 时作为兼容值 |
| `CONFERENCE_ARXIV_SEARCH_RESULTS` | `5` | 旧变量名，未设置 `CONFERENCE_ABSTRACT_SEARCH_RESULTS` 时作为兼容值 |
| `ARXIV_RETRY_THROTTLED` | `false` | arXiv 返回 429/503 时默认快速跳过并使用其它来源；设为 `true` 会按退避策略等待重试 |
| `ARXIV_RETRIES` | `4` | arXiv 对非 429/503 临时错误的最大尝试次数 |

## 第 4 步：配置模型 API Key（可选）

不配置 API Key 也能运行；配置后中文摘要质量会更好。

进入：

```text
Settings -> Secrets and variables -> Actions -> Secrets -> New repository secret
```

如果你用 DeepSeek，添加：

| Name | Secret |
| --- | --- |
| `DEEPSEEK_API_KEY` | 你的 DeepSeek API Key |

如果你用 OpenAI，添加：

| Name | Secret |
| --- | --- |
| `OPENAI_API_KEY` | 你的 OpenAI API Key |

如果你用其他 OpenAI-compatible 服务，添加：

| Name | Secret |
| --- | --- |
| `LLM_API_KEY` | 你的服务商 API Key |

如果你需要指定模型或服务地址，再到：

```text
Settings -> Secrets and variables -> Actions -> Variables -> New repository variable
```

可选添加：

| Name | 示例 |
| --- | --- |
| `LLM_BASE_URL` | `https://api.deepseek.com/v1` |
| `LLM_MODEL` | `deepseek-chat` |

只用 DeepSeek 或 OpenAI 的默认地址时，可以不填这两个变量。

## 第 5 步：第一次手动运行

进入：

```text
Actions -> Paper Daily -> Run workflow
```

第一次建议这样设置：

```text
lookback_days = 7
clear_cache = true
```

`lookback_days` 对当前顶会模式影响很小，保留默认即可。`clear_cache = true` 会清空旧方向缓存，按 2026 / 2025 顶会配置重建论文库。

点击绿色的 `Run workflow` 后等待运行完成。成功后，打开你的 GitHub Pages 链接即可查看网页：

```text
https://你的用户名.github.io/你的仓库名/
```

## 之后会自动更新

项目默认每天北京时间 06:00 自动运行一次。

第一次手动运行会初始化 2026 / 2025 顶会论文库；之后每天定时运行会恢复 GitHub Actions cache，只抓取未缓存的会议年份，并保留已经筛选出的顶会论文。

网页里可以查看：

- 顶会精品论文
- 本周论文
- 本月论文
- 本周最相关的精选论文
- 直接点击 `下载 PDF` 保存论文

## 本地预览

如果你想在自己电脑上预览页面：

```bash
python -m http.server 8000 --directory web
```

浏览器打开：

```text
http://localhost:8000
```
