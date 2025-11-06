# app/services/chat_service.py
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import json
import os
import random  # 🎯 NEW: 랜덤 기능 추가
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient

from app.models.conversation import Conversation  
from app.models.festival import Festival
from app.utils.openai_client import chat_with_gpt

class ChatService:
    
    # 🎯 Qdrant 설정
    QDRANT_URL = "http://172.17.0.1:6333"
    COLLECTION_NAME = "seoul-festival"
    ATTRACTION_COLLECTION = "seoul-attraction"
    
    @staticmethod
    def send_message(db: Session, user_id: int, message: str) -> Dict[str, Any]:
        """
        메시지 처리 및 응답 생성 - 축제 + 관광명소 통합 검색 + 랜덤 추천
        """
        try:
            # 1. 키워드 추출 및 랜덤 추천 여부 확인
            analysis = ChatService._analyze_message_simple(message)
            keyword = analysis.get('keyword', message)
            is_random = analysis.get('is_random_recommendation', False)  # 🎯 NEW
            
            results = []
            
            # 🎯 NEW: 2-1. 랜덤 추천 요청인 경우
            if is_random:
                random_attractions = ChatService._get_random_attractions(count=10)
                
                # GPT 응답 생성 (타이틀 리스트만)
                ai_response = ChatService._generate_random_response(random_attractions)
                
                # 대화 저장
                conversation = Conversation(
                    user_id=user_id,
                    question=message,
                    response=ai_response
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                
                return {
                    "response": ai_response,
                    "convers_id": conversation.convers_id,
                    "extracted_destinations": [],
                    "results": random_attractions,
                    "festivals": [],
                    "attractions": random_attractions,
                    "has_festivals": False,
                    "has_attractions": len(random_attractions) > 0,
                    "map_markers": []  # 랜덤 추천은 지도 마커 없음
                }
            
            # 2-2. 기존: 축제 + 관광명소 검색
            festival = ChatService._search_best_festival(keyword)
            if festival:
                festival['type'] = 'festival'
                results.append(festival)
            
            attraction = ChatService._search_best_attraction(keyword)
            if attraction:
                attraction['type'] = 'attraction'
                results.append(attraction)
            
            # 3. 유사도 높은 것 1개만 선택
            if results:
                results.sort(key=lambda x: x['similarity_score'], reverse=True)
                best_result = [results[0]]
            else:
                best_result = []
            
            # 4. GPT 최종 응답 생성
            ai_response = ChatService._generate_final_response(message, best_result)
            
            # 5. 대화 저장
            conversation = Conversation(
                user_id=user_id,
                question=message,
                response=ai_response
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            
            # 6. 응답 구성
            return {
                "response": ai_response,
                "convers_id": conversation.convers_id,
                "extracted_destinations": [],
                "results": best_result,
                "festivals": [r for r in best_result if r.get('type') == 'festival'],
                "attractions": [r for r in best_result if r.get('type') == 'attraction'],
                "has_festivals": any(r.get('type') == 'festival' for r in best_result),
                "has_attractions": any(r.get('type') == 'attraction' for r in best_result),
                "map_markers": ChatService._create_map_markers(best_result)
            }
            
        except Exception as e:
            raise Exception(f"채팅 처리 중 오류 발생: {str(e)}")
    
    @staticmethod
    def _analyze_message_simple(message: str) -> Dict[str, Any]:
        """
        🎯 수정: 키워드 직접 감지 (GPT 의존도 낮춤)
        """
        try:
            # 🎯 1단계: 간단한 키워드 감지 (GPT 없이)
            message_lower = message.lower()
            
            # 랜덤 추천 키워드
            random_keywords = ['가볼만한', '추천', '어디 갈', '관광지', '명소', '갈만한', '여행지']
            
            # 랜덤 추천 감지
            if any(keyword in message_lower for keyword in random_keywords):
                print(f"🎲 랜덤 추천 감지: '{message}'")
                return {"is_random_recommendation": True, "keyword": ""}
            
            # 🎯 2단계: GPT로 키워드 추출 (일반 검색)
            print(f"🔍 일반 검색 모드: '{message}'")
            
            analysis_messages = [
                {
                    "role": "system",
                    "content": """사용자 메시지에서 검색 키워드를 추출하세요.

응답 형식 (JSON):
{
    "keyword": "검색할 키워드"
}

예시:
- "Dosan park 알려줘" → {"keyword": "Dosan park"}
- "한강페스티벌 정보" → {"keyword": "한강페스티벌"}"""
                },
                {
                    "role": "user",
                    "content": f"사용자 메시지: \"{message}\""
                }
            ]
            
            gpt_response = chat_with_gpt(analysis_messages)
            
            try:
                result = json.loads(gpt_response)
                result['is_random_recommendation'] = False
                print(f"🤖 키워드 추출 성공: {result}")
                return result
            except json.JSONDecodeError:
                print(f"⚠️ JSON 파싱 실패, 원본 사용")
                return {"is_random_recommendation": False, "keyword": message}
                
        except Exception as e:
            print(f"❌ 키워드 추출 오류: {e}")
            import traceback
            traceback.print_exc()
            return {"is_random_recommendation": False, "keyword": message}
    
    @staticmethod
    def _get_random_attractions(count: int = 10) -> List[Dict[str, Any]]:
        """
        🎯 NEW: 랜덤 관광명소 추천 (타이틀만)
        """
        try:
            print(f"🎲 랜덤 관광명소 {count}개 추천 시작...")
            
            qdrant_client = QdrantClient(
                url=ChatService.QDRANT_URL,
                timeout=60,
                prefer_grpc=False
            )
            
            # 🎯 랜덤 오프셋으로 많이 가져오기 (전체 개수 모르므로)
            random_offset = random.randint(0, 100)  # 간단하게 0~100 사이
            
            scroll_result = qdrant_client.scroll(
                collection_name=ChatService.ATTRACTION_COLLECTION,
                limit=count * 3,  # 여유있게 가져오기
                offset=random_offset,
                with_payload=True,
                with_vectors=False
            )
            
            points = scroll_result[0]  # (points, next_offset) 튜플
            
            if not points:
                print(f"❌ 관광명소를 가져올 수 없습니다")
                return []
            
            print(f"📊 가져온 관광명소: {len(points)}개")
            
            # 🎯 랜덤 섞기 후 count개만 선택
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
    def _generate_random_response(attractions: List[Dict]) -> str:
        """
        🎯 NEW: 랜덤 추천 응답 생성 (카드로 보여줄 것이므로 간단히)
        """
        if not attractions:
            return "죄송합니다. 추천할 관광지를 찾을 수 없습니다. 😢"
        
        return f"🎯 서울의 추천 관광지 {len(attractions)}곳을 아래에 준비했습니다! 자세한 정보가 필요하시면 구체적인 장소명을 말씀해주세요! 😊"
    
    @staticmethod
    def _search_best_festival(keyword: str) -> Dict[str, Any]:
        """
        🎯 축제 벡터 검색
        """
        try:
            qdrant_client = QdrantClient(
                url=ChatService.QDRANT_URL,
                timeout=60,
                prefer_grpc=False
            )
            
            embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")
            query_embedding = embedding_model.embed_query(keyword)
            
            search_results = qdrant_client.search(
                collection_name=ChatService.COLLECTION_NAME,
                query_vector=query_embedding,
                limit=1,
                score_threshold=0.3,
                with_payload=True,
                with_vectors=False
            )
            
            if not search_results:
                print(f"🔍 축제 검색 결과 없음: '{keyword}'")
                return None
            
            result = search_results[0]
            festival_data = result.payload.get("metadata", {})
            
            formatted_data = {
                "festival_id": festival_data.get("festival_id", festival_data.get("row")),
                "title": festival_data.get("title"),
                "filter_type": festival_data.get("filter_type"), 
                "start_date": festival_data.get("start_date"),
                "end_date": festival_data.get("end_date"),
                "image_url": festival_data.get("image_url"),
                "detail_url": festival_data.get("detail_url"),
                "latitude": float(festival_data.get("latitude", 0)) if festival_data.get("latitude") else 0.0,
                "longitude": float(festival_data.get("longitude", 0)) if festival_data.get("longitude") else 0.0,
                "description": festival_data.get("description"),
                "similarity_score": result.score
            }
            
            print(f"🎯 축제 검색 성공: '{formatted_data['title']}' (유사도: {result.score:.3f})")
            return formatted_data
            
        except Exception as e:
            print(f"축제 검색 오류: {e}")
            return None
    
    @staticmethod
    def _search_best_attraction(keyword: str) -> Dict[str, Any]:
        """
        🎯 관광명소 벡터 검색
        """
        try:
            qdrant_client = QdrantClient(
                url=ChatService.QDRANT_URL,
                timeout=60,
                prefer_grpc=False
            )
            
            embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")
            query_embedding = embedding_model.embed_query(keyword)
            
            search_results = qdrant_client.search(
                collection_name=ChatService.ATTRACTION_COLLECTION,
                query_vector=query_embedding,
                limit=1,
                score_threshold=0.3,
                with_payload=True,
                with_vectors=False
            )
            
            if not search_results:
                print(f"🔍 관광명소 검색 결과 없음: '{keyword}'")
                return None
            
            result = search_results[0]
            attraction_data = result.payload.get("metadata", {})
            
            formatted_data = {
                "attr_id": attraction_data.get("attr_id"),
                "title": attraction_data.get("title"),
                "url": attraction_data.get("url"),
                "description": attraction_data.get("description"),
                "phone": attraction_data.get("phone"),
                "hours_of_operation": attraction_data.get("hours_of_operation"),
                "holidays": attraction_data.get("holidays"),
                "address": attraction_data.get("address"),
                "transportation": attraction_data.get("transportation"),
                "image_urls": attraction_data.get("image_urls"),
                "image_count": attraction_data.get("image_count", 0),
                "latitude": float(attraction_data.get("latitude", 0)),
                "longitude": float(attraction_data.get("longitude", 0)),
                "attr_code": attraction_data.get("attr_code"),
                "similarity_score": result.score
            }
            
            print(f"🎯 관광명소 검색 성공: '{formatted_data['title']}' (유사도: {result.score:.3f})")
            return formatted_data
            
        except Exception as e:
            print(f"관광명소 검색 오류: {e}")
            return None
    
    @staticmethod  
    def _create_map_markers(results_data: List[Dict]) -> List[Dict]:
        """
        지도 마커 데이터 생성 (축제 + 관광명소)
        """
        markers = []
        for item in results_data:
            lat = item.get('latitude', 0.0)
            lng = item.get('longitude', 0.0)
            
            if lat and lng and lat != 0.0 and lng != 0.0:
                marker = {
                    "id": item.get('festival_id') or item.get('attr_id'),
                    "title": item['title'],
                    "latitude": float(lat),
                    "longitude": float(lng),
                    "type": item.get('type', 'festival')
                }
                
                if item.get('type') == 'festival':
                    marker.update({
                        "festival_id": item['festival_id'],
                        "description": item.get('description', '')[:100] + "...",
                        "image_url": item.get('image_url'),
                        "start_date": item.get('start_date'),
                        "end_date": item.get('end_date')
                    })
                elif item.get('type') == 'attraction':
                    marker.update({
                        "attr_id": item['attr_id'],
                        "address": item.get('address'),
                        "phone": item.get('phone'),
                        "image_urls": item.get('image_urls')
                    })
                
                markers.append(marker)
        
        return markers
    
    @staticmethod
    def _generate_final_response(message: str, results_data: List[Dict]) -> str:
        """
        GPT를 통한 최종 응답 생성 (축제 + 관광명소)
        """
        try:
            if results_data:
                result = results_data[0]
                result_type = result.get('type', 'festival')
                
                if result_type == 'festival':
                    content = f"""
사용자 질문: {message}

축제 정보:
- 제목: {result.get('title')}
- 기간: {result.get('start_date')} ~ {result.get('end_date')}
- 설명: {result.get('description')}

친절하게 최대한 모든 내용을 활용해서 답변하세요."""
                else:
                    content = f"""
사용자 질문: {message}

관광명소 정보:
- 이름: {result.get('title')}
- 주소: {result.get('address')}
- 운영시간: {result.get('hours_of_operation')}
- 설명: {result.get('description')}

친절하게 최대한 모든 내용을 활용해서 답변하세요."""
                
                response_messages = [
                    {
                        "role": "system", 
                        "content": "당신은 친절한 관광 가이드입니다. 친절하게 최대한 모든 내용을 활용해서 답변하세요."
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ]
                
                return chat_with_gpt(response_messages)
                
            else:
                return "안녕하세요! 축제나 관광명소에 대해 궁금한 것이 있으시면 언제든 물어보세요! 😊"
                
        except Exception as e:
            if results_data:
                result = results_data[0]
                return f"🎯 {result.get('title')}을(를) 찾았습니다! 아래 정보를 확인해주세요 😊"
            else:
                return "안녕하세요! 궁금한 것이 있으시면 언제든 물어보세요! 😊"
    
    @staticmethod
    def get_conversation_history(db: Session, user_id: int, limit: int = 50) -> List[Dict]:
        """
        대화 히스토리 조회
        """
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