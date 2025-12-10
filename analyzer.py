def generate_analysis_prompt(video_info, subtitles, comments):
    """
    Constructs a prompt for an LLM to analyze the video content.
    """
    
    prompt = f"""
Please analyze the following Bilibili video data and provide a report.

**Video Info:**
- Title: {video_info.get('title')}
- View Count: {video_info.get('play')}
- Link: https://www.bilibili.com/video/{video_info.get('bvid')}
- Owner: {video_info.get('owner_name')}

**Subtitles (Excerpt):**
{subtitles[:3000] if subtitles else "No subtitles available."} ... (truncated)

**Analysis Tasks:**
1. **Persona**: What is the creator's persona? Why would fans follow them?
2. **Hook**: Analyze the first 5 seconds (from subtitles). What is the hook?
3. **CTA**: How do they ask for likes/follows at the end?
4. **Viral Elements**: Analyze the title and content. Why is this popular?
5. **Script Breakdown**: Briefly outline the script structure.

**Output Format:**
- Return a structured JSON or Markdown list.
"""
    return prompt

def mock_visual_analysis(video_info):
    """
    Placeholder for visual analysis (Cover, Editing).
    Requires Vision API.
    """
    return {
        "Cover Image URL": video_info.get('pic'),
        "Visual Analysis": "Requires passing Cover URL to a Vision LLM to analyze: Main Title, Colors, Fonts, Elements."
    }
