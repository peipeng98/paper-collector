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
    { "type": "arxiv", "name": "arXiv", "enabled": true }
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
      },
      {
        "id": "iccv",
        "name": "ICCV",
        "group": "computer vision",
        "dblp_toc_patterns": ["db/conf/iccv/iccv{year}.bht"]
      }
    ]
  },
  "topics": [
    {
      "id": "long_form_mllm_hallucination",
      "name": "多模态大模型长文本幻觉",
      "description": "MLLM/LVLM/VLM 在长文本、多轮视觉描述、详细图像 caption、dense caption、长视频 caption 和开放式视觉回答中的幻觉、事实性、faithfulness、visual grounding、object/attribute/relation hallucination、temporal hallucination，以及长输出生成中的检测、定位和缓解。",
      "daily_enabled": true,
      "conference_enabled": true,
      "keywords": [
        "multimodal large language model hallucination",
        "MLLM hallucination",
        "long-form hallucination",
        "long caption hallucination",
        "hyper-detailed image captioning",
        "dense hallucination localization",
        "span-level hallucination detection",
        "video hallucination",
        "large vision-language model hallucination",
        "hallucination",
        "hallucinations",
        "large vision-language model",
        "large vision language model",
        "visual hallucination",
        "object hallucination",
        "temporal hallucination",
        "visual evidence",
        "visual grounding",
        "dehallucination",
        "VidHalluc",
        "VideoHallu",
        "POPE",
        "VCD",
        "OPERA"
      ],
      "arxiv_categories": ["cs.CV", "cs.CL", "cs.AI", "cs.LG"]
    },
    {
      "id": "causal_inference_for_mllm",
      "name": "因果推断在多模态大模型中的应用",
      "description": "causal inference、structural causal model、causal graph、counterfactual intervention、causal mediation、causal debiasing、causal disentanglement 或 causal decoding 用于 MLLM/VLM/LVLM/VideoQA/VQA、视觉 grounding 和幻觉缓解。",
      "daily_enabled": true,
      "conference_enabled": true,
      "keywords": [
        "causal inference multimodal large language model",
        "structural causal model MLLM",
        "counterfactual intervention vision-language model",
        "causal debiasing multimodal large language model",
        "causal mediation vision-language model",
        "modality prior hallucination",
        "language prior visual question answering causal",
        "causal decoding multimodal large language model",
        "causal graph vision-language model",
        "causal reasoning benchmark multimodal",
        "counterfactual visual grounding",
        "object co-occurrence bias",
        "CausalMM",
        "Causal-LLaVA",
        "COAD",
        "MuCR",
        "CausalVLBench"
      ],
      "arxiv_categories": ["cs.CV", "cs.CL", "cs.AI", "cs.LG"]
    },
    {
      "id": "video_mllm_vid_llm",
      "name": "视频多模态大模型",
      "description": "Video MLLM、Video-LLM、Vid-LLM、video large language model 与 LLM-based video understanding，包括模型架构、视频指令微调、长视频理解、streaming video、temporal reasoning、temporal grounding、video QA、frame sampling、video token compression、长视频 memory、字幕和音频融合，以及 benchmark/evaluation。",
      "daily_enabled": true,
      "conference_enabled": true,
      "keywords": [
        "video multimodal large language model",
        "Video-LLM",
        "Vid-LLM",
        "video large language model",
        "long video understanding",
        "streaming video understanding",
        "temporal reasoning benchmark",
        "temporal grounding video",
        "video instruction tuning",
        "video question answering large language model",
        "video token compression",
        "Video-MME",
        "MVBench",
        "MLVU",
        "TempCompass",
        "VideoChatGPT",
        "Video-LLaVA",
        "Video-LLaMA",
        "MovieChat",
        "TimeChat",
        "LongVideoBench"
      ],
      "arxiv_categories": ["cs.CV", "cs.CL", "cs.AI", "cs.LG"]
    },
    {
      "id": "llm_agent_memory_systems",
      "name": "Agent 记忆系统",
      "description": "LLM-based agents 的显式 memory systems，包括 long-term memory、episodic/semantic/procedural/working/skill/reflective memory、graph memory、memory consolidation、retrieval、update、selective forgetting、personalization、多会话连续性和 memory evaluation benchmark。过滤只有静态 RAG、没有 agent memory lifecycle 的论文。",
      "daily_enabled": false,
      "conference_enabled": true,
      "keywords": [
        "LLM agent memory",
        "memory systems LLM agents",
        "long-term memory LLM-based agents",
        "agent memory episodic semantic procedural",
        "memory consolidation LLM agent",
        "selective forgetting LLM agent memory",
        "reflective memory dialogue agent",
        "graph memory LLM agents",
        "skill library LLM agent",
        "multi-session conversation memory",
        "MemoryAgentBench",
        "MemGPT",
        "A-MEM",
        "Mem0",
        "MemoryBank",
        "Generative Agents",
        "Reflexion",
        "Voyager"
      ],
      "arxiv_categories": ["cs.AI", "cs.CL", "cs.LG", "cs.HC"]
    },
    {
      "id": "clip_training_contrastive_pretraining",
      "name": "CLIP training 与图文对比预训练",
      "description": "CLIP training、contrastive language-image pretraining、ALIGN/OpenCLIP/SigLIP/EVA-CLIP/Long-CLIP/LLM2CLIP 相关论文，重点关注训练目标、loss 改进、大 batch、negative sampling、数据过滤、caption quality、synthetic/long captions、scaling laws、可复现训练 recipe、多语言和领域适配。",
      "daily_enabled": false,
      "conference_enabled": true,
      "keywords": [
        "CLIP training",
        "contrastive language-image pretraining",
        "contrastive language-image learning",
        "image-text pair curation",
        "CLIP data filtering",
        "caption quality CLIP",
        "synthetic captions CLIP",
        "long caption CLIP training",
        "OpenCLIP training recipe",
        "DataComp CLIP training",
        "ALIGN noisy text supervision",
        "SigLIP sigmoid loss",
        "EVA-CLIP",
        "Long-CLIP",
        "LLM2CLIP",
        "MetaCLIP",
        "large batch CLIP contrastive loss",
        "scaling laws contrastive language-image"
      ],
      "arxiv_categories": ["cs.CV", "cs.CL", "cs.LG", "cs.AI"]
    }
  ]
}
```
