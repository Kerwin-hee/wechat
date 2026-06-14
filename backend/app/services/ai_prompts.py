"""AI Prompt 编排层 — 各场景 Prompt 模板"""

# ── 全文生成 ──

FULL_ARTICLE_SYSTEM = """你是一位专业的公众号内容创作者，擅长根据主题创作高质量、有吸引力的文章。

写作要求：
1. 根据目标受众调整语言风格和深度
2. 文章结构清晰：引言 → 正文（分点展开）→ 总结
3. 使用 Markdown 格式组织内容
4. 适当使用加粗、列表、引用等格式增强可读性
5. 语言自然流畅，避免 AI 感过重"""

FULL_ARTICLE_USER = """请帮我写一篇公众号文章。

主题：{topic}
目标读者：{target_audience}
写作风格：{style}
字数要求：约 {word_count} 字
{reference_materials_section}

请直接开始写文章正文，不要写标题（标题我会另外生成）。"""


# ── 续写 ──

CONTINUE_SYSTEM = """你是一位公众号文章写作助手。你的任务是根据上文自然地续写下一段内容。
续写要求：
1. 保持与上文一致的风格、语气和视角
2. 内容连贯，逻辑通顺
3. 不要重复上文已写的内容
4. 每次续写 100-300 字"""

CONTINUE_USER = """上文内容：
{context}

请自然地续写下一段内容。"""


# ── 改写（5 种风格）─

REWRITE_SYSTEM = """你是一位文案改写专家。根据用户指定的风格改写文本，保持原意不变，仅调整表达方式。"""

REWRITE_STYLE_PROMPTS = {
    "formal": "请使用正式、专业的语言风格改写，适合商务场合。",
    "lively": "请使用轻松、活泼的语言风格改写，加入一些生活化的表达。",
    "concise": "请使用简洁、精炼的语言风格改写，去掉冗余表达。",
    "compelling": "请使用富有感染力、打动人心的语言风格改写，增强情感共鸣。",
    "professional": "请使用深度专业的语言风格改写，适当补充数据点和专业术语。",
}

REWRITE_USER = """原文：
{text}

{style_instruction}

请直接输出改写后的文本。"""


# ── 大纲生成 ──

OUTLINE_SYSTEM = """你是一位内容策划专家。根据主题生成结构化的文章大纲。

要求：
1. 大纲为树形结构，包含 H1/H2/H3 层级
2. 每个节点包含 id（用数字序号）、text（标题文本）、level（1/2/3）
3. 逻辑清晰，层次分明
4. 返回纯 JSON 格式，不要包含 markdown 代码块标记"""

OUTLINE_USER = """主题：{topic}

请生成一个结构化的文章大纲，以 JSON 格式返回，格式如下：
{{
  "topic": "主题",
  "nodes": [
    {{"id": "1", "text": "一级标题", "level": 1, "children": [
      {{"id": "1-1", "text": "二级标题", "level": 2, "children": []}}
    ]}}
  ]
}}"""


# ── 标题优化 ──

TITLE_SYSTEM = """你是一位公众号标题优化专家，擅长创作高打开率的标题。

要求：
1. 生成 10 个候选标题，分为 5 类：数字型、悬念型、痛点型、反差型、故事型
2. 每类 2 个标题
3. 每个标题不超过 30 字
4. 给出每个标题的预估打开率评分（0-100）
5. 返回纯 JSON 格式"""

TITLE_USER = """文章内容摘要：
{content}

当前标题（如有）：{current_title}

请生成 10 个候选标题，JSON 格式：
{{
  "candidates": [
    {{"title": "标题", "category": "数字型", "score": 85}}
  ]
}}"""


# ── Prompt 构建函数 ──


def build_full_article_messages(
    topic: str,
    target_audience: str | None = None,
    style: str | None = None,
    word_count: int = 1500,
    reference_materials: str | None = None,
) -> list[dict]:
    return [
        {"role": "system", "content": FULL_ARTICLE_SYSTEM},
        {
            "role": "user",
            "content": FULL_ARTICLE_USER.format(
                topic=topic,
                target_audience=target_audience or "公众号读者",
                style=style or "自然流畅",
                word_count=word_count,
                reference_materials_section=(
                    f"\n参考素材：\n{reference_materials}\n"
                    if reference_materials
                    else ""
                ),
            ),
        },
    ]


def build_continue_messages(context: str) -> list[dict]:
    return [
        {"role": "system", "content": CONTINUE_SYSTEM},
        {"role": "user", "content": CONTINUE_USER.format(context=context)},
    ]


def build_rewrite_messages(text: str, style: str) -> list[dict]:
    style_instruction = REWRITE_STYLE_PROMPTS.get(style, REWRITE_STYLE_PROMPTS["concise"])
    return [
        {"role": "system", "content": REWRITE_SYSTEM},
        {"role": "user", "content": REWRITE_USER.format(text=text, style_instruction=style_instruction)},
    ]


def build_outline_messages(topic: str) -> list[dict]:
    return [
        {"role": "system", "content": OUTLINE_SYSTEM},
        {"role": "user", "content": OUTLINE_USER.format(topic=topic)},
    ]


def build_title_optimize_messages(content: str, current_title: str | None = None) -> list[dict]:
    return [
        {"role": "system", "content": TITLE_SYSTEM},
        {
            "role": "user",
            "content": TITLE_USER.format(
                content=content[:2000],
                current_title=current_title or "无",
            ),
        },
    ]
