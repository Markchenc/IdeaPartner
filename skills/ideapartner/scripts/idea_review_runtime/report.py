"""Render each structured report block once, with traceable citations."""
from urllib.parse import quote
from .validation import SECTIONS, refs_in

def render_report(payload, ledger):
    zh = payload["language"] == "zh"
    titles = ["问题定义", "现有局限与核心困难", "核心研究与贡献设计", "方法构建", "实验设想", "预期困难"] if zh else [
        "Problem definition", "Limitations and core difficulty", "Contribution design",
        "Method construction", "Experimental setting", "Expected difficulties"]
    dims = dict(zip(("value", "contribution", "mechanism", "testability"),
                    ("问题价值", "贡献增量", "方法与机制", "可验证性与条件可行性") if zh else
                    ("Problem value", "Contribution", "Method and mechanism", "Testability and feasibility")))
    labels = {"researcher_stated": "原述", "evidence_supported": "证据支持", "inferred": "推断", "missing": "缺失"}
    def text(block):
        citations, seen = [], set()
        for cid in refs_in(block):
            claim = ledger["claims"][cid]
            for ref in claim["source_refs"]:
                sid = ref["source_id"]
                marker = (sid, claim["locator"])
                if marker in seen: continue
                seen.add(marker)
                source = ledger["sources"][sid]
                url = source.get("url")
                if not url:
                    ids = source["identifiers"]
                    url = ("https://doi.org/" + ids["doi"]) if ids.get("doi") else (
                        "https://arxiv.org/abs/" + ids["arxiv"] if ids.get("arxiv") else
                        "https://openalex.org/" + ids["openalex"].rsplit("/", 1)[-1])
                title = (source["title"] + " — " + claim["locator"]).replace("[", "\\[").replace("]", "\\]")
                citations.append(f"[{title}]({quote(url, safe=':/?&=#%+@')})")
        return block["text"] + (" " + "；".join(citations) if citations else "")
    out = ["# IdeaPartner", "", "## " + ("结论" if zh else "Decision"), "", text(payload["decision"]), "",
           "## " + ("结构化 idea" if zh else "Structured idea"), ""]
    for key, title in zip(SECTIONS, titles):
        out += ["### " + title, ""]
        for item in payload["structured_idea"][key]:
            provenance = labels[item["provenance"]] if zh else item["provenance"]
            out += [f"- **{provenance}：** " + text(item)]
        out.append("")
    out += ["## " + ("审查" if zh else "Assessment"), ""]
    for section in payload["assessment"]:
        out += ["### " + dims[section["dimension"]], ""]
        for block in section["blocks"]: out += [text(block), ""]
    for key, title in (("recommendations", "推进建议" if zh else "Next actions"),
                       ("limitations", "不确定性与限制" if zh else "Limitations")):
        out += ["## " + title, ""]
        for block in payload[key]: out += [text(block), ""]
    return "\n".join(out).rstrip() + "\n"
