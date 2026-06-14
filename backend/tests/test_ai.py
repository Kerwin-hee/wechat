"""测试 AI 网关"""

import pytest
from app.services.ai_gateway import AIGateway
from app.services.ai_prompts import (
    build_continue_messages,
    build_full_article_messages,
    build_outline_messages,
    build_rewrite_messages,
    build_title_optimize_messages,
)


class TestAIPrompts:
    """Prompt 构建测试"""

    def test_build_full_article_messages(self):
        msgs = build_full_article_messages(
            topic="Python 异步编程",
            target_audience="后端开发者",
            style="技术深度",
            word_count=1500,
        )
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert "Python 异步编程" in msgs[1]["content"]
        assert "后端开发者" in msgs[1]["content"]

    def test_build_continue_messages(self):
        msgs = build_continue_messages("上文测试内容")
        assert len(msgs) == 2
        assert msgs[1]["content"].startswith("上文内容")

    def test_build_rewrite_messages(self):
        for style in ["formal", "lively", "concise", "compelling", "professional"]:
            msgs = build_rewrite_messages("测试文本", style)
            assert len(msgs) == 2

    def test_build_outline_messages(self):
        msgs = build_outline_messages("Python 入门教程")
        assert len(msgs) == 2
        assert "Python 入门教程" in msgs[1]["content"]

    def test_build_title_optimize_messages(self):
        msgs = build_title_optimize_messages("文章内容测试", "原标题")
        assert len(msgs) == 2
        assert "原标题" in msgs[1]["content"]


class TestAIQuotaLogic:
    """额度逻辑测试（不依赖数据库）"""

    def test_free_quota_limits(self):
        from app.services.ai_quota import FREE_QUOTA_LIMITS

        assert FREE_QUOTA_LIMITS["full_article"] == 3
        assert FREE_QUOTA_LIMITS["continue"] == 10
        assert FREE_QUOTA_LIMITS["rewrite"] == 5
        assert FREE_QUOTA_LIMITS["outline"] == 5
        assert FREE_QUOTA_LIMITS["title_optimize"] == 5
