# app/services/chat_service.py - 다중 검색 패턴 확장 버전
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import json
import os
import random
import re
import asyncio
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

from app.models.conversation import Conversation  
from app.models.festival import Festival
from app.utils.openai_client import chat_with_gpt, chat_with_gpt_stream
from app.utils.prompts import (
    KPOP_FESTIVAL_QUICK_PROMPT,
    KPOP_ATTRACTION_QUICK_PROMPT,
    COMPARISON_PROMPT,
    ADVICE_PROMPT,
    RESTAURANT_QUICK_PROMPT,
    RESTAURANT_COMPARISON_PROMPT,
    RESTAURANT_ADVICE_PROMPT,
    KCONTENT_QUICK_PROMPT,
    KCONTENT_COMPARISON_PROMPT,
    KCONTENT_ADVICE_PROMPT
)

class ChatService:
    
    # 🎯 설정값들
    QDRANT_URL = os.getenv("QDRANT_URL", "http://172.17.0.1:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    
    COLLECTION_NAME = "seoul-festival"
    ATTRACTION_COLLECTION = "seoul-attraction"
    RESTAURANT_COLLECTION = "seoul-restaurant"
    KCONTENT_COLLECTION = "seoul-kcontents"  # 🎬 K-Content 추가
    
    # 🚀 캐싱된 인스턴스들
    _embedding_model = None
    _qdrant_client = None
    
    @staticmethod
    def _get_embedding_model():
        """임베딩 모델 싱글톤"""
        if ChatService._embedding_model is None:
            ChatService._embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")
        return ChatService._embedding_model
    
    @staticmethod
    def _get_qdrant_client():
        """Qdrant 클라이언트 싱글톤"""
        if ChatService._qdrant_client is None:
            if ChatService.QDRANT_API_KEY:
                ChatService._qdrant_client = QdrantClient(
                    url=ChatService.QDRANT_URL,
                    api_key=ChatService.QDRANT_API_KEY,
                    timeout=60,
                    prefer_grpc=False
                )
                print(f"✅ Qdrant Cloud 연결: {ChatService.QDRANT_URL}")
            else:
                ChatService._qdrant_client = QdrantClient(
                    url=ChatService.QDRANT_URL,
                    timeout=60,
                    prefer_grpc=False
                )
                print(f"✅ Qdrant Local 연결: {ChatService.QDRANT_URL}")
        return ChatService._qdrant_client
    
    # ===== 통합된 검색어 처리 함수들 =====
    
    @staticmethod
    def _process_search_query(query: str, search_type: str = "attraction") -> str:
        """통합 검색어 처리 (전처리 + 정규화) - K-Content 포함"""
        
        # 1. 불용어 제거 (더 제한적으로)
        stopwords = {"a", "an", "the", "me", "to", "introduce"}  # 🔧 줄임
        words = [w for w in query.lower().split() if w not in stopwords]
        cleaned_query = " ".join(words) if words else query
        
        # 2. 검색어 정규화 (타입별 보정 규칙)
        if search_type == "kcontent":
            # K-Drama/K-Content 특화 보정
            corrections = {
                "crash landing on you": "사랑의 불시착",
                "itaewon class": "이태원 클라쓰",
                "kingdom": "킹덤",
                "goblin": "도깨비",
                "descendants of the sun": "태양의 후예",
                "my love from the star": "별에서 온 그대",
                "mom's friend's son": "엄마친구아들",
                "filming location": "촬영지",
                "drama location": "드라마 촬영지",
                "kdrama": "한국 드라마",
                "k-drama": "한국 드라마",
                "divorce insurance": "이혼보험",  # 🆕 추가
            }
        else:
            # 일반 관광지/레스토랑 보정
            corrections = {
                "namsan tower": "namsan seoul tower",
                "n tower": "namsan seoul tower", 
                "seoul tower": "namsan seoul tower",
                "63 building": "63빌딩",
                "lotte tower": "lotte world tower",
                "dongdaemun": "dongdaemun design plaza",
                "myeongdong": "myeongdong shopping street",
                "gangnam": "gangnam district",
                "hongdae": "hongik university area",
                "bukchon": "bukchon hanok village",
                "insadong": "insadong cultural street",
                "itaewon": "itaewon global village",
                "korean bbq": "korean barbecue",
                "korean food": "korean restaurant",
                "chinese food": "chinese restaurant",
                "japanese food": "japanese restaurant",
                "hongdae food": "hongik university restaurant",
                "gangnam food": "gangnam district restaurant",
                "myeongdong food": "myeongdong restaurant",
            }
        
        query_lower = cleaned_query.lower()
        for wrong, correct in corrections.items():
            if wrong in query_lower:
                cleaned_query = cleaned_query.replace(wrong, correct)
                print(f"🔧 검색어 보정: '{wrong}' → '{correct}'")
        
        return cleaned_query
    
    @staticmethod
    def _expand_search_terms(query: str, search_type: str = "attraction") -> List[str]:
        """검색어 확장 (타입별 변형)"""
        variants = [query]
        query_lower = query.lower()
        
        if search_type == "kcontent":
            # K-Content 전용 확장
            if "filming" in query_lower or "location" in query_lower:
                variants.append(query.replace("filming location", "촬영지"))
                variants.append(query.replace("location", "장소"))
            if "drama" in query_lower:
                variants.append(query.replace("drama", "드라마"))
        else:
            # 일반 관광지/레스토랑 확장
            if "seoul" not in query_lower and len(query.split()) <= 2:
                variants.extend([f"{query} seoul", f"seoul {query}"])
            
            translations = {
                "tower": "타워", "palace": "궁", "temple": "사", 
                "market": "시장", "park": "공원", "restaurant": "맛집", "food": "음식"
            }
            
            for english, korean in translations.items():
                if english in query_lower:
                    variants.append(query.replace(english, korean).replace(english.title(), korean))
        
        return list(set(variants))
    
    @staticmethod
    def _calculate_keyword_overlap(query: str, title: str) -> float:
        """키워드 겹치는 정도 계산"""
        query_words = set(query.lower().split())
        title_words = set(title.lower().split())
        
        overlap = len(query_words & title_words)
        total = len(query_words | title_words)
        
        return overlap / total if total > 0 else 0
    
    @staticmethod
    def _improved_search(query: str, search_type: str = "attraction") -> Optional[Dict]:
        """개선된 통합 검색 로직 (K-Content 포함)"""
        try:
            print(f"🔍 개선된 검색 시작: '{query}' (타입: {search_type})")
            
            # 1. 쿼리 처리 (타입별)
            cleaned_query = ChatService._process_search_query(query, search_type)
            
            # 2. 검색어 확장 (타입별)
            search_variants = ChatService._expand_search_terms(cleaned_query, search_type)
            print(f"🔧 검색 변형들: {search_variants}")
            
            # 3. 모든 변형으로 검색
            best_result = None
            best_score = 0
            
            qdrant_client = ChatService._get_qdrant_client()
            embedding_model = ChatService._get_embedding_model()
            
            # 컬렉션 선택
            collections = {
                "restaurant": ChatService.RESTAURANT_COLLECTION,
                "attraction": ChatService.ATTRACTION_COLLECTION,
                "festival": ChatService.COLLECTION_NAME,
                "kcontent": ChatService.KCONTENT_COLLECTION  # 🎬 K-Content 추가
            }
            collection_name = collections.get(search_type, ChatService.COLLECTION_NAME)
            
            for variant in search_variants:
                try:
                    query_embedding = embedding_model.embed_query(variant)
                    
                    search_results = qdrant_client.search(
                        collection_name=collection_name,
                        query_vector=query_embedding,
                        limit=5,
                        score_threshold=0.3,
                        with_payload=True,
                        with_vectors=False
                    )
                    
                    for result in search_results:
                        vector_score = result.score
                        
                        # 타입별 제목 추출 (K-Content 필드명 매핑)
                        if search_type == "restaurant":
                            title = result.payload.get("metadata", {}).get("name", "")
                        elif search_type == "kcontent":
                            metadata = result.payload.get("metadata", {})
                            drama_name = metadata.get("drama_name_ko", "")  # 🔄 변경
                            location_name = metadata.get("location_name_en", "")  # 🔄 변경
                            title = f"{drama_name} {location_name}"
                        else:
                            title = result.payload.get("metadata", {}).get("title", "")
                            
                        keyword_score = ChatService._calculate_keyword_overlap(cleaned_query, title)
                        combined_score = vector_score * 0.8 + keyword_score * 0.2
                        
                        if combined_score > best_score:
                            best_score = combined_score
                            best_result = result
                            print(f"✅ 더 좋은 결과: '{variant}' → 점수: {combined_score:.3f}")
                
                except Exception as e:
                    print(f"⚠️ 변형 '{variant}' 검색 실패: {e}")
                    continue
            
            # 결과 반환 (K-Content는 임계값 0.4, 나머지는 0.5)
            threshold = 0.4 if search_type == "kcontent" else 0.5
            if best_result and best_score > threshold:
                return best_result
            else:
                print(f"❌ 유효한 결과 없음 (최고 점수: {best_score:.3f})")
                return None
                
        except Exception as e:
            print(f"❌ 개선된 검색 오류: {e}")
            import traceback
            traceback.print_exc()
            return None

    # ===== 🆕 다중 K-Content 검색 함수 =====
    
    @staticmethod
    def _search_multiple_kcontent(keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """🆕 K-Content 다중 검색 - 카드 형태 출력용"""
        try:
            print(f"🔍 다중 K-Content 검색 시작: '{keyword}' (최대 {limit}개)")
            
            # 1. 쿼리 처리
            cleaned_query = ChatService._process_search_query(keyword, "kcontent")
            search_variants = ChatService._expand_search_terms(cleaned_query, "kcontent")
            print(f"🔧 검색 변형들: {search_variants}")
            
            # 2. 모든 매칭 결과 수집
            all_results = []
            seen_content_ids = set()  # 중복 제거용
            
            qdrant_client = ChatService._get_qdrant_client()
            embedding_model = ChatService._get_embedding_model()
            
            for variant in search_variants:
                try:
                    query_embedding = embedding_model.embed_query(variant)
                    
                    search_results = qdrant_client.search(
                        collection_name=ChatService.KCONTENT_COLLECTION,
                        query_vector=query_embedding,
                        limit=30,  # 더 많이 가져와서 선별
                        score_threshold=0.3,
                        with_payload=True,
                        with_vectors=False
                    )
                    
                    for result in search_results:
                        metadata = result.payload.get("metadata", {})
                        content_id = metadata.get("content_id", "")
                        
                        # 중복 제거
                        if content_id in seen_content_ids:
                            continue
                        seen_content_ids.add(content_id)
                        
                        # 드라마명 매칭 체크
                        drama_name_ko = metadata.get("drama_name_ko", "")
                        drama_name_en = metadata.get("drama_name_en", "")
                        location_name = metadata.get("location_name_en", "")
                        title = f"{drama_name_ko} {location_name}"
                        
                        vector_score = result.score
                        keyword_score = ChatService._calculate_keyword_overlap(cleaned_query, title)
                        combined_score = vector_score * 0.8 + keyword_score * 0.2
                        
                        # 임계값 통과한 결과만 포함
                        if combined_score > 0.35:  # 다중 검색은 조금 낮은 임계값
                            # 🎨 카드 형태 데이터 생성
                            card_data = {
                                "content_id": content_id,
                                "location_name": location_name,
                                "category": metadata.get("category_en", ""),
                                "thumbnail": metadata.get("thumbnail", ""),
                                "drama_name": drama_name_ko,
                                "drama_name_en": drama_name_en,
                                "latitude": float(metadata.get("latitude", 0)),
                                "longitude": float(metadata.get("longitude", 0)),
                                "similarity_score": combined_score,
                                "type": "kcontent"
                            }
                            all_results.append(card_data)
                            print(f"✅ 추가: {location_name} ({drama_name_ko}) - 점수: {combined_score:.3f}")
                
                except Exception as e:
                    print(f"⚠️ 변형 '{variant}' 검색 실패: {e}")
                    continue
            
            # 점수순 정렬 후 상위 limit개 반환
            all_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            final_results = all_results[:limit]
            
            print(f"🎯 최종 {len(final_results)}개 장소 선별 완료")
            return final_results
                
        except Exception as e:
            print(f"❌ 다중 K-Content 검색 오류: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    # ===== 검색 결과 포맷팅 (타입별) =====
    
    @staticmethod
    def _format_search_result(result, search_type: str) -> Dict[str, Any]:
        """검색 결과를 타입별로 포맷팅 (K-Content 포함)"""
        if not result:
            return None
            
        metadata = result.payload.get("metadata", {})
        page_content = result.payload.get("page_content", "")
        
        if search_type == "restaurant":
            return {
                "id": str(metadata.get("restaurant_id", "")),
                "restaurant_name": metadata.get("name", ""),
                "place": metadata.get("place", ""),
                "place_en": metadata.get("place_en", ""),
                "subway": metadata.get("subway", ""),
                "description": page_content[:200] if page_content else "",
                "latitude": float(metadata.get("latitude", 0)),
                "longitude": float(metadata.get("longitude", 0)),
                "similarity_score": result.score,
                "type": "restaurant"
            }
        elif search_type == "festival":
            return {
                "festival_id": metadata.get("festival_id", metadata.get("row")),
                "title": metadata.get("title", ""),
                "filter_type": metadata.get("filter_type", ""), 
                "start_date": metadata.get("start_date", ""),
                "end_date": metadata.get("end_date", ""),
                "image_url": metadata.get("image_url", ""),
                "detail_url": metadata.get("detail_url", ""),
                "latitude": float(metadata.get("latitude", 0)) if metadata.get("latitude") else 0.0,
                "longitude": float(metadata.get("longitude", 0)) if metadata.get("longitude") else 0.0,
                "description": metadata.get("description", ""),
                "similarity_score": result.score,
                "type": "festival"
            }
        elif search_type == "kcontent":
            # 🎬 K-Content 포맷팅 (실제 컬럼명 사용)
            return {
                "content_id": metadata.get("content_id", ""),
                "drama_name": metadata.get("drama_name_ko", ""),  # 🔄 변경
                "drama_name_en": metadata.get("drama_name_en", ""),
                "location_name": metadata.get("location_name_en", ""),  # 🔄 변경
                "address": metadata.get("address_en", ""),  # 🔄 변경
                "trip_tip": metadata.get("trip_tip_en", ""),  # 🔄 trip_tip_en → trip_tip
                "keyword": metadata.get("keyword_en", ""),  # 🔄 변경
                "category": metadata.get("category_en", ""),  # 🔄 변경
                "thumbnail": metadata.get("thumbnail", ""),
                "second_image": metadata.get("second_image", ""),
                "third_image": metadata.get("third_image", ""),
                "latitude": float(metadata.get("latitude", 0)),
                "longitude": float(metadata.get("longitude", 0)),
                "similarity_score": result.score,
                "type": "kcontent"
            }
        else:  # attraction
            return {
                "attr_id": metadata.get("attr_id", ""),
                "title": metadata.get("title", ""),
                "url": metadata.get("url", ""),
                "description": metadata.get("description", ""),
                "phone": metadata.get("phone", ""),
                "hours_of_operation": metadata.get("hours_of_operation", "운영시간 정보 없음"),
                "holidays": metadata.get("holidays", ""),
                "address": metadata.get("address", ""),
                "transportation": metadata.get("transportation", ""),
                "image_urls": metadata.get("image_urls", []),
                "image_count": metadata.get("image_count", 0),
                "latitude": float(metadata.get("latitude", 0)),
                "longitude": float(metadata.get("longitude", 0)),
                "attr_code": metadata.get("attr_code", ""),
                "similarity_score": result.score,
                "type": "attraction"
            }
    
    # ===== 타입별 검색 함수들 =====
    
    @staticmethod
    def _search_best_restaurant(keyword: str) -> Optional[Dict[str, Any]]:
        """레스토랑 검색"""
        result = ChatService._improved_search(keyword, "restaurant")
        return ChatService._format_search_result(result, "restaurant")
    
    @staticmethod
    def _search_best_festival(keyword: str) -> Optional[Dict[str, Any]]:
        """축제 검색"""
        result = ChatService._improved_search(keyword, "festival")
        return ChatService._format_search_result(result, "festival")
    
    @staticmethod
    def _search_best_attraction(keyword: str) -> Optional[Dict[str, Any]]:
        """관광명소 검색"""
        result = ChatService._improved_search(keyword, "attraction")
        return ChatService._format_search_result(result, "attraction")
    
    @staticmethod
    def _search_best_kcontent(keyword: str) -> Optional[Dict[str, Any]]:
        """🎬 K-Content 검색"""
        result = ChatService._improved_search(keyword, "kcontent")
        return ChatService._format_search_result(result, "kcontent")
    
    # ===== 메시지 분석 =====
    
    @staticmethod
    def _analyze_message_fast(message: str, is_kcontent_mode: bool = False) -> Dict[str, Any]:
        """메시지 분석 (🔧 더 넓은 다중 검색 패턴)"""
        message_lower = message.lower().strip()
        print(f"\n🔍 질문 분석 시작: '{message}' (K-Content모드: {is_kcontent_mode})")
        
        # 수량 추출
        number_patterns = [r'(\d+)곳', r'(\d+)개', r'(\d+)가지', r'(\d+)\s*places?', r'(\d+)\s*spots?', r'(\d+)\s*locations?']
        extracted_count = None
        for pattern in number_patterns:
            match = re.search(pattern, message_lower)
            if match:
                extracted_count = int(match.group(1))
                print(f"   ✅ 수량 발견: {extracted_count}개")
                break
        
        # 🆕 더 넓은 다중 검색 패턴 감지
        multiple_patterns = [
            'places that appeared', 'locations that appeared', 'places from',
            'all places', 'all locations', 'filming locations',
            'places in', 'locations in', 'where', 'appeared',
            'show me', 'tell me where', 'what are the places',
            'places of', 'locations of', 'spots from', 'spots in',
            '모든 장소', '전체 촬영지', '나온 장소', '등장한 장소', '촬영 장소들',
            'drama', 'divorce insurance', 'places'  # 🔧 더 추가
        ]
        
        has_multiple_intent = any(pattern in message_lower for pattern in multiple_patterns)
        
        # 🔧 드라마 관련 키워드 체크
        drama_keywords = ['drama', 'divorce insurance', "mom's friend's son", 'appeared', 'filming', 'locations', 'places']
        has_drama = any(kw in message_lower for kw in drama_keywords)
        
        # 🎯 K-Content 모드이거나 드라마 관련이면 다중 검색 허용
        if has_multiple_intent and (is_kcontent_mode or has_drama):
            keyword = ChatService._extract_keyword_simple(message)
            print(f"🎬 다중 검색 트리거! 키워드: '{keyword}'")
            return {"type": "multiple_kcontent_search", "keyword": keyword, "count": extracted_count or 20}
        
        # 비교 질문 감지
        comparison_patterns = [' vs ', 'vs.', ' versus ', 'which one', 'which is better', 'compare']
        if any(p in message_lower for p in comparison_patterns):
            return {"type": "comparison", "keyword": message, "count": extracted_count}
        
        # 조언/팁 질문 감지
        advice_patterns = ['tip', 'tips', 'advice', '팁', '조언', 'how to', '어떻게', '방법', 'what should i know', '알아야', '준비', 'etiquette', '에티켓']
        
        if is_kcontent_mode:
            # K-Content 모드: 드라마 관련 키워드 체크
            drama_keywords = ['drama', 'filming', 'location', 'scene', '드라마', '촬영지', '장면', '장소']
            has_drama = any(kw in message_lower for kw in drama_keywords)
            has_advice = any(kw in message_lower for kw in advice_patterns)
            
            if has_advice and not has_drama:
                return {"type": "general_advice", "keyword": message, "count": extracted_count}
        else:
            # 일반 모드: 장소 관련 키워드 체크
            place_keywords = ['palace', 'temple', 'tower', 'museum', 'park', '궁', '사찰', '타워', '박물관', '공원', 'gangnam', 'hongdae', 'myeongdong', 'itaewon', 'culture', '문화', 'transportation', '교통', 'weather', '날씨']
            has_advice = any(kw in message_lower for kw in advice_patterns)
            has_place = any(place in message_lower for place in place_keywords)
            
            if has_advice and not has_place:
                return {"type": "general_advice", "keyword": message, "count": extracted_count}
        
        # 추천 질문 감지
        recommendation_patterns = ['recommend', 'suggestion', 'suggest', '추천', 'places to visit', 'where to go', '가볼', 'best places', 'top places', '명소', 'best', 'top', 'popular', '인기']
        has_recommendation = any(kw in message_lower for kw in recommendation_patterns)
        
        if has_recommendation or extracted_count:
            return {"type": "recommendation", "keyword": message, "count": extracted_count or 10}
        
        # 기본 검색
        keyword = ChatService._extract_keyword_simple(message)
        search_type = "kcontent_search" if is_kcontent_mode else "place_search"
        return {"type": search_type, "keyword": keyword, "count": extracted_count}
    
    @staticmethod
    def _extract_keyword_simple(message: str) -> str:
        """키워드 추출 (더 보수적으로)"""
        remove_words = [
            'introduce', 'introduco', 'tell me about', 'what is', 'where is', 'about', 
            'where', 'are'  # 🔧 핵심 단어는 유지
        ]
        keyword = message.lower()
        for word in remove_words:
            keyword = keyword.replace(word, '')
        keyword = ' '.join(keyword.split())
        return keyword.strip() if len(keyword.strip()) >= 2 else message
    
    @staticmethod
    def _is_restaurant_query(message: str) -> bool:
        """레스토랑 관련 질문 판단"""
        restaurant_keywords = ['restaurant', 'food', 'eat', 'dining', 'meal', 'cuisine', 'dish', '레스토랑', '음식', '먹', '식당', '맛집', '요리', '음식점']
        return any(keyword in message.lower() for keyword in restaurant_keywords)
    
    # ===== 지도 마커 =====
    
    @staticmethod
    def _create_markers(results_data: List[Dict]) -> List[Dict]:
        """지도 마커 생성 (통합 - K-Content 포함)"""
        markers = []
        for item in results_data:
            if not item:
                continue
            lat, lng = item.get('latitude', 0.0), item.get('longitude', 0.0)
            
            if lat and lng and lat != 0.0 and lng != 0.0:
                item_type = item.get('type', 'attraction')
                
                # 기본 마커 정보
                marker = {
                    "id": item.get('festival_id') or item.get('attr_id') or item.get('content_id') or item.get('id'),
                    "latitude": float(lat),
                    "longitude": float(lng),
                    "type": item_type
                }
                
                # 타입별 추가 정보 (K-Content 필드명 매핑)
                if item_type == 'restaurant':
                    marker.update({
                        "title": item.get('restaurant_name', ''),
                        "restaurant_id": item.get('id'),
                        "description": item.get('description', ''),
                        "place": item.get('place', ''),
                        "subway": item.get('subway', '')
                    })
                elif item_type == 'festival':
                    marker.update({
                        "title": item.get('title', ''),
                        "festival_id": item['festival_id'],
                        "description": item.get('description', '')[:100] + "...",
                        "image_url": item.get('image_url'),
                        "start_date": item.get('start_date'),
                        "end_date": item.get('end_date')
                    })
                elif item_type == 'kcontent':
                    # 🎬 K-Content 마커 (필드명 매핑)
                    marker.update({
                        "title": f"{item.get('drama_name')} - {item.get('location_name')}",
                        "content_id": item.get('content_id'),
                        "drama_name": item.get('drama_name'),
                        "location_name": item.get('location_name'),
                        "address": item.get('address'),
                        "thumbnail": item.get('thumbnail'),
                        "trip_tip": item.get('trip_tip', '')[:100] + "..." if item.get('trip_tip') else ""
                    })
                else:  # attraction
                    marker.update({
                        "title": item.get('title', ''),
                        "attr_id": item.get('attr_id'),
                        "address": item.get('address'),
                        "phone": item.get('phone'),
                        "image_urls": item.get('image_urls')
                    })
                
                markers.append(marker)
        
        return markers
    
    # ===== 랜덤 추천 =====
    
    @staticmethod
    def _get_random_attractions(count: int = 10) -> List[Dict[str, Any]]:
        """랜덤 관광명소 추천"""
        try:
            print(f"🎲 랜덤 관광명소 {count}개 추천 시작...")
            
            qdrant_client = ChatService._get_qdrant_client()
            fetch_count = min(count * 5, 100)
            
            scroll_result = qdrant_client.scroll(
                collection_name=ChatService.ATTRACTION_COLLECTION,
                limit=fetch_count,
                offset=random.randint(0, 50),
                with_payload=True,
                with_vectors=False
            )
            
            points = scroll_result[0]
            if not points:
                return []
            
            random.shuffle(points)
            selected_points = points[:count]
            
            attractions = []
            for point in selected_points:
                attraction_data = point.payload.get("metadata", {})
                formatted_data = {
                    "attr_id": attraction_data.get("attr_id"),
                    "title": attraction_data.get("title"),
                    "latitude": float(attraction_data.get("latitude", 0)),
                    "longitude": float(attraction_data.get("longitude", 0)),
                    "type": "attraction"
                }
                attractions.append(formatted_data)
            
            return attractions
            
        except Exception as e:
            print(f"❌ 랜덤 추천 오류: {e}")
            return []
    
    @staticmethod
    def _get_random_kcontents(count: int = 10) -> List[Dict[str, Any]]:
        """🎬 랜덤 K-Content 추천"""
        try:
            print(f"🎲 랜덤 K-Content {count}개 추천 시작...")
            
            qdrant_client = ChatService._get_qdrant_client()
            fetch_count = min(count * 5, 100)
            
            scroll_result = qdrant_client.scroll(
                collection_name=ChatService.KCONTENT_COLLECTION,
                limit=fetch_count,
                offset=random.randint(0, 50),
                with_payload=True,
                with_vectors=False
            )
            
            points = scroll_result[0]
            if not points:
                return []
            
            random.shuffle(points)
            selected_points = points[:count]
            
            kcontents = []
            for point in selected_points:
                kcontent_metadata = point.payload.get("metadata", {})
                formatted_data = {
                    "content_id": kcontent_metadata.get("content_id"),
                    "drama_name": kcontent_metadata.get("drama_name_ko"),  # 🔄 변경
                    "location_name": kcontent_metadata.get("location_name_en"),  # 🔄 변경
                    "thumbnail": kcontent_metadata.get("thumbnail", ""),
                    "latitude": float(kcontent_metadata.get("latitude", 0)),
                    "longitude": float(kcontent_metadata.get("longitude", 0)),
                    "type": "kcontent"
                }
                kcontents.append(formatted_data)
            
            return kcontents
            
        except Exception as e:
            print(f"❌ 랜덤 K-Content 추천 오류: {e}")
            return []
    
    @staticmethod
    def _generate_random_response(items: List[Dict], is_kcontent: bool = False) -> str:
        """랜덤 추천 응답 생성"""
        if not items:
            if is_kcontent:
                return "Sorry, I couldn't find any K-Drama locations at the moment. 😢"
            return "Hey Hunters! 😅 지금 추천할 미션 장소가 없네... 다시 검색해볼게! 🔥"
        
        if is_kcontent:
            return f"🎬 OMG! Here are {len(items)} amazing K-Drama filming locations in Seoul! Each spot is iconic and perfect for K-Drama fans! Ask me about any specific location for more details! 💕✨"
        return f"Yo! Hunters! 🔥💫 엄선한 {len(items)}개의 전설적인 장소들이야! 각 장소마다 특별한 빛의 에너지가 있으니까 직접 체크해봐! 궁금한 곳 있으면 말해줘! Let's explore! 🌙✨"
    
    # ===== 메인 API 함수 (스트리밍 전용) =====
    
    @staticmethod
    async def send_message_streaming(db: Session, user_id: int, message: str, is_kcontent_mode: bool = False):
        """스트리밍 메시지 처리 (다중 검색 기능 추가)"""
        try:
            # 분석
            analysis = ChatService._analyze_message_fast(message, is_kcontent_mode)
            question_type = analysis.get('type', 'place_search')
            keyword = analysis.get('keyword', message)
            is_restaurant_query = ChatService._is_restaurant_query(message)
            
            print(f"📋 스트리밍 분석: type={question_type}, keyword={keyword}, kcontent={is_kcontent_mode}, restaurant={is_restaurant_query}")
            
            # 🎬 K-Content 모드 처리
            if is_kcontent_mode:
                # 🆕 다중 검색 처리
                if question_type == "multiple_kcontent_search":
                    yield f"data: {json.dumps({'type': 'searching', 'message': '🔍 Finding all filming locations from this drama...'}, ensure_ascii=False)}\n\n"
                    
                    count = analysis.get('count', 20)
                    multiple_kcontents = ChatService._search_multiple_kcontent(keyword, count)
                    
                    if not multiple_kcontents:
                        yield f"data: {json.dumps({'type': 'error', 'message': 'Sorry, I could not find locations for this drama. 😅'}, ensure_ascii=False)}\n\n"
                        return
                    
                    # AI 응답 생성
                    ai_response = f"🎬 Amazing! I found {len(multiple_kcontents)} filming locations from this drama! Each place has its own special story. Tap any location card below for detailed information! 💕✨"
                    
                    # 대화 저장
                    conversation = Conversation(user_id=user_id, question=message, response=ai_response)
                    db.add(conversation)
                    db.commit()
                    db.refresh(conversation)
                    
                    # 🎨 카드 형태 데이터 준비
                    location_cards = []
                    for location in multiple_kcontents:
                        card = {
                            "content_id": location.get('content_id'),
                            "location_name": location.get('location_name'),      # 📍 장소명
                            "category": location.get('category'),                # 🏷️ 카테고리  
                            "thumbnail": location.get('thumbnail'),              # 🖼️ 썸네일
                            "drama_name": location.get('drama_name'),
                            "clickable": True                                    # 클릭 가능 표시
                        }
                        location_cards.append(card)
                    
                    # 지도 마커 생성
                    map_markers = []
                    for location in multiple_kcontents:
                        if location.get('latitude') and location.get('longitude'):
                            marker = {
                                "id": location.get('content_id'),
                                "latitude": location.get('latitude'),
                                "longitude": location.get('longitude'),
                                "title": location.get('location_name'),
                                "category": location.get('category'),
                                "type": "kcontent"
                            }
                            map_markers.append(marker)
                    
                    # 🎯 최종 응답
                    completion_data = {
                        'type': 'multiple_locations',               # 🆕 새로운 응답 타입
                        'full_response': ai_response,
                        'convers_id': conversation.convers_id,
                        'location_cards': location_cards,           # 🎨 카드 데이터 배열
                        'total_count': len(multiple_kcontents),
                        'drama_name': multiple_kcontents[0].get('drama_name') if multiple_kcontents else '',
                        'has_kcontents': True,
                        'map_markers': map_markers
                    }
                    
                    yield f"data: {json.dumps(completion_data, ensure_ascii=False)}\n\n"
                    return
                
                # 비교 질문
                elif question_type == "comparison":
                    yield f"data: {json.dumps({'type': 'generating', 'message': '🤔 Comparing K-Drama locations...'}, ensure_ascii=False)}\n\n"
                    
                    prompt = KCONTENT_COMPARISON_PROMPT.format(message=message)
                    full_response = ""
                    for chunk in chat_with_gpt_stream([{"role": "user", "content": prompt}], max_tokens=300, temperature=0.7):
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.02)
                    
                    conversation = Conversation(user_id=user_id, question=message, response=full_response)
                    db.add(conversation)
                    db.commit()
                    db.refresh(conversation)
                    
                    yield f"data: {json.dumps({'type': 'done', 'full_response': full_response, 'convers_id': conversation.convers_id, 'kcontents': [], 'has_kcontents': False}, ensure_ascii=False)}\n\n"
                    return
                
                # 조언 질문
                elif question_type == "general_advice":
                    yield f"data: {json.dumps({'type': 'generating', 'message': '💡 Preparing K-Drama tips...'}, ensure_ascii=False)}\n\n"
                    
                    prompt = KCONTENT_ADVICE_PROMPT.format(message=message)
                    full_response = ""
                    for chunk in chat_with_gpt_stream([{"role": "user", "content": prompt}], max_tokens=350, temperature=0.7):
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.02)
                    
                    conversation = Conversation(user_id=user_id, question=message, response=full_response)
                    db.add(conversation)
                    db.commit()
                    db.refresh(conversation)
                    
                    yield f"data: {json.dumps({'type': 'done', 'full_response': full_response, 'convers_id': conversation.convers_id, 'kcontents': [], 'has_kcontents': False}, ensure_ascii=False)}\n\n"
                    return
                
                # 랜덤 추천
                elif question_type == "recommendation":
                    yield f"data: {json.dumps({'type': 'random', 'message': '🎲 Finding amazing K-Drama locations...'}, ensure_ascii=False)}\n\n"
                    
                    count = analysis.get('count', 10)
                    random_kcontents = ChatService._get_random_kcontents(count)
                    ai_response = ChatService._generate_random_response(random_kcontents, True)
                    
                    conversation = Conversation(user_id=user_id, question=message, response=ai_response)
                    db.add(conversation)
                    db.commit()
                    db.refresh(conversation)
                    
                    map_markers = ChatService._create_markers(random_kcontents)
                    
                    yield f"data: {json.dumps({'type': 'done', 'full_response': ai_response, 'results': random_kcontents, 'kcontents': random_kcontents, 'convers_id': conversation.convers_id, 'has_kcontents': True, 'map_markers': map_markers}, ensure_ascii=False)}\n\n"
                    return
                
                # K-Content 검색
                else:
                    yield f"data: {json.dumps({'type': 'searching', 'message': '🔍 Searching for K-Drama location...'}, ensure_ascii=False)}\n\n"
                    
                    kcontent = ChatService._search_best_kcontent(keyword)
                    
                    if not kcontent:
                        yield f"data: {json.dumps({'type': 'error', 'message': 'Sorry, I could not find that K-Drama location. 😅'}, ensure_ascii=False)}\n\n"
                        return
                    
                    kcontent['type'] = 'kcontent'
                    title = f"{kcontent['drama_name']} - {kcontent['location_name']}"
                    
                    yield f"data: {json.dumps({'type': 'found', 'title': title, 'result': kcontent}, ensure_ascii=False)}\n\n"
                    yield f"data: {json.dumps({'type': 'generating', 'message': '🎬 Preparing K-Drama info...'}, ensure_ascii=False)}\n\n"
                    
                    prompt = KCONTENT_QUICK_PROMPT.format(
                        drama_name=kcontent.get('drama_name', ''),
                        location_name=kcontent.get('location_name', ''),
                        address=kcontent.get('address', ''),
                        trip_tip=kcontent.get('trip_tip', '')[:500],
                        keyword=kcontent.get('keyword', ''),
                        message=message
                    )
                    
                    full_response = ""
                    for chunk in chat_with_gpt_stream([{"role": "user", "content": prompt}], max_tokens=250, temperature=0.6):
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.02)
                    
                    conversation = Conversation(user_id=user_id, question=message, response=full_response)
                    db.add(conversation)
                    db.commit()
                    db.refresh(conversation)
                    
                    map_markers = ChatService._create_markers([kcontent])
                    
                    completion_data = {
                        'type': 'done',
                        'full_response': full_response,
                        'convers_id': conversation.convers_id,
                        'result': kcontent,
                        'results': [kcontent],
                        'kcontents': [kcontent],
                        'has_kcontents': True,
                        'map_markers': map_markers
                    }
                    
                    yield f"data: {json.dumps(completion_data, ensure_ascii=False)}\n\n"
                    return
            
            # 🎤 일반 모드에서도 다중 검색 허용
            elif question_type == "multiple_kcontent_search":
                yield f"data: {json.dumps({'type': 'searching', 'message': '🔍 Finding all filming locations from this drama...'}, ensure_ascii=False)}\n\n"
                
                count = analysis.get('count', 20)
                multiple_kcontents = ChatService._search_multiple_kcontent(keyword, count)
                
                if not multiple_kcontents:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Sorry, I could not find locations for this drama. 😅'}, ensure_ascii=False)}\n\n"
                    return
                
                # AI 응답 생성
                ai_response = f"🎬 Amazing! I found {len(multiple_kcontents)} filming locations from this drama! Each place has its own special story. Tap any location card below for detailed information! 💕✨"
                
                # 대화 저장
                conversation = Conversation(user_id=user_id, question=message, response=ai_response)
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                
                # 🎨 카드 형태 데이터 준비
                location_cards = []
                for location in multiple_kcontents:
                    card = {
                        "content_id": location.get('content_id'),
                        "location_name": location.get('location_name'),      # 📍 장소명
                        "category": location.get('category'),                # 🏷️ 카테고리  
                        "thumbnail": location.get('thumbnail'),              # 🖼️ 썸네일
                        "drama_name": location.get('drama_name'),
                        "clickable": True                                    # 클릭 가능 표시
                    }
                    location_cards.append(card)
                
                # 지도 마커 생성
                map_markers = []
                for location in multiple_kcontents:
                    if location.get('latitude') and location.get('longitude'):
                        marker = {
                            "id": location.get('content_id'),
                            "latitude": location.get('latitude'),
                            "longitude": location.get('longitude'),
                            "title": location.get('location_name'),
                            "category": location.get('category'),
                            "type": "kcontent"
                        }
                        map_markers.append(marker)
                
                # 🎯 최종 응답
                completion_data = {
                    'type': 'multiple_locations',               # 🆕 새로운 응답 타입
                    'full_response': ai_response,
                    'convers_id': conversation.convers_id,
                    'location_cards': location_cards,           # 🎨 카드 데이터 배열
                    'total_count': len(multiple_kcontents),
                    'drama_name': multiple_kcontents[0].get('drama_name') if multiple_kcontents else '',
                    'has_kcontents': True,
                    'map_markers': map_markers
                }
                
                yield f"data: {json.dumps(completion_data, ensure_ascii=False)}\n\n"
                return
            
            # 🎤 일반 모드 처리 (기존 로직)
            # 레스토랑 관련 처리
            if is_restaurant_query:
                if question_type == "comparison":
                    yield f"data: {json.dumps({'type': 'generating', 'message': '🤔 레스토랑 비교 분석 중...'}, ensure_ascii=False)}\n\n"
                    
                    prompt = RESTAURANT_COMPARISON_PROMPT.format(message=message)
                    full_response = ""
                    for chunk in chat_with_gpt_stream([{"role": "user", "content": prompt}], max_tokens=300, temperature=0.7):
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.02)
                    
                    conversation = Conversation(user_id=user_id, question=message, response=full_response)
                    db.add(conversation)
                    db.commit()
                    db.refresh(conversation)
                    
                    yield f"data: {json.dumps({'type': 'done', 'full_response': full_response, 'convers_id': conversation.convers_id, 'results': [], 'festivals': [], 'attractions': [], 'restaurants': [], 'has_festivals': False, 'has_attractions': False, 'has_restaurants': False}, ensure_ascii=False)}\n\n"
                    return
                
                elif question_type == "general_advice":
                    yield f"data: {json.dumps({'type': 'generating', 'message': '💡 음식 문화 팁 준비 중...'}, ensure_ascii=False)}\n\n"
                    
                    prompt = RESTAURANT_ADVICE_PROMPT.format(message=message)
                    full_response = ""
                    for chunk in chat_with_gpt_stream([{"role": "user", "content": prompt}], max_tokens=350, temperature=0.7):
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.02)
                    
                    conversation = Conversation(user_id=user_id, question=message, response=full_response)
                    db.add(conversation)
                    db.commit()
                    db.refresh(conversation)
                    
                    yield f"data: {json.dumps({'type': 'done', 'full_response': full_response, 'convers_id': conversation.convers_id, 'results': [], 'festivals': [], 'attractions': [], 'restaurants': [], 'has_festivals': False, 'has_attractions': False, 'has_restaurants': False}, ensure_ascii=False)}\n\n"
                    return
                
                else:
                    # 레스토랑 검색
                    yield f"data: {json.dumps({'type': 'searching', 'message': '🔍 맛집을 찾고 있어요...'}, ensure_ascii=False)}\n\n"
                    
                    restaurant = ChatService._search_best_restaurant(keyword)
                    
                    if not restaurant:
                        yield f"data: {json.dumps({'type': 'error', 'message': 'Hey Hunters! 😅 그 맛집을 찾을 수 없네... 다른 곳을 찾아보자! 🔥'}, ensure_ascii=False)}\n\n"
                        return
                    
                    yield f"data: {json.dumps({'type': 'found', 'title': restaurant['restaurant_name'], 'result': restaurant}, ensure_ascii=False)}\n\n"
                    yield f"data: {json.dumps({'type': 'generating', 'message': '💫 레스토랑 정보 생성 중...'}, ensure_ascii=False)}\n\n"
                    
                    prompt = RESTAURANT_QUICK_PROMPT.format(
                        restaurant_name=restaurant.get('restaurant_name', ''),
                        location=restaurant.get('place', ''),
                        description=restaurant.get('description', ''),
                        message=message
                    )
                    
                    full_response = ""
                    for chunk in chat_with_gpt_stream([{"role": "user", "content": prompt}], max_tokens=250, temperature=0.6):
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.02)
                    
                    conversation = Conversation(user_id=user_id, question=message, response=full_response)
                    db.add(conversation)
                    db.commit()
                    db.refresh(conversation)
                    
                    map_markers = ChatService._create_markers([restaurant])
                    
                    completion_data = {
                        'type': 'done',
                        'full_response': full_response,
                        'convers_id': conversation.convers_id,
                        'result': restaurant,
                        'results': [restaurant],
                        'festivals': [],
                        'attractions': [],
                        'restaurants': [restaurant],
                        'has_festivals': False,
                        'has_attractions': False,
                        'has_restaurants': True,
                        'map_markers': map_markers
                    }
                    
                    yield f"data: {json.dumps(completion_data, ensure_ascii=False)}\n\n"
                    return
            
            # 비교 질문 처리
            elif question_type == "comparison":
                yield f"data: {json.dumps({'type': 'generating', 'message': '🤔 비교 분석 중...'}, ensure_ascii=False)}\n\n"
                
                prompt = COMPARISON_PROMPT.format(message=message)
                full_response = ""
                for chunk in chat_with_gpt_stream([{"role": "user", "content": prompt}], max_tokens=300, temperature=0.7):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.02)
                
                conversation = Conversation(user_id=user_id, question=message, response=full_response)
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                
                yield f"data: {json.dumps({'type': 'done', 'full_response': full_response, 'convers_id': conversation.convers_id, 'results': [], 'festivals': [], 'attractions': [], 'restaurants': [], 'has_festivals': False, 'has_attractions': False, 'has_restaurants': False}, ensure_ascii=False)}\n\n"
                return
            
            # 일반 조언 질문 처리
            elif question_type == "general_advice":
                yield f"data: {json.dumps({'type': 'generating', 'message': '💡 여행 팁 준비 중...'}, ensure_ascii=False)}\n\n"
                
                prompt = ADVICE_PROMPT.format(message=message)
                full_response = ""
                for chunk in chat_with_gpt_stream([{"role": "user", "content": prompt}], max_tokens=350, temperature=0.7):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.02)
                
                conversation = Conversation(user_id=user_id, question=message, response=full_response)
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                
                yield f"data: {json.dumps({'type': 'done', 'full_response': full_response, 'convers_id': conversation.convers_id, 'results': [], 'festivals': [], 'attractions': [], 'restaurants': [], 'has_festivals': False, 'has_attractions': False, 'has_restaurants': False}, ensure_ascii=False)}\n\n"
                return
            
            # 랜덤 추천 처리
            elif question_type == "recommendation":
                yield f"data: {json.dumps({'type': 'random', 'message': '🎲 랜덤 추천 준비 중...'}, ensure_ascii=False)}\n\n"
                
                count = analysis.get('count', 10)
                random_attractions = ChatService._get_random_attractions(count)
                ai_response = ChatService._generate_random_response(random_attractions, False)
                
                conversation = Conversation(user_id=user_id, question=message, response=ai_response)
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                
                yield f"data: {json.dumps({'type': 'done', 'full_response': ai_response, 'results': random_attractions, 'attractions': random_attractions, 'convers_id': conversation.convers_id, 'has_festivals': False, 'has_attractions': True, 'has_restaurants': False, 'map_markers': ChatService._create_markers(random_attractions)}, ensure_ascii=False)}\n\n"
                return
            
            # ✅ 일반 장소 검색 (병렬 처리 - K-Content 추가!)
            else:
                yield f"data: {json.dumps({'type': 'searching', 'message': '🔍 정보를 찾고 있어요...'}, ensure_ascii=False)}\n\n"
                
                with ThreadPoolExecutor(max_workers=4) as executor:  # ✅ 3 → 4
                    festival_future = executor.submit(ChatService._search_best_festival, keyword)
                    attraction_future = executor.submit(ChatService._search_best_attraction, keyword)
                    restaurant_future = executor.submit(ChatService._search_best_restaurant, keyword)
                    kcontent_future = executor.submit(ChatService._search_best_kcontent, keyword)  # ✅ 추가
                    
                    festival = festival_future.result()
                    attraction = attraction_future.result()
                    restaurant = restaurant_future.result()
                    kcontent = kcontent_future.result()  # ✅ 추가
                
                results = []
                if festival:
                    festival['type'] = 'festival'
                    results.append(festival)
                if attraction:
                    attraction['type'] = 'attraction'
                    results.append(attraction)
                if restaurant:
                    restaurant['type'] = 'restaurant'
                    results.append(restaurant)
                if kcontent:  # ✅ 추가
                    kcontent['type'] = 'kcontent'
                    results.append(kcontent)
                
                if not results:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Hey Hunters! 😅 그 장소를 찾을 수 없네... 🔥'}, ensure_ascii=False)}\n\n"
                    return
                
                results.sort(key=lambda x: x['similarity_score'], reverse=True)
                result = results[0]
                
                # 🎯 제목 생성 (f-string 중첩 방지)
                if result.get('restaurant_name'):
                    title = result.get('restaurant_name')
                elif result.get('title'):
                    title = result.get('title')
                else:
                    title = f"{result.get('drama_name', 'Unknown')} - {result.get('location_name', 'Unknown')}"
                
                yield f"data: {json.dumps({'type': 'found', 'title': title, 'result': result}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'generating', 'message': '💫 응답하는 중...'}, ensure_ascii=False)}\n\n"
                
                # 프롬프트 생성
                result_type = result.get('type', 'attraction')
                
                if result_type == 'festival':
                    prompt = KPOP_FESTIVAL_QUICK_PROMPT.format(
                        title=result.get('title', ''),
                        start_date=result.get('start_date', ''),
                        end_date=result.get('end_date', ''),
                        description=result.get('description', '')[:500],
                        message=message
                    )
                elif result_type == 'restaurant':
                    prompt = RESTAURANT_QUICK_PROMPT.format(
                        restaurant_name=result.get('restaurant_name', ''),
                        location=result.get('place', ''),
                        description=result.get('description', ''),
                        message=message
                    )
                elif result_type == 'kcontent':  # ✅ 추가
                    prompt = KCONTENT_QUICK_PROMPT.format(
                        drama_name=result.get('drama_name', ''),
                        location_name=result.get('location_name', ''),
                        address=result.get('address', ''),
                        trip_tip=result.get('trip_tip', '')[:500],
                        keyword=result.get('keyword', ''),
                        message=message
                    )
                else:  # attraction
                    prompt = KPOP_ATTRACTION_QUICK_PROMPT.format(
                        title=result.get('title', ''),
                        address=result.get('address', ''),
                        hours_of_operation=result.get('hours_of_operation', '운영시간 정보 없음'),
                        description=result.get('description', '')[:500],
                        message=message
                    )
                
                full_response = ""
                for chunk in chat_with_gpt_stream([{"role": "user", "content": prompt}], max_tokens=250, temperature=0.6):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.02)
                
                conversation = Conversation(user_id=user_id, question=message, response=full_response)
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                
                map_markers = ChatService._create_markers([result])
                
                completion_data = {
                    'type': 'done',
                    'full_response': full_response,
                    'convers_id': conversation.convers_id,
                    'result': result,
                    'results': [result],
                    'festivals': [result] if result_type == 'festival' else [],
                    'attractions': [result] if result_type == 'attraction' else [],
                    'restaurants': [result] if result_type == 'restaurant' else [],
                    'kcontents': [result] if result_type == 'kcontent' else [],  # ✅ 추가
                    'has_festivals': result_type == 'festival',
                    'has_attractions': result_type == 'attraction',
                    'has_restaurants': result_type == 'restaurant',
                    'has_kcontents': result_type == 'kcontent',  # ✅ 추가
                    'map_markers': map_markers
                }
                
                yield f"data: {json.dumps(completion_data, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            print(f"❌ Streaming 오류: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    # ===== 호환성 함수 =====
    
    @staticmethod  
    def send_message(db: Session, user_id: int, message: str, is_kcontent_mode: bool = False) -> Dict[str, Any]:
        """기존 호환성을 위한 동기 wrapper"""
        import asyncio
        
        async def _collect_streaming_result():
            result_data = None
            async for chunk in ChatService.send_message_streaming(db, user_id, message, is_kcontent_mode):
                if '"type": "done"' in chunk or '"type": "multiple_locations"' in chunk:
                    try:
                        data = json.loads(chunk.split('data: ')[1])
                        return data
                    except:
                        pass
            return {"response": "처리 중 오류가 발생했습니다.", "convers_id": None, "results": []}
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(_collect_streaming_result())
    
    @staticmethod
    def get_conversation_history(db: Session, user_id: int, limit: int = 50) -> List[Dict]:
        """대화 히스토리 조회"""
        conversations = db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.datetime.desc()).limit(limit).all()
        
        return [
            {
                "conversation_id": conv.convers_id,
                "message": conv.question,
                "response": conv.response,
                "created_at": conv.datetime.isoformat()
            }
            for conv in reversed(conversations)
        ]
        
        