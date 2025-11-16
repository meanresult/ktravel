# app/services/chat_service.py - 스트리밍 전용 최종 간소화 버전
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
from app.utils.openai_client import chat_with_gpt_stream
from app.utils.prompts import (
    KPOP_FESTIVAL_QUICK_PROMPT,
    KPOP_ATTRACTION_QUICK_PROMPT,
    COMPARISON_PROMPT,
    ADVICE_PROMPT,
    RESTAURANT_QUICK_PROMPT,
    RESTAURANT_COMPARISON_PROMPT,
    RESTAURANT_ADVICE_PROMPT
)

class ChatService:
    
    # 🎯 설정값들
    QDRANT_URL = os.getenv("QDRANT_URL", "http://172.17.0.1:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    
    COLLECTION_NAME = "seoul-festival"
    ATTRACTION_COLLECTION = "seoul-attraction"
    RESTAURANT_COLLECTION = "seoul-restaurant"
    
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
    def _process_search_query(query: str) -> str:
        """통합 검색어 처리 (전처리 + 정규화)"""
        
        # 1. 불용어 제거
        stopwords = {"a", "an", "the", "in", "at", "on", "me", "to", "introduce", "tell", "show", "explain", "describe"}
        words = [w for w in query.lower().split() if w not in stopwords]
        cleaned_query = " ".join(words) if words else query
        
        # 2. 검색어 정규화 (주요 보정 규칙들)
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
    def _expand_search_terms(query: str) -> List[str]:
        """검색어 확장 (한영 변환, 서울 추가 등)"""
        variants = [query]
        query_lower = query.lower()
        
        # 서울 추가
        if "seoul" not in query_lower and len(query.split()) <= 2:
            variants.extend([f"{query} seoul", f"seoul {query}"])
        
        # 한영 변환
        translations = {
            "tower": "타워", "palace": "궁", "temple": "사", 
            "market": "시장", "park": "공원", "restaurant": "맛집", "food": "음식"
        }
        
        for english, korean in translations.items():
            if english in query_lower:
                variants.append(query.replace(english, korean).replace(english.title(), korean))
        
        return list(set(variants))  # 중복 제거
    
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
        """개선된 검색 로직 (기존 기능 완전 유지)"""
        try:
            print(f"🔍 개선된 검색 시작: '{query}' (타입: {search_type})")
            
            # 1. 쿼리 처리
            cleaned_query = ChatService._process_search_query(query)
            
            # 2. 검색어 확장
            search_variants = ChatService._expand_search_terms(cleaned_query)
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
                "festival": ChatService.COLLECTION_NAME
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
                        # Vector 유사도 + 키워드 매칭 점수 (기존 로직 완전 유지)
                        vector_score = result.score
                        
                        if search_type == "restaurant":
                            title = result.payload.get("metadata", {}).get("name", "")
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
            
            # 결과 반환 (기존 임계값 0.5 유지)
            if best_result and best_score > 0.5:
                return best_result
            else:
                print(f"❌ 유효한 결과 없음 (최고 점수: {best_score:.3f})")
                return None
                
        except Exception as e:
            print(f"❌ 개선된 검색 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    # ===== 검색 결과 포맷팅 (타입별) =====
    
    @staticmethod
    def _format_search_result(result, search_type: str) -> Dict[str, Any]:
        """검색 결과를 타입별로 포맷팅"""
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
    
    # ===== 타입별 검색 함수들 (병렬 처리를 위해 개별 유지) =====
    
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
    
    # ===== 메시지 분석 =====
    
    @staticmethod
    def _analyze_message_fast(message: str) -> Dict[str, Any]:
        """메시지 분석 (기존 로직 완전 유지)"""
        message_lower = message.lower().strip()
        print(f"\n🔍 질문 분석 시작: '{message}'")
        
        # 수량 추출
        number_patterns = [r'(\d+)곳', r'(\d+)개', r'(\d+)가지', r'(\d+)\s*places?', r'(\d+)\s*spots?']
        extracted_count = None
        for pattern in number_patterns:
            match = re.search(pattern, message_lower)
            if match:
                extracted_count = int(match.group(1))
                print(f"   ✅ 수량 발견: {extracted_count}개")
                break
        
        # 비교 질문 감지
        comparison_patterns = [' vs ', 'vs.', ' versus ', 'which one', 'which is better']
        if any(p in message_lower for p in comparison_patterns):
            return {"type": "comparison", "keyword": message, "count": extracted_count}
        
        # 조언/팁 질문 감지
        advice_patterns = ['tip', 'tips', 'advice', '팁', '조언', 'how to', '어떻게', '방법', 'culture', '문화', 'transportation', '교통', 'weather', '날씨']
        place_keywords = ['palace', 'temple', 'tower', 'museum', 'park', '궁', '사찰', '타워', '박물관', '공원', 'gangnam', 'hongdae', 'myeongdong', 'itaewon']
        
        has_advice_keyword = any(kw in message_lower for kw in advice_patterns)
        has_place = any(place in message_lower for place in place_keywords)
        
        if has_advice_keyword and not has_place:
            return {"type": "general_advice", "keyword": message, "count": extracted_count}
        
        # 추천 질문 감지
        recommendation_patterns = ['recommend', 'suggestion', 'suggest', '추천', 'places to visit', 'where to go', '가볼', 'best places', 'top places', '명소']
        has_recommendation = any(kw in message_lower for kw in recommendation_patterns)
        
        if has_recommendation or extracted_count:
            return {"type": "recommendation", "keyword": message, "count": extracted_count or 10}
        
        # 기본 장소 검색
        keyword = ChatService._extract_keyword_simple(message)
        return {"type": "place_search", "keyword": keyword, "count": extracted_count}
    
    @staticmethod
    def _extract_keyword_simple(message: str) -> str:
        """키워드 추출"""
        remove_words = ['introduce', 'tell me about', 'what is', 'where is', 'about', 'the', 'a', 'an', 'me']
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
    
    # ===== 지도 마커 및 기타 유틸리티 =====
    
    @staticmethod
    def _create_markers(results_data: List[Dict]) -> List[Dict]:
        """지도 마커 생성 (통합)"""
        markers = []
        for item in results_data:
            if not item:
                continue
            lat, lng = item.get('latitude', 0.0), item.get('longitude', 0.0)
            
            if lat and lng and lat != 0.0 and lng != 0.0:
                marker = {
                    "id": item.get('festival_id') or item.get('attr_id') or item.get('id'),
                    "title": item.get('title') or item.get('restaurant_name', ''),
                    "latitude": float(lat),
                    "longitude": float(lng),
                    "type": item.get('type', 'attraction')
                }
                
                # 타입별 추가 정보
                if item.get('type') == 'restaurant':
                    marker.update({
                        "restaurant_id": item.get('id'),
                        "description": item.get('description', ''),
                        "place": item.get('place', ''),
                        "subway": item.get('subway', '')
                    })
                elif item.get('type') == 'festival':
                    marker.update({
                        "festival_id": item['festival_id'],
                        "description": item.get('description', '')[:100] + "...",
                        "image_url": item.get('image_url'),
                        "start_date": item.get('start_date'),
                        "end_date": item.get('end_date')
                    })
                else:  # attraction
                    marker.update({
                        "attr_id": item.get('attr_id'),
                        "address": item.get('address'),
                        "phone": item.get('phone'),
                        "image_urls": item.get('image_urls')
                    })
                
                markers.append(marker)
        
        return markers
    
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
                print(f"❌ 관광명소를 가져올 수 없습니다")
                return []
            
            print(f"📊 가져온 관광명소: {len(points)}개")
            random.shuffle(points)
            selected_points = points[:count]
            
            attractions = []
            for point in selected_points:
                attraction_data = point.payload.get("metadata", {})
                formatted_data = {
                    "attr_id": attraction_data.get("attr_id"),
                    "title": attraction_data.get("title"),
                    "type": "attraction"
                }
                attractions.append(formatted_data)
                print(f"  ✅ {formatted_data['title']}")
            
            print(f"🎲 랜덤 추천 완료: {len(attractions)}개")
            return attractions
            
        except Exception as e:
            print(f"❌ 랜덤 추천 오류: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def _generate_kpop_random_response(attractions: List[Dict]) -> str:
        """랜덤 추천 응답 (K-pop 모드)"""
        if not attractions:
            return "Hey Hunters! 😅 지금 추천할 미션 장소가 없네... 다시 검색해볼게! 🔥"
        return f"Yo! Hunters! 🔥💫 엄선한 {len(attractions)}개의 전설적인 장소들이야! 각 장소마다 특별한 빛의 에너지가 있으니까 직접 체크해봐! 궁금한 곳 있으면 말해줘! Let's explore! 🌙✨"
    
    # ===== 메인 API 함수 (스트리밍 전용) =====
    
    @staticmethod
    async def send_message_streaming(db: Session, user_id: int, message: str):
        """스트리밍 메시지 처리 (유일한 메인 함수)"""
        try:
            # K-pop 모드 판단
            conversation_count = db.query(Conversation).filter(Conversation.user_id == user_id).count()
            is_kpop_mode = conversation_count < 50
            
            analysis = ChatService._analyze_message_fast(message)
            question_type = analysis.get('type', 'place_search')
            keyword = analysis.get('keyword', message)
            is_random = analysis.get('is_random_recommendation', False)
            is_restaurant_query = ChatService._is_restaurant_query(message)
            
            print(f"📋 스트리밍 분석: type={question_type}, keyword={keyword}, restaurant={is_restaurant_query}")
            
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
            elif is_random or question_type == "random_recommendation" or question_type == "recommendation":
                yield f"data: {json.dumps({'type': 'random', 'message': '🎲 랜덤 추천 준비 중...'}, ensure_ascii=False)}\n\n"
                
                count = analysis.get('count', 10)
                random_attractions = ChatService._get_random_attractions(count)
                ai_response = ChatService._generate_kpop_random_response(random_attractions)
                
                conversation = Conversation(user_id=user_id, question=message, response=ai_response)
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                
                yield f"data: {json.dumps({'type': 'done', 'full_response': ai_response, 'results': random_attractions, 'attractions': random_attractions, 'convers_id': conversation.convers_id, 'has_festivals': False, 'has_attractions': True, 'has_restaurants': False, 'map_markers': ChatService._create_markers(random_attractions)}, ensure_ascii=False)}\n\n"
                return
            
            # 일반 장소 검색 (병렬 처리 유지)
            else:
                yield f"data: {json.dumps({'type': 'searching', 'message': '🔍 정보를 찾고 있어요...'}, ensure_ascii=False)}\n\n"
                
                with ThreadPoolExecutor(max_workers=3) as executor:
                    festival_future = executor.submit(ChatService._search_best_festival, keyword)
                    attraction_future = executor.submit(ChatService._search_best_attraction, keyword)
                    restaurant_future = executor.submit(ChatService._search_best_restaurant, keyword)
                    
                    festival = festival_future.result()
                    attraction = attraction_future.result()
                    restaurant = restaurant_future.result()
                
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
                
                if not results:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Hey Hunters! 😅 그 장소를 찾을 수 없네... 🔥'}, ensure_ascii=False)}\n\n"
                    return
                
                results.sort(key=lambda x: x['similarity_score'], reverse=True)
                result = results[0]
                
                yield f"data: {json.dumps({'type': 'found', 'title': result.get('restaurant_name') or result.get('title'), 'result': result}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'generating', 'message': '💫 응답하는 중...'}, ensure_ascii=False)}\n\n"
                
                # 프롬프트 생성
                title = result.get('title', '') or result.get('restaurant_name', '')
                description = result.get('description', '')[:500]
                result_type = result.get('type', 'attraction')
                
                prompts = {
                    'festival': KPOP_FESTIVAL_QUICK_PROMPT.format(
                        title=title,
                        start_date=result.get('start_date', ''),
                        end_date=result.get('end_date', ''),
                        description=description,
                        message=message
                    ),
                    'restaurant': RESTAURANT_QUICK_PROMPT.format(
                        restaurant_name=result.get('restaurant_name', ''),
                        location=result.get('place', ''),
                        description=description,
                        message=message
                    ),
                    'attraction': KPOP_ATTRACTION_QUICK_PROMPT.format(
                        title=title,
                        address=result.get('address', ''),
                        hours_of_operation=result.get('hours_of_operation', '운영시간 정보 없음'),
                        description=description,
                        message=message
                    )
                }
                
                prompt = prompts.get(result_type, prompts['attraction'])
                
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
                    'festivals': [result] if result.get('type') == 'festival' else [],
                    'attractions': [result] if result.get('type') == 'attraction' else [],
                    'restaurants': [result] if result.get('type') == 'restaurant' else [],
                    'has_festivals': result.get('type') == 'festival',
                    'has_attractions': result.get('type') == 'attraction',
                    'has_restaurants': result.get('type') == 'restaurant',
                    'map_markers': map_markers
                }
                
                yield f"data: {json.dumps(completion_data, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            print(f"❌ Streaming 오류: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    # ===== 호환성 함수 (기존 코드 호환용) =====
    
    @staticmethod  
    def send_message(db: Session, user_id: int, message: str) -> Dict[str, Any]:
        """기존 호환성을 위한 동기 wrapper (실제로는 스트리밍 결과를 동기로 변환)"""
        import asyncio
        
        # 스트리밍 결과를 모아서 최종 결과만 반환
        async def _collect_streaming_result():
            result_data = None
            async for chunk in ChatService.send_message_streaming(db, user_id, message):
                if '"type": "done"' in chunk:
                    # done 메시지에서 결과 추출
                    try:
                        data = json.loads(chunk.split('data: ')[1])
                        return data
                    except:
                        pass
            return {"response": "처리 중 오류가 발생했습니다.", "convers_id": None, "results": []}
        
        # 비동기 함수를 동기로 실행
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