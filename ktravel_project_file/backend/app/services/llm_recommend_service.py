# backend/app/services/llm_recommend_service.py
"""
LLM 기반 추천 강화 서비스

recommend.py의 벡터 기반 추천 결과를 LLM에게 보내서
더 개인화된, 설명이 있는 추천을 생성합니다.
"""

import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI


class LLMRecommendService:
    """
    LLM을 사용하여 추천 결과를 개선하는 서비스
    """
    
    def __init__(self):
        """OpenAI API 클라이언트 초기화"""
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = "gpt-4o-mini"  # 또는 "gpt-4o"
    
    
    def enhance_recommendations(
        self,
        user_bookmarks: List[Dict[str, Any]],
        recommended_items: List[Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]] = None,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        벡터 기반 추천을 LLM으로 재정렬 및 설명 추가
        
        Args:
            user_bookmarks: 사용자가 북마크한 장소 목록
            recommended_items: Qdrant에서 추천한 장소 목록
            user_preferences: 사용자 선호도 정보 (선택)
            top_n: 최종 추천 개수
            
        Returns:
            {
                "recommendations": [
                    {
                        "place_type": 3,
                        "reference_id": 123,
                        "name": "Namsan Tower",
                        "reason": "야경을 좋아하시는 것 같아서...",
                        "score": 0.95,
                        "original_rank": 1,
                        "llm_rank": 1,
                        ...
                    }
                ],
                "summary": "당신은 야경과 전통 건축물을 좋아하시는군요..."
            }
        """
        
        # 1️⃣ LLM에게 보낼 프롬프트 생성
        prompt = self._build_prompt(
            user_bookmarks,
            recommended_items,
            user_preferences,
            top_n
        )
        
        # 2️⃣ LLM 호출
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # 3️⃣ 응답 파싱
            llm_result = json.loads(response.choices[0].message.content)
            
            # 4️⃣ 원본 데이터와 병합
            enhanced = self._merge_with_original(
                llm_result,
                recommended_items
            )
            
            return enhanced
            
        except Exception as e:
            print(f"❌ LLM 추천 강화 실패: {e}")
            # 실패 시 원본 추천 그대로 반환
            return {
                "recommendations": recommended_items[:top_n],
                "summary": "Based on your bookmarked places, here are similar recommendations.",
                "error": str(e)
            }
    
    
    def _get_system_prompt(self) -> str:
        """시스템 프롬프트 정의"""
        return """You are a K-Culture travel expert AI assistant.
Your task is to analyze user's bookmarked places and recommend similar places.

You should:
1. Understand user's preferences from their bookmarks (e.g., likes night views, traditional architecture, cafes)
2. Rank the recommended places based on how well they match user's taste
3. Provide personalized reasons for each recommendation
4. Write a summary of user's travel preferences

Output Format (JSON):
{
    "user_taste_summary": "This user seems to enjoy...",
    "recommendations": [
        {
            "reference_id": 123,
            "rank": 1,
            "reason": "This place offers stunning night views, similar to Namsan Tower you bookmarked",
            "match_score": 0.95
        }
    ]
}

Important:
- Keep reasons concise but specific (max 100 characters)
- Rank by personal preference match, not just similarity score
- Return exactly the requested number of recommendations
- All text should be in English"""
    
    
    def _build_prompt(
        self,
        user_bookmarks: List[Dict],
        recommended_items: List[Dict],
        user_preferences: Optional[Dict],
        top_n: int
    ) -> str:
        """사용자 데이터를 바탕으로 프롬프트 생성"""
        
        # 북마크 요약
        bookmarks_summary = []
        for bm in user_bookmarks[:10]:  # 최근 10개만
            bookmarks_summary.append({
                "name": bm.get("name", "Unknown"),
                "category": bm.get("extra", {}).get("category_en", ""),
                "keyword": bm.get("extra", {}).get("keyword_en", ""),
                "location": bm.get("extra", {}).get("location_name_en", "")
            })
        
        # 추천 후보 요약
        candidates_summary = []
        for idx, item in enumerate(recommended_items[:20]):  # 상위 20개
            candidates_summary.append({
                "rank": idx + 1,
                "reference_id": item.get("reference_id"),
                "name": item.get("name", "Unknown"),
                "category": item.get("category", ""),
                "address": item.get("address", ""),
                "score": item.get("score", 0),
                "extra": {
                    "category_en": item.get("extra", {}).get("category_en", ""),
                    "keyword_en": item.get("extra", {}).get("keyword_en", ""),
                    "location_name_en": item.get("extra", {}).get("location_name_en", "")
                }
            })
        
        prompt = f"""Analyze the user's travel preferences and re-rank recommendations.

User's Bookmarked Places:
{json.dumps(bookmarks_summary, indent=2, ensure_ascii=False)}

Recommended Candidates (from vector similarity):
{json.dumps(candidates_summary, indent=2, ensure_ascii=False)}

Task:
1. Identify user's preferences (what kind of places they like)
2. Re-rank the candidates based on personal taste match
3. Select top {top_n} recommendations
4. Provide specific reasons for each recommendation

Return JSON with:
- user_taste_summary: Brief analysis of user's preferences
- recommendations: Array of top {top_n} places with reference_id, rank, reason, match_score
"""
        
        return prompt
    
    
    def _merge_with_original(
        self,
        llm_result: Dict,
        original_items: List[Dict]
    ) -> Dict[str, Any]:
        """LLM 결과와 원본 데이터 병합"""
        
        # reference_id로 매핑
        id_to_item = {
            item["reference_id"]: item 
            for item in original_items
        }
        
        # LLM 추천 결과에 원본 데이터 병합
        enhanced_recs = []
        for llm_rec in llm_result.get("recommendations", []):
            ref_id = llm_rec["reference_id"]
            
            if ref_id in id_to_item:
                original = id_to_item[ref_id]
                enhanced = {
                    **original,  # 원본 데이터 (name, address, image_url 등)
                    "llm_rank": llm_rec["rank"],
                    "llm_reason": llm_rec["reason"],
                    "llm_match_score": llm_rec.get("match_score", 0),
                    "original_score": original.get("score", 0)
                }
                enhanced_recs.append(enhanced)
        
        return {
            "recommendations": enhanced_recs,
            "user_taste_summary": llm_result.get("user_taste_summary", ""),
            "total_count": len(enhanced_recs)
        }


# ============================================================
# 편의 함수들
# ============================================================

def get_llm_recommendations(
    user_bookmarks: List[Dict],
    qdrant_recommendations: List[Dict],
    top_n: int = 10
) -> Dict[str, Any]:
    """
    LLM 기반 추천 생성 (편의 함수)
    
    Example:
        >>> bookmarks = [{"name": "Namsan Tower", ...}, ...]
        >>> candidates = [{"name": "N Seoul Tower", ...}, ...]
        >>> result = get_llm_recommendations(bookmarks, candidates, top_n=5)
        >>> print(result["recommendations"][0]["llm_reason"])
    """
    service = LLMRecommendService()
    return service.enhance_recommendations(
        user_bookmarks,
        qdrant_recommendations,
        top_n=top_n
    )


# ============================================================
# 간단한 추천 설명 생성 (LLM 없이도 작동)
# ============================================================

def generate_simple_reason(
    user_bookmarks: List[Dict],
    recommended_item: Dict
) -> str:
    """
    LLM 없이 간단한 추천 이유 생성
    (API 비용 절약용 fallback)
    """
    
    # 사용자가 북마크한 카테고리 분석
    bookmarked_categories = set()
    bookmarked_keywords = set()
    
    for bm in user_bookmarks:
        cat = bm.get("extra", {}).get("category_en", "")
        kw = bm.get("extra", {}).get("keyword_en", "")
        if cat:
            bookmarked_categories.add(cat.lower())
        if kw:
            for k in kw.split(","):
                bookmarked_keywords.add(k.strip().lower())
    
    # 추천 아이템의 카테고리/키워드
    rec_category = recommended_item.get("extra", {}).get("category_en", "").lower()
    rec_keywords = recommended_item.get("extra", {}).get("keyword_en", "").lower().split(",")
    rec_keywords = [k.strip() for k in rec_keywords if k.strip()]
    
    # 매칭되는 요소 찾기
    matching_keywords = bookmarked_keywords.intersection(set(rec_keywords))
    
    if rec_category in bookmarked_categories:
        return f"Similar {rec_category} to your bookmarked places"
    elif matching_keywords:
        kw = list(matching_keywords)[0]
        return f"Features {kw} like your favorite spots"
    else:
        return f"Highly rated place similar to your taste"