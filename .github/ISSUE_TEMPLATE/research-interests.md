---
name: Research Interests
about: Override the default paper tracking topics with repository-specific JSON.
title: Research Interests
labels: configuration
assignees: ""
---

Edit the JSON block below to change tracked topics. Keep the issue title as `Research Interests`.

```json
{
  "sources": [
    { "type": "arxiv", "name": "arXiv", "enabled": false }
  ],
  "conference_sources": {
    "enabled": true,
    "years": [2026, 2025],
    "venues": [
      {
        "id": "icml",
        "name": "ICML",
        "group": "machine learning",
        "dblp_toc_patterns": ["db/conf/icml/icml{year}.bht"]
      },
      {
        "id": "iclr",
        "name": "ICLR",
        "group": "machine learning",
        "dblp_toc_patterns": ["db/conf/iclr/iclr{year}.bht"]
      },
      {
        "id": "neurips",
        "name": "NeurIPS",
        "group": "machine learning",
        "dblp_toc_patterns": [
          "db/conf/nips/nips{year}.bht",
          "db/conf/neurips/neurips{year}.bht"
        ]
      },
      {
        "id": "acl",
        "name": "ACL",
        "group": "natural language processing",
        "dblp_toc_patterns": [
          "db/conf/acl/acl{year}-1.bht",
          "db/conf/acl/acl{year}-2.bht"
        ]
      },
      {
        "id": "cvpr",
        "name": "CVPR",
        "group": "computer vision",
        "dblp_toc_patterns": ["db/conf/cvpr/cvpr{year}.bht"]
      }
    ]
  },
  "topics": [
    {
      "id": "mllm_visual_object_hallucination",
      "name": "多模态视觉与对象幻觉",
      "description": "关注 MLLM/LVLM 在图像理解、视觉问答和详细图像描述中的 visual hallucination、object hallucination、grounding failure、vision-language alignment failure，以及视觉证据不足或语言先验过强导致的非 grounded 输出。",
      "keywords": [
        "multimodal large language model hallucination",
        "MLLM hallucination",
        "LVLM hallucination",
        "visual hallucination",
        "object hallucination",
        "vision-language hallucination",
        "vision-language alignment",
        "visual grounding",
        "grounding failure",
        "language prior"
      ],
      "arxiv_categories": ["cs.CV", "cs.CL", "cs.AI", "cs.LG"]
    }
  ]
}
```
