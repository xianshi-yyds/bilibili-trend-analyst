
def generate_market_report(creators):
    """
    Generates a comparative market analysis based on the list of creators.
    Returns a dictionary of insights.
    """
    if not creators:
        return {}

    # 1. Audience Analysis (Based on Tags/Titles)
    all_tags = []
    for c in creators:
        # crude extraction from title/desc since we don't always have clean tags
        text = (c.get('latest_video_title', '') + c.get('intro', '')).lower()
        if '教程' in text or '入门' in text: all_tags.append('新手/小白')
        if '实战' in text or '进阶' in text: all_tags.append('从业者/进阶')
        if '测评' in text: all_tags.append('消费决策者')
        if '搞笑' in text or '整活' in text: all_tags.append('泛娱乐用户')
    
    audience_summary = "多元化"
    if all_tags:
        from collections import Counter
        top_audience = Counter(all_tags).most_common(2)
        audience_summary = " & ".join([t[0] for t in top_audience])

    # 2. Top Performer
    valid_creators = [c for c in creators if isinstance(c.get('avg_views'), (int, float))]
    top_creator = max(valid_creators, key=lambda x: x['avg_views']) if valid_creators else None
    
    # 3. Pros/Cons & Positioning (Rule-based)
    detailed_analysis = []
    for c in creators:
        views = c.get('avg_views', 0)
        freq = c.get('weekly_freq', 0)
        
        # Positioning
        title = c.get('latest_video_title', '')
        if '教程' in title: pos = "干货教学"
        elif '盘点' in title: pos = "资源整合"
        else: pos = "垂直领域"
        
        # Pros/Cons
        pros = []
        cons = []
        if views > 100000: pros.append("流量爆发力强")
        elif views > 10000: pros.append("垂直粘性高")
        
        if freq >= 1: pros.append("更新稳定")
        else: cons.append("更新频率低")
        
        if not pros: pros.append("潜力新星")
        if not cons: cons.append("近期表现平稳")

        detailed_analysis.append({
            "mid": c['mid'],
            "positioning": pos,
            "pros": pros,
            "cons": cons,
            "target_audience": "相关兴趣人群" # Placeholder logic
        })

    return {
        "audience_summary": audience_summary,
        "top_performer": top_creator['author'] if top_creator else "N/A",
        "market_gap": "目前头部内容集中在基础教学，进阶实战内容相对稀缺，存在差异化机会。", # Fixed insight for now
        "details": {d['mid']: d for d in detailed_analysis}
    }
