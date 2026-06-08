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
      "id": "mllm_hallucination_factuality",
      "name": "多模态大模型幻觉与事实性",
      "description": "宽召回 MLLM/LVLM/VLM/audio-visual/video multimodal models 中的 hallucination、object hallucination、visual hallucination、cross-modal hallucination、factuality、faithfulness 和 grounding failure。",
      "keywords": [
        "hallucination",
        "multimodal hallucination",
        "MLLM hallucination",
        "LVLM hallucination",
        "VLM hallucination",
        "visual hallucination",
        "object hallucination",
        "cross-modal hallucination",
        "large vision-language model",
        "multimodal factuality",
        "visual grounding"
      ],
      "arxiv_categories": ["cs.CV", "cs.CL", "cs.AI", "cs.LG"]
    },
    {
      "id": "mllm_hallucination_mitigation_alignment",
      "name": "幻觉缓解、对齐与解码",
      "description": "覆盖 decoding、attention/activation steering、DPO/RLHF/preference optimization、reward model、self-correction 和 post-training alignment。",
      "keywords": [
        "hallucination mitigation",
        "mitigate hallucinations",
        "visual evidence prompting",
        "contrastive decoding",
        "activation steering",
        "attention intervention",
        "self-correction hallucination",
        "multimodal preference optimization",
        "DPO hallucination"
      ],
      "arxiv_categories": ["cs.CV", "cs.CL", "cs.AI", "cs.LG"]
    },
    {
      "id": "mllm_hallucination_detection_benchmark_attribution",
      "name": "幻觉检测、基准与归因分析",
      "description": "覆盖 hallucination detection、benchmark、evaluation dataset、token-level localization、visual evidence attribution、attention head analysis 和 causal/counterfactual analysis。",
      "keywords": [
        "hallucination detection",
        "hallucination evaluation",
        "hallucination benchmark",
        "token-level localization",
        "visual evidence",
        "visual evidence attribution",
        "attention head analysis",
        "visual grounding benchmark",
        "video hallucination"
      ],
      "arxiv_categories": ["cs.CV", "cs.CL", "cs.AI", "cs.LG"]
    }
  ]
}
```
