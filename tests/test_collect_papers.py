import datetime as dt
import io
import json
import os
import tempfile
import urllib.error
import unittest
from pathlib import Path
from unittest import mock

from scripts.collect_papers import (
    ConferenceSource,
    apply_daily_affiliation_quality,
    arxiv_query_for_topic,
    arxiv_retry_wait_seconds,
    cached_conference_years,
    collect,
    collection_cutoff,
    conference_abstract_sources,
    default_conference_years,
    default_llm_base_url,
    default_llm_model,
    effective_daily_paper_limit,
    enrich_conference_paper_from_arxiv,
    fetch_arxiv,
    fallback_summary,
    find_google_scholar_serpapi_by_title,
    find_conference_abstract_by_title,
    google_scholar_paper_from_item,
    is_relevant_enough,
    has_meaningful_summary,
    is_retryable_dblp_error,
    is_retryable_arxiv_error,
    merge_with_retained_papers,
    merge_config,
    openalex_abstract_text,
    openalex_institutions_from_work,
    openalex_paper_from_work,
    llm_http_error_message,
    parse_arxiv_entries,
    parse_conference_sources,
    parse_dblp_html_toc,
    parse_dblp_hits,
    parse_sources,
    parse_topics,
    should_retry_arxiv_error,
    should_attempt_conference_abstract_enrichment,
    select_balanced_papers,
    trusted_affiliation_hits,
    should_summarize_paper_with_llm,
    split_conference_payload,
    score_paper,
    source_request_headers,
    SourceConfig,
    semantic_scholar_paper_from_item,
    titles_match,
    Topic,
    trim_papers_for_storage,
    uncached_conference_years,
)


def paper(paper_id: str, level: str, published: str) -> dict:
    return {
        "id": paper_id,
        "title": paper_id,
        "published": published,
        "best_match": {
            "topic_id": "topic",
            "topic_name": "Topic",
            "score": {"high": 0.9, "medium": 0.5, "low": 0.2}[level],
            "level": level,
            "reason": "test",
        },
        "matches": [],
        "chinese_summary": {},
    }


class RetentionTest(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("ARXIV_RETRY_MIN_SECONDS", None)
        os.environ.pop("ARXIV_RETRY_BASE_SECONDS", None)
        os.environ.pop("ARXIV_RETRY_MAX_SECONDS", None)
        os.environ.pop("ARXIV_RETRY_THROTTLED", None)
        os.environ.pop("CUSTOM_FEED_HEADERS", None)
        os.environ.pop("CUSTOM_FEED_BEARER_TOKEN", None)
        os.environ.pop("LLM_SUMMARIZE_CONFERENCE", None)
        os.environ.pop("LLM_SUMMARIZE_TITLE_ONLY", None)
        os.environ.pop("LLM_API_KEY", None)
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("DEEPSEEK_API_KEY", None)
        os.environ.pop("LLM_BASE_URL", None)
        os.environ.pop("LLM_MODEL", None)
        os.environ.pop("LLM_MAX_TOKENS", None)
        os.environ.pop("MIN_CONFERENCE_SCORE", None)
        os.environ.pop("MIN_CONFERENCE_TITLE_ONLY_SCORE", None)
        os.environ.pop("MIN_TITLE_ONLY_SCORE", None)
        os.environ.pop("MIN_PAPER_SCORE", None)
        os.environ.pop("CONFERENCE_ABSTRACT_SOURCES", None)
        os.environ.pop("CONFERENCE_ABSTRACT_SEARCH_RESULTS", None)
        os.environ.pop("CONFERENCE_ENRICHMENT_TITLE_TERMS", None)
        os.environ.pop("CONFERENCE_ENRICHMENT_NEAR_MISS_SCORE", None)
        os.environ.pop("CONFERENCE_REQUIRED_CONTEXT_TERMS", None)
        os.environ.pop("MAX_CONFERENCE_ABSTRACT_ENRICHMENTS", None)
        os.environ.pop("ENABLE_SEMANTIC_SCHOLAR", None)
        os.environ.pop("ARXIV_QUERY_MODE", None)
        os.environ.pop("MIN_DAILY_PAPERS", None)
        os.environ.pop("DAILY_BACKFILL_DAYS", None)
        os.environ.pop("SERPAPI_API_KEY", None)
        os.environ.pop("SERPAPI_KEY", None)
        os.environ.pop("DAILY_PAPER_LIMIT_MODE", None)
        os.environ.pop("MAX_DAILY_PAPERS", None)
        os.environ.pop("MAX_WEEKLY_PAPERS", None)
        os.environ.pop("MAX_MONTHLY_PAPERS", None)
        os.environ.pop("MAX_DAILY_PAPERS_PER_TOPIC", None)
        os.environ.pop("MAX_CONFERENCE_PAPERS_PER_TOPIC", None)
        os.environ.pop("DAILY_ENRICH_OPENALEX_METADATA", None)
        os.environ.pop("MAX_DAILY_METADATA_ENRICHMENTS", None)
        os.environ.pop("DAILY_METADATA_ENRICHMENT_DELAY_SECONDS", None)
        os.environ.pop("DAILY_METADATA_ENRICHMENT_MIN_SCORE", None)
        os.environ.pop("DAILY_AFFILIATION_MODE", None)
        os.environ.pop("DAILY_TRUSTED_AFFILIATION_BONUS", None)
        os.environ.pop("TRUSTED_AFFILIATION_TERMS", None)

    def test_arxiv_retry_wait_uses_retry_after_header(self) -> None:
        os.environ["ARXIV_RETRY_MIN_SECONDS"] = "30"
        error = urllib.error.HTTPError(
            "https://export.arxiv.org/api/query",
            429,
            "Too Many Requests",
            {"Retry-After": "75"},
            None,
        )

        self.assertEqual(arxiv_retry_wait_seconds(error, 0), 75.0)

    def test_arxiv_retry_wait_clamps_short_retry_after_header(self) -> None:
        os.environ["ARXIV_RETRY_MIN_SECONDS"] = "30"
        error = urllib.error.HTTPError(
            "https://export.arxiv.org/api/query",
            503,
            "Service Unavailable",
            {"Retry-After": "0"},
            None,
        )

        self.assertEqual(arxiv_retry_wait_seconds(error, 0), 30.0)

    def test_arxiv_retry_wait_uses_capped_backoff(self) -> None:
        os.environ["ARXIV_RETRY_MIN_SECONDS"] = "5"
        os.environ["ARXIV_RETRY_BASE_SECONDS"] = "10"
        os.environ["ARXIV_RETRY_MAX_SECONDS"] = "25"

        self.assertEqual(arxiv_retry_wait_seconds(TimeoutError("timed out"), 0), 10.0)
        self.assertEqual(arxiv_retry_wait_seconds(TimeoutError("timed out"), 2), 25.0)

    def test_arxiv_retryable_errors(self) -> None:
        rate_limited = urllib.error.HTTPError("url", 429, "Too Many Requests", {}, None)
        not_found = urllib.error.HTTPError("url", 404, "Not Found", {}, None)

        self.assertTrue(is_retryable_arxiv_error(rate_limited))
        self.assertTrue(is_retryable_arxiv_error(TimeoutError("timed out")))
        self.assertFalse(is_retryable_arxiv_error(not_found))

    def test_dblp_does_not_retry_missing_toc_500(self) -> None:
        missing_toc = urllib.error.HTTPError("url", 500, "Internal Server Error", {}, None)
        rate_limited = urllib.error.HTTPError("url", 429, "Too Many Requests", {}, None)

        self.assertFalse(is_retryable_dblp_error(missing_toc))
        self.assertTrue(is_retryable_dblp_error(rate_limited))

    def test_arxiv_retry_policy_fast_fails_throttling_by_default(self) -> None:
        rate_limited = urllib.error.HTTPError("url", 429, "Too Many Requests", {}, None)
        service_unavailable = urllib.error.HTTPError("url", 503, "Service Unavailable", {}, None)
        gateway_error = urllib.error.HTTPError("url", 502, "Bad Gateway", {}, None)

        self.assertFalse(should_retry_arxiv_error(rate_limited))
        self.assertFalse(should_retry_arxiv_error(service_unavailable))
        self.assertTrue(should_retry_arxiv_error(gateway_error))

    def test_arxiv_retry_policy_can_retry_throttling_when_enabled(self) -> None:
        os.environ["ARXIV_RETRY_THROTTLED"] = "true"
        rate_limited = urllib.error.HTTPError("url", 429, "Too Many Requests", {}, None)
        service_unavailable = urllib.error.HTTPError("url", 503, "Service Unavailable", {}, None)

        self.assertTrue(should_retry_arxiv_error(rate_limited))
        self.assertTrue(should_retry_arxiv_error(service_unavailable))

    def test_fetch_arxiv_does_not_sleep_on_service_unavailable_by_default(self) -> None:
        topic = Topic(
            id="llm_quant",
            name="LLM quantization",
            description="",
            keywords=["LLM quantization"],
            arxiv_categories=["cs.CL"],
        )
        service_unavailable = urllib.error.HTTPError(
            "https://export.arxiv.org/api/query",
            503,
            "Service Unavailable",
            {},
            None,
        )

        with (
            mock.patch("scripts.collect_papers.urllib.request.urlopen", side_effect=service_unavailable),
            mock.patch("scripts.collect_papers.time.sleep") as sleep_mock,
        ):
            with self.assertRaises(urllib.error.HTTPError):
                fetch_arxiv(topic, 1)

        sleep_mock.assert_not_called()

    def test_parse_sources_supports_custom_feed(self) -> None:
        sources = parse_sources(
            {
                "sources": [
                    "arxiv",
                    {
                        "type": "feed",
                        "name": "Journal Feed",
                        "url": "https://example.com/rss.xml",
                        "headers_env": "CUSTOM_FEED_HEADERS",
                    },
                    {"type": "crossref", "enabled": False},
                ]
            }
        )

        self.assertEqual([source.type for source in sources], ["arxiv", "feed"])
        self.assertEqual(sources[1].name, "Journal Feed")
        self.assertEqual(sources[1].url, "https://example.com/rss.xml")
        self.assertEqual(sources[1].headers_env, "CUSTOM_FEED_HEADERS")

    def test_parse_topics_supports_daily_and_conference_scopes(self) -> None:
        topics = parse_topics(
            {
                "topics": [
                    {"name": "Default Scope", "keywords": ["default"]},
                    {
                        "id": "conference_only",
                        "name": "Conference Only",
                        "keywords": ["agent memory"],
                        "daily_enabled": False,
                    },
                    {
                        "id": "daily_only",
                        "name": "Daily Only",
                        "keywords": ["arxiv stream"],
                        "conference_enabled": False,
                    },
                ]
            }
        )

        self.assertTrue(topics[0].daily_enabled)
        self.assertTrue(topics[0].conference_enabled)
        self.assertFalse(topics[1].daily_enabled)
        self.assertTrue(topics[1].conference_enabled)
        self.assertTrue(topics[2].daily_enabled)
        self.assertFalse(topics[2].conference_enabled)

    def test_semantic_scholar_sources_are_opt_in(self) -> None:
        sources = parse_sources({"sources": ["arxiv", "semantic_scholar"]})

        self.assertEqual([source.type for source in sources], ["arxiv"])

        os.environ["ENABLE_SEMANTIC_SCHOLAR"] = "true"
        sources = parse_sources({"sources": ["arxiv", "semantic_scholar"]})

        self.assertEqual([source.type for source in sources], ["arxiv", "semantic_scholar"])

    def test_source_request_headers_reads_secret_envs(self) -> None:
        os.environ["CUSTOM_FEED_HEADERS"] = '{"X-API-Key": "secret"}'
        os.environ["CUSTOM_FEED_BEARER_TOKEN"] = "token"

        headers = source_request_headers(
            SourceConfig(
                type="feed",
                name="Private Feed",
                url="https://example.com/feed.xml",
                headers_env="CUSTOM_FEED_HEADERS",
                bearer_token_env="CUSTOM_FEED_BEARER_TOKEN",
            )
        )

        self.assertEqual(headers["X-API-Key"], "secret")
        self.assertEqual(headers["Authorization"], "Bearer token")

    def test_openalex_abstract_text_reconstructs_inverted_index(self) -> None:
        abstract = openalex_abstract_text({"abstract_inverted_index": {"hello": [0], "world": [1]}})

        self.assertEqual(abstract, "hello world")

    def test_parse_arxiv_entries_reuses_atom_parser(self) -> None:
        xml = b"""
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <id>https://arxiv.org/abs/2601.00001</id>
            <title>Fast Tensor Compute for LLM Serving</title>
            <summary>This paper studies efficient tensor compute for large language model serving systems.</summary>
            <published>2026-01-01T00:00:00Z</published>
            <updated>2026-01-02T00:00:00Z</updated>
            <author><name>Ada Example</name></author>
            <category term="cs.AR" />
            <link title="pdf" href="https://arxiv.org/pdf/2601.00001" />
          </entry>
        </feed>
        """

        papers = parse_arxiv_entries(xml, seed_topic="arch")

        self.assertEqual(papers[0]["id"], "2601.00001")
        self.assertEqual(papers[0]["seed_topic"], "arch")
        self.assertEqual(papers[0]["authors"], ["Ada Example"])
        self.assertEqual(papers[0]["categories"], ["cs.AR"])

    def test_arxiv_query_defaults_to_keyword_search(self) -> None:
        topic = Topic(
            id="llm",
            name="LLM inference",
            description="",
            keywords=["LLM inference"],
            arxiv_categories=["cs.CL", "cs.LG"],
        )

        query = arxiv_query_for_topic(topic)

        self.assertIn('all:"LLM inference"', query)
        self.assertNotIn("cat:cs.CL", query)
        self.assertNotIn(" AND ", query)

    def test_arxiv_query_can_use_broad_mode(self) -> None:
        os.environ["ARXIV_QUERY_MODE"] = "broad"
        topic = Topic(
            id="llm",
            name="LLM inference",
            description="",
            keywords=["LLM inference"],
            arxiv_categories=["cs.CL", "cs.LG"],
        )

        query = arxiv_query_for_topic(topic)

        self.assertIn('all:"LLM inference"', query)
        self.assertIn("cat:cs.CL", query)
        self.assertIn(" OR ", query)
        self.assertNotIn(" AND ", query)

    def test_arxiv_query_can_use_strict_mode(self) -> None:
        os.environ["ARXIV_QUERY_MODE"] = "strict"
        topic = Topic(
            id="llm",
            name="LLM inference",
            description="",
            keywords=["LLM inference"],
            arxiv_categories=["cs.CL"],
        )

        query = arxiv_query_for_topic(topic)

        self.assertIn(" AND ", query)

    def test_keyword_scoring_does_not_match_acronyms_inside_words(self) -> None:
        topic = Topic(
            id="long_form",
            name="Long-form MLLM Hallucination",
            description="long-form multimodal hallucination",
            keywords=["DeCo", "OPERA", "video large language model"],
            arxiv_categories=[],
        )

        false_match = score_paper(
            topic,
            {
                "title": "Decoder-only Diffusion Fourier Neural Operator",
                "summary": "A generic visual generation method.",
                "categories": [],
            },
        )
        true_match = score_paper(
            topic,
            {
                "title": "OPERA: Mitigating Hallucination in Video Large Language Models",
                "summary": "This paper studies hallucination in video large language models.",
                "categories": [],
            },
        )

        self.assertEqual(false_match["keyword_hits"], [])
        self.assertEqual(true_match["keyword_hits"], ["OPERA", "video large language model"])

    def test_title_matching_allows_punctuation_differences(self) -> None:
        self.assertTrue(titles_match("Fast Tensor Compute: An LLM Serving Study.", "Fast Tensor Compute - An LLM Serving Study"))
        self.assertFalse(titles_match("Fast Tensor Compute", "Database Indexing for Cloud Storage"))

    def test_enrich_conference_paper_from_arxiv_copies_abstract_and_links(self) -> None:
        conference = {
            "id": "dblp:conf/isca/example",
            "source": "DBLP · ISCA",
            "source_type": "conference",
            "title": "Fast Tensor Compute",
            "summary": "DBLP 题录：ISCA 2026 会议论文。",
            "categories": ["ISCA"],
        }
        arxiv = {
            "id": "2601.00001",
            "title": "Fast Tensor Compute",
            "summary": "This paper presents a detailed architecture for tensor compute in LLM serving systems. " * 2,
            "paper_url": "https://arxiv.org/abs/2601.00001",
            "pdf_url": "https://arxiv.org/pdf/2601.00001",
            "authors": ["Ada Example"],
            "categories": ["cs.AR"],
        }

        self.assertTrue(enrich_conference_paper_from_arxiv(conference, arxiv))
        self.assertEqual(conference["abstract_source"], "arXiv")
        self.assertEqual(conference["paper_url"], "https://arxiv.org/abs/2601.00001")
        self.assertIn("cs.AR", conference["categories"])

    def test_semantic_scholar_candidate_normalizes_abstract_source(self) -> None:
        candidate = semantic_scholar_paper_from_item(
            {
                "paperId": "abc",
                "title": "Fast Tensor Compute",
                "abstract": "This paper presents a detailed architecture for tensor compute in LLM serving systems.",
                "authors": [{"name": "Ada Example"}],
                "year": 2026,
                "url": "https://www.semanticscholar.org/paper/abc",
                "openAccessPdf": {"url": "https://example.com/paper.pdf"},
                "venue": "ISCA",
                "fieldsOfStudy": ["Computer Science"],
            }
        )

        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["source"], "Semantic Scholar")
        self.assertEqual(candidate["authors"], ["Ada Example"])
        self.assertEqual(candidate["pdf_url"], "https://example.com/paper.pdf")
        self.assertIn("ISCA", candidate["categories"])

    def test_semantic_scholar_candidate_handles_null_lists(self) -> None:
        candidate = semantic_scholar_paper_from_item(
            {
                "paperId": "abc",
                "title": "Fast Tensor Compute",
                "abstract": "This paper presents a detailed architecture for tensor compute in LLM serving systems.",
                "authors": None,
                "fieldsOfStudy": None,
                "openAccessPdf": None,
            }
        )

        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["authors"], [])
        self.assertEqual(candidate["categories"], [])

    def test_dblp_toc_summary_is_not_meaningful_abstract(self) -> None:
        self.assertFalse(
            has_meaningful_summary(
                {
                    "source_type": "conference",
                    "summary": "DBLP 题录：ASPLOS 2026 会议论文。 页码：1815-1831。" * 3,
                }
            )
        )
        self.assertTrue(
            has_meaningful_summary(
                {
                    "source_type": "conference",
                    "abstract_source": "OpenAlex",
                    "summary": "This paper presents a detailed architecture for tensor compute in LLM serving systems. " * 2,
                }
            )
        )

    def test_openalex_candidate_reconstructs_abstract(self) -> None:
        candidate = openalex_paper_from_work(
            {
                "id": "https://openalex.org/W1",
                "title": "Fast Tensor Compute",
                "abstract_inverted_index": {
                    "This": [0],
                    "paper": [1],
                    "studies": [2],
                    "tensor": [3],
                    "compute": [4],
                },
                "publication_year": 2026,
                "authorships": [{"author": {"display_name": "Ada Example"}}],
                "concepts": [{"display_name": "Computer architecture"}],
            }
        )

        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["source"], "OpenAlex")
        self.assertEqual(candidate["summary"], "This paper studies tensor compute")

    def test_openalex_candidate_includes_institutions(self) -> None:
        work = {
            "id": "https://openalex.org/W2",
            "title": "Reliable Multimodal Hallucination Detection",
            "abstract_inverted_index": {"Reliable": [0], "multimodal": [1], "hallucination": [2]},
            "publication_year": 2026,
            "authorships": [
                {
                    "author": {"display_name": "Ada Example"},
                    "institutions": [{"display_name": "Stanford University"}],
                    "raw_affiliation_strings": ["OpenAI, San Francisco, USA"],
                }
            ],
            "concepts": [],
        }

        self.assertEqual(openalex_institutions_from_work(work), ["Stanford University", "OpenAI, San Francisco, USA"])
        candidate = openalex_paper_from_work(work)

        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["institutions"], ["Stanford University", "OpenAI, San Francisco, USA"])

    def test_daily_affiliation_quality_boosts_trusted_institutions(self) -> None:
        os.environ["DAILY_AFFILIATION_MODE"] = "prefer"
        os.environ["DAILY_TRUSTED_AFFILIATION_BONUS"] = "0.1"
        paper = {"institutions": ["Stanford University", "Small Lab"]}
        best_match = {"score": 0.35, "level": "low", "reason": "关键词命中：hallucination"}

        apply_daily_affiliation_quality(paper, best_match)

        self.assertEqual(trusted_affiliation_hits(paper), ["Stanford"])
        self.assertEqual(paper["affiliation_quality"], "trusted")
        self.assertEqual(best_match["score"], 0.45)
        self.assertEqual(best_match["level"], "medium")
        self.assertIn("机构命中：Stanford", best_match["reason"])

    def test_daily_affiliation_quality_can_require_trusted_institutions(self) -> None:
        os.environ["DAILY_AFFILIATION_MODE"] = "require"
        paper = {"institutions": ["Small Lab"]}
        best_match = {"score": 0.9, "level": "high", "reason": "关键词命中：hallucination"}

        apply_daily_affiliation_quality(paper, best_match)

        self.assertTrue(paper["daily_affiliation_rejected"])
        self.assertFalse(is_relevant_enough(paper, best_match))

    def test_effective_daily_paper_limit_can_follow_window(self) -> None:
        os.environ["DAILY_PAPER_LIMIT_MODE"] = "auto"
        os.environ["MAX_DAILY_PAPERS"] = "4"
        os.environ["MAX_WEEKLY_PAPERS"] = "12"
        os.environ["MAX_MONTHLY_PAPERS"] = "30"

        self.assertEqual(effective_daily_paper_limit(1, 50), 4)
        self.assertEqual(effective_daily_paper_limit(7, 50), 12)
        self.assertEqual(effective_daily_paper_limit(30, 50), 30)

    def test_balanced_selection_round_robins_topics_before_filling(self) -> None:
        papers = []
        for index, (topic_id, score) in enumerate(
            [
                ("a", 0.95),
                ("a", 0.94),
                ("a", 0.93),
                ("b", 0.70),
                ("b", 0.69),
                ("c", 0.50),
            ]
        ):
            item = paper(f"{topic_id}-{index}", "high", f"2026-01-0{index + 1}T00:00:00+00:00")
            item["best_match"]["topic_id"] = topic_id
            item["best_match"]["score"] = score
            papers.append(item)

        selected = select_balanced_papers(papers, max_total=5, max_per_topic=2)

        self.assertEqual([item["id"] for item in selected], ["a-0", "b-3", "c-5", "a-1", "b-4"])

    def test_conference_abstract_finder_tries_sources_after_arxiv_failure(self) -> None:
        semantic_candidate = {
            "id": "s2:abc",
            "source": "Semantic Scholar",
            "title": "Fast Tensor Compute",
            "summary": "This paper presents a detailed architecture for tensor compute in LLM serving systems. " * 2,
            "paper_url": "https://www.semanticscholar.org/paper/abc",
            "pdf_url": "",
            "authors": [],
            "categories": [],
        }
        os.environ["CONFERENCE_ABSTRACT_SOURCES"] = "arxiv,semantic_scholar"
        os.environ["ENABLE_SEMANTIC_SCHOLAR"] = "true"

        with (
            mock.patch("scripts.collect_papers.find_arxiv_by_title", side_effect=TimeoutError("slow")),
            mock.patch("scripts.collect_papers.find_semantic_scholar_by_title", return_value=semantic_candidate),
        ):
            candidate = find_conference_abstract_by_title("Fast Tensor Compute")

        self.assertEqual(candidate, semantic_candidate)

    def test_conference_abstract_sources_skip_semantic_by_default(self) -> None:
        os.environ["CONFERENCE_ABSTRACT_SOURCES"] = "arxiv,semantic_scholar,crossref"

        self.assertEqual(conference_abstract_sources(), ["arxiv", "crossref"])

    def test_conference_abstract_finder_does_not_call_semantic_unless_enabled(self) -> None:
        crossref_candidate = {
            "id": "doi:abc",
            "source": "Crossref",
            "title": "Fast Tensor Compute",
            "summary": "This paper presents a detailed architecture for tensor compute in LLM serving systems. " * 2,
            "paper_url": "https://doi.org/example",
            "pdf_url": "",
            "authors": [],
            "categories": [],
        }
        os.environ["CONFERENCE_ABSTRACT_SOURCES"] = "semantic_scholar,crossref"

        with (
            mock.patch("scripts.collect_papers.find_semantic_scholar_by_title") as semantic_mock,
            mock.patch("scripts.collect_papers.find_crossref_by_title", return_value=crossref_candidate),
        ):
            candidate = find_conference_abstract_by_title("Fast Tensor Compute")

        semantic_mock.assert_not_called()
        self.assertEqual(candidate, crossref_candidate)

    def test_google_scholar_serpapi_title_finder(self) -> None:
        os.environ["SERPAPI_API_KEY"] = "test-key"
        data = {
            "organic_results": [
                {
                    "title": "Visual Evidence Prompting Mitigates Hallucinations in Large Vision-Language Models",
                    "link": "https://example.com/paper",
                    "snippet": "Large Vision-Language Models suffer from hallucination, and visual evidence prompting mitigates hallucinations by grounding generations in fine-grained image evidence.",
                    "publication_info": {"summary": "Wei Li et al. - ACL, 2025"},
                    "resources": [{"file_format": "PDF", "link": "https://example.com/paper.pdf"}],
                }
            ]
        }

        with mock.patch("scripts.collect_papers.request_json", return_value=data) as request_mock:
            candidate = find_google_scholar_serpapi_by_title(
                "Visual Evidence Prompting Mitigates Hallucinations in Large Vision-Language Models"
            )

        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["source"], "Google Scholar")
        self.assertEqual(candidate["published"], "2025-01-01T00:00:00+00:00")
        self.assertEqual(candidate["pdf_url"], "https://example.com/paper.pdf")
        self.assertIn("api_key=test-key", request_mock.call_args.args[0])

    def test_google_scholar_item_parser_is_shared_with_source_fetch(self) -> None:
        candidate = google_scholar_paper_from_item(
            {
                "title": "Token-Level Detective Reward Model for Large Vision Language Models",
                "link": "https://example.com/tldr",
                "snippet": "A token-level reward model helps multimodal models self-correct hallucinated generations.",
                "publication_info": {"summary": "ICLR 2025"},
            },
            "Google Scholar",
        )

        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["categories"], ["Google Scholar"])
        self.assertEqual(candidate["published"], "2025-01-01T00:00:00+00:00")

    def test_conference_abstract_finder_supports_google_scholar_serpapi(self) -> None:
        scholar_candidate = {
            "id": "google-scholar:paper",
            "source": "Google Scholar",
            "title": "Token-Level Detective Reward Model for Large Vision Language Models",
            "summary": "This paper provides token-level feedback for multimodal models and uses the signal for hallucination evaluation and self-correction. " * 2,
            "paper_url": "https://example.com/tldr",
            "pdf_url": "",
            "authors": [],
            "categories": ["Google Scholar"],
        }
        os.environ["CONFERENCE_ABSTRACT_SOURCES"] = "google_scholar_serpapi"

        with mock.patch("scripts.collect_papers.find_google_scholar_serpapi_by_title", return_value=scholar_candidate):
            candidate = find_conference_abstract_by_title(
                "Token-Level Detective Reward Model for Large Vision Language Models"
            )

        self.assertEqual(candidate, scholar_candidate)

    def test_conference_enrichment_prefilter_uses_title_terms_and_near_miss_score(self) -> None:
        paper_with_title_signal = {
            "source_type": "conference",
            "title": "Token-Level Detective Reward Model for Large Vision Language Models",
            "summary": "DBLP 题录：ICLR 2025 会议论文。",
        }
        generic_paper = {
            "source_type": "conference",
            "title": "A Generic Optimization Method",
            "summary": "DBLP 题录：ICML 2025 会议论文。",
        }

        self.assertTrue(
            should_attempt_conference_abstract_enrichment(
                paper_with_title_signal,
                {"score": 0.0, "keyword_hits": []},
            )
        )
        self.assertFalse(
            should_attempt_conference_abstract_enrichment(
                generic_paper,
                {"score": 0.02, "keyword_hits": []},
            )
        )
        self.assertTrue(
            should_attempt_conference_abstract_enrichment(
                generic_paper,
                {"score": 0.12, "keyword_hits": []},
            )
        )

    def test_relevance_filter_rejects_weak_title_only_and_conference_matches(self) -> None:
        weak_title = {"title": "A Generic Optimization Study", "summary": ""}
        weak_conference = {
            "title": "A Generic Conference Paper",
            "summary": "DBLP 题录：ASPLOS 2026 会议论文。",
            "source_type": "conference",
        }
        keyword_match = {
            "title": "KV cache compression for LLM serving",
            "summary": "",
            "source_type": "conference",
        }

        self.assertFalse(is_relevant_enough(weak_title, {"score": 0.03, "keyword_hits": []}))
        self.assertFalse(is_relevant_enough(weak_conference, {"score": 0.05, "keyword_hits": []}))
        self.assertTrue(is_relevant_enough(keyword_match, {"score": 0.04, "keyword_hits": ["KV cache compression"]}))

    def test_relevance_filter_uses_stricter_conference_title_only_threshold(self) -> None:
        title_only_conference = {
            "title": "Orthogonal Subspace Decomposition for Generalizable Image Detection",
            "summary": "DBLP 题录：CVPR 2025 会议论文。",
            "source_type": "conference",
        }

        self.assertFalse(is_relevant_enough(title_only_conference, {"score": 0.25, "keyword_hits": []}))
        self.assertTrue(is_relevant_enough(title_only_conference, {"score": 0.35, "keyword_hits": []}))

    def test_relevance_filter_can_require_multimodal_context_for_conferences(self) -> None:
        os.environ["CONFERENCE_REQUIRED_CONTEXT_TERMS"] = "vision-language,visual,multimodal,LVLM,MLLM"
        generic_hallucination = {
            "title": "Faithfulness in Rationale Generation",
            "summary": "This work studies faithfulness and hallucination in text-only rationale generation. " * 2,
            "source_type": "conference",
        }
        multimodal_hallucination = {
            "title": "Object Hallucination Mitigation in Large Vision-Language Models",
            "summary": "This work studies object hallucination and visual grounding in LVLMs. " * 2,
            "source_type": "conference",
        }

        self.assertFalse(
            is_relevant_enough(
                generic_hallucination,
                {"score": 0.5, "keyword_hits": ["faithfulness"]},
            )
        )
        self.assertTrue(
            is_relevant_enough(
                multimodal_hallucination,
                {"score": 0.1, "keyword_hits": ["object hallucination"]},
            )
        )

    def test_llm_summary_skips_conference_and_title_only_by_default(self) -> None:
        self.assertFalse(should_summarize_paper_with_llm({"source_type": "conference", "summary": "DBLP 题录。"}))
        self.assertFalse(should_summarize_paper_with_llm({"source": "Crossref", "summary": ""}))
        self.assertTrue(should_summarize_paper_with_llm({"source": "arXiv", "summary": "x" * 100}))
        self.assertTrue(should_summarize_paper_with_llm({"source_type": "conference", "summary": "x" * 100}))

        os.environ["LLM_SUMMARIZE_CONFERENCE"] = "true"
        os.environ["LLM_SUMMARIZE_TITLE_ONLY"] = "true"
        self.assertTrue(should_summarize_paper_with_llm({"source_type": "conference", "summary": "DBLP 题录。"}))
        self.assertTrue(should_summarize_paper_with_llm({"source": "Crossref", "summary": ""}))

    def test_deepseek_defaults_use_current_api_model(self) -> None:
        os.environ["DEEPSEEK_API_KEY"] = "test-key"

        self.assertEqual(default_llm_base_url(), "https://api.deepseek.com")
        self.assertEqual(default_llm_model(), "deepseek-v4-flash")

    def test_llm_http_error_message_includes_response_body(self) -> None:
        error = urllib.error.HTTPError(
            "https://api.deepseek.com/chat/completions",
            400,
            "Bad Request",
            {},
            io.BytesIO(b'{"error":{"message":"Model Not Exist","type":"invalid_request_error"}}'),
        )

        message = llm_http_error_message(error)

        self.assertIn("HTTP 400", message)
        self.assertIn("Model Not Exist", message)

    def test_fallback_summary_distinguishes_api_failure_from_missing_api(self) -> None:
        summary = fallback_summary(
            {
                "title": "A multimodal hallucination paper",
                "summary": "This paper studies hallucination in multimodal large language models.",
            },
            {"reason": "matches hallucination"},
            "LLM API request failed: HTTP 401",
        )

        self.assertIn("模型 API 调用失败", summary["problem"])
        self.assertIn("HTTP 401", summary["limitations"])
        self.assertNotIn("未配置模型 API", summary["problem"])

    def test_merge_retains_previous_high_medium_and_recent_low(self) -> None:
        now = dt.datetime(2026, 5, 28, tzinfo=dt.timezone.utc)
        stale_low = paper("old-low", "low", "2026-03-01T00:00:00+00:00")
        stale_low["first_seen_at"] = "2026-03-02T00:00:00+00:00"
        existing = {
            "generated_at_iso": "2026-05-27T00:00:00+00:00",
            "papers": [
                paper("old-high", "high", "2026-05-26T00:00:00+00:00"),
                paper("old-medium", "medium", "2026-05-25T00:00:00+00:00"),
                paper("recent-low", "low", "2026-05-24T00:00:00+00:00"),
                stale_low,
            ],
        }

        merged, stats = merge_with_retained_papers(
            [paper("new-low", "low", "2026-05-28T00:00:00+00:00")],
            existing,
            now,
            recent_history_days=45,
        )

        self.assertEqual({item["id"] for item in merged}, {"new-low", "old-high", "old-medium", "recent-low"})
        self.assertEqual(stats["retained_paper_count"], 3)
        self.assertEqual(stats["retained_recent_low_count"], 1)
        self.assertEqual(stats["dropped_low_relevance_count"], 1)
        self.assertTrue(next(item for item in merged if item["id"] == "old-high")["retained_from_previous_run"])

    def test_merge_retains_only_active_conference_years(self) -> None:
        now = dt.datetime(2026, 5, 28, tzinfo=dt.timezone.utc)
        active = paper("isca-2025", "low", "2025-01-01T00:00:00+00:00")
        active["source_type"] = "conference"
        active["conference"] = {"id": "isca", "year": 2025}
        active["best_match"]["keyword_hits"] = ["active conference topic"]
        stale = paper("isca-2024", "low", "2024-01-01T00:00:00+00:00")
        stale["source_type"] = "conference"
        stale["conference"] = {"id": "isca", "year": 2024}
        existing = {
            "generated_at_iso": "2026-05-27T00:00:00+00:00",
            "papers": [active, stale],
        }

        merged, stats = merge_with_retained_papers(
            [],
            existing,
            now,
            recent_history_days=45,
            active_conference_years_by_source={"isca": {2026, 2025}},
        )

        self.assertEqual([item["id"] for item in merged], ["isca-2025"])
        self.assertEqual(stats["retained_paper_count"], 1)
        self.assertEqual(stats["dropped_low_relevance_count"], 1)

    def test_collection_cutoff_uses_previous_run_for_incremental_mode(self) -> None:
        now = dt.datetime(2026, 5, 28, 22, tzinfo=dt.timezone.utc)
        cutoff, mode = collection_cutoff(
            {"generated_at_iso": "2026-05-27T22:00:00+00:00"},
            now,
            days=7,
            incremental_since_last_run=True,
        )

        self.assertEqual(mode, "incremental")
        self.assertEqual(cutoff, dt.datetime(2026, 5, 27, 22, tzinfo=dt.timezone.utc))

    def test_collection_cutoff_falls_back_to_lookback(self) -> None:
        now = dt.datetime(2026, 5, 28, 22, tzinfo=dt.timezone.utc)
        cutoff, mode = collection_cutoff({}, now, days=7, incremental_since_last_run=True)

        self.assertEqual(mode, "lookback")
        self.assertEqual(cutoff, dt.datetime(2026, 5, 21, 22, tzinfo=dt.timezone.utc))

    def test_storage_trim_removes_low_then_oldest(self) -> None:
        payload = {
            "generated_at_iso": "2026-05-28T00:00:00+00:00",
            "papers": [
                paper("newer-high", "high", "2026-05-28T00:00:00+00:00"),
                paper("older-high", "high", "2026-05-20T00:00:00+00:00"),
                paper("newer-low", "low", "2026-05-28T00:00:00+00:00"),
            ],
            "stats": {},
        }

        trimmed, stats = trim_papers_for_storage(payload, max_stored_papers=2, max_data_bytes=0)
        self.assertEqual({item["id"] for item in trimmed}, {"newer-high", "older-high"})
        self.assertEqual(stats["storage_trimmed_by_level"]["low"], 1)

        payload["papers"] = trimmed
        trimmed, stats = trim_papers_for_storage(payload, max_stored_papers=1, max_data_bytes=0)
        self.assertEqual([item["id"] for item in trimmed], ["newer-high"])
        self.assertEqual(stats["storage_trimmed_by_level"]["high"], 1)

    def test_split_conference_payload_migrates_mixed_cache(self) -> None:
        existing = {
            "generated_at_iso": "2026-05-28T00:00:00+00:00",
            "papers": [
                {"id": "daily", "source": "arXiv"},
                {"id": "conf", "source_type": "conference"},
            ],
        }

        daily, conference = split_conference_payload(existing)

        self.assertEqual([item["id"] for item in daily["papers"]], ["daily"])
        self.assertEqual([item["id"] for item in conference["papers"]], ["conf"])

    def test_conference_years_default_to_recent_window(self) -> None:
        now = dt.datetime(2026, 5, 28, tzinfo=dt.timezone.utc)

        self.assertEqual(default_conference_years({}, now), [2026, 2025])
        self.assertEqual(default_conference_years({"lookback_years": 3}, now), [2026, 2025, 2024])
        self.assertEqual(default_conference_years({"years": [2024, "2026", "bad"]}, now), [2026, 2024])

    def test_cached_conference_years_reads_existing_payload(self) -> None:
        payload = {
            "papers": [
                {"source_type": "conference", "conference": {"id": "isca", "year": 2025}},
                {"source_type": "conference", "conference": {"id": "isca", "year": "2026"}},
                {"source_type": "arxiv", "conference": {"id": "isca", "year": 2024}},
            ]
        }

        self.assertEqual(cached_conference_years(payload), {"isca": {2026, 2025}})

    def test_uncached_conference_years_skips_cache_hits(self) -> None:
        source = ConferenceSource(
            id="isca",
            name="ISCA",
            group="computer architecture",
            dblp_toc_patterns=["db/conf/isca/isca{year}.bht"],
            years=[2026, 2025],
        )

        self.assertEqual(uncached_conference_years(source, {"isca": {2025}}), [2026])
        self.assertEqual(uncached_conference_years(source, {"isca": {2026, 2025}}), [])

    def test_issue_config_keeps_default_conferences_and_adds_custom_venue(self) -> None:
        default = {
            "conference_sources": {
                "enabled": True,
                "current_year": 2026,
                "venues": [
                    {
                        "id": "isca",
                        "name": "ISCA",
                        "group": "computer architecture",
                        "dblp_toc_patterns": ["db/conf/isca/isca{year}.bht"],
                    }
                ],
            },
            "topics": [{"name": "Default", "keywords": []}],
        }
        override = {
            "conference_sources": {
                "additional_venues": [
                    {
                        "id": "pldi",
                        "name": "PLDI",
                        "group": "programming languages",
                        "dblp_toc_patterns": ["db/conf/pldi/pldi{year}.bht"],
                    }
                ]
            },
            "topics": [{"name": "Custom", "keywords": ["compiler"]}],
        }

        merged = merge_config(default, override)
        venue_ids = [venue["id"] for venue in merged["conference_sources"]["venues"]]

        self.assertEqual(venue_ids, ["isca", "pldi"])
        self.assertEqual(merged["topics"][0]["name"], "Custom")

    def test_parse_conference_sources_can_disable_defaults(self) -> None:
        now = dt.datetime(2026, 5, 28, tzinfo=dt.timezone.utc)
        config = {
            "conference_sources": {
                "enabled": True,
                "years": [2025],
                "venues": [
                    {
                        "id": "isca",
                        "name": "ISCA",
                        "enabled": False,
                        "dblp_toc_patterns": ["db/conf/isca/isca{year}.bht"],
                    },
                    {
                        "id": "mlsys",
                        "name": "MLSys",
                        "dblp_toc_patterns": "db/conf/mlsys/mlsys{year}.bht",
                    },
                ],
            }
        }

        sources = parse_conference_sources(config, now)

        self.assertEqual([source.id for source in sources], ["mlsys"])
        self.assertEqual(sources[0].years, [2025])

    def test_parse_dblp_hits_builds_conference_papers(self) -> None:
        source = ConferenceSource(
            id="isca",
            name="ISCA",
            group="computer architecture",
            dblp_toc_patterns=["db/conf/isca/isca{year}.bht"],
            years=[2024],
        )
        data = {
            "result": {
                "hits": {
                    "hit": [
                        {
                            "info": {
                                "key": "conf/isca/Example24",
                                "title": "An Efficient Tensor Accelerator.",
                                "authors": {"author": [{"text": "Ada Example"}, {"text": "Lin System"}]},
                                "venue": "ISCA",
                                "pages": "1-14",
                                "doi": "10.1145/example",
                                "ee": "https://doi.org/10.1145/example",
                                "url": "https://dblp.org/rec/conf/isca/Example24",
                            }
                        },
                        {"info": {"key": "conf/isca/2024", "title": "Proceedings"}},
                    ]
                }
            }
        }

        papers = parse_dblp_hits(data, source, 2024, "db/conf/isca/isca2024.bht")

        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["id"], "dblp:conf/isca/Example24")
        self.assertEqual(papers[0]["source_type"], "conference")
        self.assertEqual(papers[0]["title"], "An Efficient Tensor Accelerator")
        self.assertEqual(papers[0]["authors"], ["Ada Example", "Lin System"])
        self.assertEqual(papers[0]["conference"]["year"], 2024)

    def test_parse_dblp_html_toc_builds_conference_papers(self) -> None:
        source = ConferenceSource(
            id="usenix_atc",
            name="USENIX ATC",
            group="systems",
            dblp_toc_patterns=["db/conf/usenix/usenix{year}.bht"],
            years=[2025],
        )
        html = """
        <li class="entry inproceedings" id="conf/usenix/2025">
          <span class="title" itemprop="name">Proceedings of the 2025 USENIX Annual Technical Conference.</span>
        </li>
        <li class="entry inproceedings" id="conf/usenix/GuptaIYBPKK25">
          <li class="ee"><a href="https://www.usenix.org/conference/atc25/presentation/gupta">electronic edition</a></li>
          <span itemprop="author"><span itemprop="name" title="Sushant Kumar Gupta">Sushant Kumar Gupta</span></span>,
          <span itemprop="author"><span itemprop="name" title="Anil Raghunath Iyer">Anil Raghunath Iyer</span></span>:<br>
          <span class="title" itemprop="name">Fast ACS: Low-Latency File-Based Ordered Message Delivery at Scale.</span>
          <span itemprop="pagination">1-17</span>
        </li>
        """

        papers = parse_dblp_html_toc(html, source, 2025, "db/conf/usenix/usenix2025.bht")

        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["id"], "dblp:conf/usenix/GuptaIYBPKK25")
        self.assertEqual(papers[0]["title"], "Fast ACS: Low-Latency File-Based Ordered Message Delivery at Scale")
        self.assertEqual(papers[0]["authors"], ["Sushant Kumar Gupta", "Anil Raghunath Iyer"])
        self.assertEqual(papers[0]["pdf_url"], "https://www.usenix.org/conference/atc25/presentation/gupta")

    def test_collect_enriches_conference_candidates_before_relevance_filtering(self) -> None:
        config = {
            "sources": [{"type": "arxiv", "name": "arXiv", "enabled": False}],
            "conference_sources": {
                "enabled": True,
                "years": [2025],
                "venues": [
                    {
                        "id": "iclr",
                        "name": "ICLR",
                        "group": "machine learning",
                        "dblp_toc_patterns": ["db/conf/iclr/iclr{year}.bht"],
                    }
                ],
            },
            "topics": [
                {
                    "id": "mllm_eval",
                    "name": "MLLM Hallucination Evaluation",
                    "description": "hallucination evaluation and visual grounding for large vision language models",
                    "keywords": ["hallucination evaluation", "visual grounding"],
                    "arxiv_categories": ["cs.CV"],
                }
            ],
        }
        conference_paper = {
            "id": "dblp:conf/iclr/Example25",
            "source": "DBLP · ICLR",
            "source_type": "conference",
            "title": "Token-Level Detective Reward Model for Large Vision Language Models",
            "authors": ["Ada Example"],
            "summary": "DBLP 题录：ICLR 2025 会议论文。",
            "published": "2025-01-01T00:00:00+00:00",
            "updated": "2025-01-01T00:00:00+00:00",
            "paper_url": "https://dblp.org/rec/conf/iclr/Example25",
            "pdf_url": "",
            "categories": ["ICLR", "machine learning", "2025"],
            "conference": {"id": "iclr", "name": "ICLR", "year": 2025},
        }
        abstract_candidate = {
            "id": "openalex:example",
            "source": "OpenAlex",
            "title": "Token-Level Detective Reward Model for Large Vision Language Models",
            "summary": "This paper studies hallucination evaluation for large vision language models and uses token-level feedback to improve visual grounding. " * 2,
            "published": "2025-01-01T00:00:00+00:00",
            "paper_url": "https://example.com/tldr",
            "pdf_url": "",
            "authors": ["Ada Example"],
            "categories": ["cs.CV"],
        }

        os.environ["MIN_CONFERENCE_SCORE"] = "0.9"
        os.environ["MAX_CONFERENCE_ABSTRACT_ENRICHMENTS"] = "5"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = tmp_path / "interests.json"
            output_path = tmp_path / "papers.json"
            conference_output_path = tmp_path / "conference.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with (
                mock.patch("scripts.collect_papers.fetch_dblp_conference", return_value=[conference_paper]),
                mock.patch("scripts.collect_papers.find_conference_abstract_by_title", return_value=abstract_candidate),
                mock.patch("scripts.collect_papers.time.sleep"),
            ):
                collect(
                    config_path,
                    output_path,
                    conference_output_path,
                    days=7,
                    max_per_topic=1,
                    max_summaries=0,
                    max_new_papers=10,
                    max_stored_papers=10,
                    max_new_conference_papers=10,
                    max_stored_conference_papers=10,
                    max_data_bytes=0,
                    incremental_since_last_run=False,
                    recent_history_days=45,
                    clear_cache=True,
                )

            conference_payload = json.loads(conference_output_path.read_text(encoding="utf-8"))

        self.assertEqual(conference_payload["stats"]["conference_abstract_enrichment_attempted"], 1)
        self.assertEqual(conference_payload["stats"]["conference_abstract_enrichment_succeeded"], 1)
        self.assertEqual(conference_payload["stats"]["conference_candidate_paper_count"], 1)
        self.assertEqual(conference_payload["papers"][0]["abstract_source"], "OpenAlex")
        self.assertEqual(conference_payload["papers"][0]["best_match"]["keyword_hits"], ["hallucination evaluation", "visual grounding"])

    def test_collect_uses_daily_and_conference_topic_scopes(self) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        config = {
            "sources": [{"type": "arxiv", "name": "arXiv"}],
            "conference_sources": {
                "enabled": True,
                "years": [2025],
                "venues": [
                    {
                        "id": "iclr",
                        "name": "ICLR",
                        "group": "machine learning",
                        "dblp_toc_patterns": ["db/conf/iclr/iclr{year}.bht"],
                    }
                ],
            },
            "topics": [
                {
                    "id": "daily_only",
                    "name": "Daily Hallucination",
                    "description": "daily hallucination stream",
                    "keywords": ["daily hallucination"],
                    "arxiv_categories": ["cs.CV"],
                    "conference_enabled": False,
                },
                {
                    "id": "conference_only",
                    "name": "Agent Memory Systems",
                    "description": "agent memory lifecycle",
                    "keywords": ["agent memory"],
                    "arxiv_categories": ["cs.AI"],
                    "daily_enabled": False,
                },
            ],
        }
        daily_paper = {
            "id": "2601.00003v1",
            "source": "arXiv",
            "title": "Daily Hallucination Tracking for Multimodal Models",
            "authors": ["Ada Example"],
            "summary": "This paper studies daily hallucination tracking for multimodal models. " * 3,
            "published": now.isoformat(),
            "updated": now.isoformat(),
            "paper_url": "https://arxiv.org/abs/2601.00003v1",
            "pdf_url": "https://arxiv.org/pdf/2601.00003v1",
            "categories": ["cs.CV"],
        }
        conference_paper = {
            "id": "dblp:conf/iclr/Memory25",
            "source": "DBLP · ICLR",
            "source_type": "conference",
            "title": "Agent Memory Systems for Long-Horizon LLM Agents",
            "authors": ["Grace Example"],
            "summary": "DBLP 题录：ICLR 2025 会议论文。",
            "published": "2025-01-01T00:00:00+00:00",
            "updated": "2025-01-01T00:00:00+00:00",
            "paper_url": "https://dblp.org/rec/conf/iclr/Memory25",
            "pdf_url": "",
            "categories": ["ICLR", "machine learning", "2025"],
            "conference": {"id": "iclr", "name": "ICLR", "year": 2025},
        }

        os.environ["MAX_CONFERENCE_ABSTRACT_ENRICHMENTS"] = "0"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = tmp_path / "interests.json"
            output_path = tmp_path / "papers.json"
            conference_output_path = tmp_path / "conference.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with (
                mock.patch("scripts.collect_papers.fetch_source_topic", return_value=[daily_paper]) as fetch_topic_mock,
                mock.patch("scripts.collect_papers.fetch_dblp_conference", return_value=[conference_paper]),
                mock.patch("scripts.collect_papers.time.sleep"),
            ):
                daily_payload = collect(
                    config_path,
                    output_path,
                    conference_output_path,
                    days=7,
                    max_per_topic=1,
                    max_summaries=0,
                    max_new_papers=10,
                    max_stored_papers=10,
                    max_new_conference_papers=10,
                    max_stored_conference_papers=10,
                    max_data_bytes=0,
                    incremental_since_last_run=False,
                    recent_history_days=45,
                    clear_cache=True,
                )

            conference_payload = json.loads(conference_output_path.read_text(encoding="utf-8"))

        self.assertEqual(fetch_topic_mock.call_count, 1)
        self.assertEqual(fetch_topic_mock.call_args.args[1].id, "daily_only")
        self.assertEqual([topic["id"] for topic in daily_payload["topics"]], ["daily_only"])
        self.assertEqual([topic["id"] for topic in conference_payload["topics"]], ["conference_only"])
        self.assertEqual(daily_payload["papers"][0]["best_match"]["topic_id"], "daily_only")
        self.assertEqual(conference_payload["papers"][0]["best_match"]["topic_id"], "conference_only")

    def test_collect_enriches_daily_arxiv_with_trusted_institutions(self) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        config = {
            "sources": [{"type": "arxiv", "name": "arXiv"}],
            "conference_sources": {"enabled": False},
            "topics": [
                {
                    "id": "mllm",
                    "name": "MLLM Hallucination",
                    "description": "multimodal large language model hallucination",
                    "keywords": ["multimodal hallucination", "visual hallucination"],
                    "arxiv_categories": ["cs.CV"],
                }
            ],
        }
        fetched_paper = {
            "id": "2601.00002v1",
            "source": "arXiv",
            "title": "Reliable Visual Hallucination Detection for Multimodal Models",
            "authors": ["Ada Example"],
            "summary": "This paper studies multimodal hallucination and visual hallucination detection in large vision-language models. " * 2,
            "published": now.isoformat(),
            "updated": now.isoformat(),
            "paper_url": "https://arxiv.org/abs/2601.00002v1",
            "pdf_url": "https://arxiv.org/pdf/2601.00002v1",
            "categories": ["cs.CV"],
        }
        openalex_candidate = {
            "id": "openalex:W2",
            "source": "OpenAlex",
            "title": fetched_paper["title"],
            "summary": fetched_paper["summary"],
            "published": now.isoformat(),
            "paper_url": "https://openalex.org/W2",
            "pdf_url": "",
            "authors": ["Ada Example"],
            "categories": ["cs.CV"],
            "institutions": ["Stanford University"],
        }

        os.environ["DAILY_ENRICH_OPENALEX_METADATA"] = "true"
        os.environ["DAILY_METADATA_ENRICHMENT_DELAY_SECONDS"] = "0"
        os.environ["DAILY_AFFILIATION_MODE"] = "prefer"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = tmp_path / "interests.json"
            output_path = tmp_path / "papers.json"
            conference_output_path = tmp_path / "conference.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with (
                mock.patch("scripts.collect_papers.fetch_source_topic", return_value=[fetched_paper]),
                mock.patch("scripts.collect_papers.find_openalex_by_title", return_value=openalex_candidate),
                mock.patch("scripts.collect_papers.time.sleep"),
            ):
                payload = collect(
                    config_path,
                    output_path,
                    conference_output_path,
                    days=7,
                    max_per_topic=1,
                    max_summaries=0,
                    max_new_papers=10,
                    max_stored_papers=10,
                    max_new_conference_papers=10,
                    max_stored_conference_papers=10,
                    max_data_bytes=0,
                    incremental_since_last_run=False,
                    recent_history_days=45,
                    clear_cache=True,
                )

        self.assertEqual(payload["stats"]["daily_metadata_enrichment_attempted"], 1)
        self.assertEqual(payload["stats"]["daily_metadata_enrichment_succeeded"], 1)
        self.assertEqual(payload["stats"]["daily_trusted_affiliation_count"], 1)
        self.assertEqual(payload["papers"][0]["institutions"], ["Stanford University"])
        self.assertEqual(payload["papers"][0]["trusted_affiliation_hits"], ["Stanford"])

    def test_collect_backfills_recent_arxiv_when_daily_window_is_empty(self) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        recent_but_not_today = (now - dt.timedelta(days=3)).isoformat()
        config = {
            "sources": [{"type": "arxiv", "name": "arXiv"}],
            "conference_sources": {"enabled": False},
            "topics": [
                {
                    "id": "tensor",
                    "name": "Tensor Compute",
                    "description": "tensor core architecture for LLM inference",
                    "keywords": ["tensor core", "LLM inference"],
                    "arxiv_categories": ["cs.AR"],
                }
            ],
        }
        fetched_paper = {
            "id": "2601.00001v1",
            "source": "arXiv",
            "title": "Fast Tensor Core Architecture for LLM Inference",
            "authors": ["Ada Example"],
            "summary": "This paper presents a tensor core architecture for efficient LLM inference. " * 3,
            "published": recent_but_not_today,
            "updated": recent_but_not_today,
            "paper_url": "https://arxiv.org/abs/2601.00001v1",
            "pdf_url": "https://arxiv.org/pdf/2601.00001v1",
            "categories": ["cs.AR"],
        }

        os.environ["MIN_DAILY_PAPERS"] = "1"
        os.environ["DAILY_BACKFILL_DAYS"] = "14"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config_path = tmp_path / "interests.json"
            output_path = tmp_path / "papers.json"
            conference_output_path = tmp_path / "conference.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with (
                mock.patch("scripts.collect_papers.fetch_source_topic", return_value=[fetched_paper]),
                mock.patch("scripts.collect_papers.time.sleep"),
            ):
                payload = collect(
                    config_path,
                    output_path,
                    conference_output_path,
                    days=1,
                    max_per_topic=1,
                    max_summaries=0,
                    max_new_papers=10,
                    max_stored_papers=10,
                    max_new_conference_papers=10,
                    max_stored_conference_papers=10,
                    max_data_bytes=0,
                    incremental_since_last_run=False,
                    recent_history_days=45,
                    clear_cache=True,
                )

        self.assertEqual(payload["stats"]["daily_candidate_paper_count"], 1)
        self.assertEqual(payload["stats"]["daily_backfill_added_count"], 1)
        self.assertTrue(payload["papers"][0]["backfilled_from_recent_arxiv"])


if __name__ == "__main__":
    unittest.main()
