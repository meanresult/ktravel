# app/services/chat_service.py
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import json
import os
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient

from app.models.conversation import Conversation  
from app.models.festival import Festival
from app.utils.openai_client import chat_with_gpt

class ChatService:
    
    # 🎯 Qdrant 설정
    QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
    #QDRANT_URL = "http://172.17.0.1:6333"  # 🎯 실제 호스트 IP
    COLLECTION_NAME = "seoul-festival"
    
    @staticmethod
    def send_message(db: Session, user_id: int, message: str) -> Dict[str, Any]:
        """
        메시지 처리 및 응답 생성
        """
        try:
            # 1. GPT에게 축제 검색 필요 여부 + 키워드 추출 요청
            festival_query_result = ChatService._analyze_message_with_gpt(message)
            
            festivals_data = []
            if festival_query_result.get('is_festival_query') and festival_query_result.get('keyword'):
                # 2. 🎯 벡터 검색으로 가장 유사한 1개만 가져오기
                festival_data = ChatService._search_best_festival(festival_query_result['keyword'])
                if festival_data:
                    festivals_data = [festival_data]
            
            # 3. GPT 최종 응답 생성
            ai_response = ChatService._generate_final_response(message, festivals_data)
            
            # 4. 대화 저장
            conversation = Conversation(
                user_id=user_id,
                question=message,
                response=ai_response
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            
            # 5. 응답 구성 (기존 RDB 응답 형식 유지)
            return {
                "response": ai_response,
                "convers_id": conversation.convers_id,
                "extracted_destinations": [],  # 기존 구조 유지
                "festivals": festivals_data,
                "has_festivals": len(festivals_data) > 0,
                "map_markers": ChatService._create_map_markers(festivals_data)
            }
            
        except Exception as e:
            raise Exception(f"채팅 처리 중 오류 발생: {str(e)}")
    
    @staticmethod
    def _analyze_message_with_gpt(message: str) -> Dict[str, Any]:
        """
        🎯 개선: GPT를 사용해 메시지 분석 (더 적극적인 축제 검색)
        """
        try:
            analysis_messages = [
                {
                    "role": "system",
                    "content": """당신은 사용자의 메시지를 분석하여 축제/행사 정보 검색이 필요한지 판단하는 전문가입니다.

**중요**: 다음과 같은 경우 is_festival_query를 true로 설정하세요:
1. 축제, 행사, 이벤트, 공연, 전시 등의 단어가 명시된 경우
2. 특정 장소(궁궐, 공원, 한강 등) + "에 대해", "정보", "알려줘" 같은 표현 
   → 해당 장소의 행사/축제를 찾아야 함
3. "야연", "페스티벌", "축전" 등 행사 관련 용어
4. 날짜/계절 + 장소 조합 (예: "5월 창경궁", "가을 한강")

**일반 대화 (false):**
- 단순 인사 (안녕, 고마워)
- 날씨, 시간 질문
- 교통편, 길찾기

응답 형식 (JSON):
{
    "is_festival_query": true/false,
    "keyword": "검색 키워드"
}

예시:
- "창경궁 야연 알려줘" → {"is_festival_query": true, "keyword": "창경궁 야연"}
- "창경궁에 대해 알려줘" → {"is_festival_query": true, "keyword": "창경궁"}
- "궁중문화축전 정보" → {"is_festival_query": true, "keyword": "궁중문화축전"}
- "한강 축제" → {"is_festival_query": true, "keyword": "한강"}
- "안녕하세요" → {"is_festival_query": false}"""
                },
                {
                    "role": "user",
                    "content": f"사용자 메시지: \"{message}\""
                }
            ]
            
            gpt_response = chat_with_gpt(analysis_messages)
            
            # JSON 파싱 시도
            try:
                result = json.loads(gpt_response)
                print(f"🤖 GPT 분석: {result}")  # 🎯 디버깅 로그 추가
                return result
            except json.JSONDecodeError:
                print(f"⚠️ JSON 파싱 실패: {gpt_response}")
                return {"is_festival_query": False}
                
        except Exception as e:
            print(f"❌ GPT 메시지 분석 오류: {e}")
            return {"is_festival_query": False}
    
    @staticmethod
    def _search_best_festival(keyword: str) -> Dict[str, Any]:
        """
        🎯 벡터 검색으로 가장 유사한 축제 1개만 반환
        Document 메타데이터를 그대로 활용하여 기존 RDB 형식 유지
        """
        try:
            print(f"🔍 검색 키워드: '{keyword}'")  # 🎯 디버깅 로그
            
            # 🎯 Qdrant 클라이언트 연결
            qdrant_client = QdrantClient(
                url=ChatService.QDRANT_URL,
                timeout=60,
                prefer_grpc=False
            )
            
            # 임베딩 모델 준비
            embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")
            
            # 검색어 임베딩 생성
            query_embedding = embedding_model.embed_query(keyword)
            print(f"✅ 임베딩 생성 완료 (차원: {len(query_embedding)})")  # 🎯 디버깅 로그
            
            # 🎯 벡터 검색 (임계값 낮춤)
            search_results = qdrant_client.search(
                collection_name=ChatService.COLLECTION_NAME,
                query_vector=query_embedding,
                limit=3,  # 🎯 3개 가져와서 로그 확인
                score_threshold=0.2,  # 🎯 0.3 → 0.2로 낮춤
                with_payload=True,
                with_vectors=False
            )
            
            if not search_results:
                print(f"❌ 검색 결과 없음: '{keyword}'")
                return None
            
            # 🎯 검색 결과 로그 출력
            print(f"🎯 검색된 결과 {len(search_results)}개:")
            for i, r in enumerate(search_results, 1):
                title = r.payload.get("metadata", {}).get("title", "N/A")
                print(f"  {i}. {title} (유사도: {r.score:.3f})")
            
            # 가장 유사한 결과 1개
            result = search_results[0]
            festival_data = result.payload.get("metadata", {})
            
            # 🎯 기존 RDB 응답과 동일한 형식으로 변환
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
            
            print(f"✅ 최종 선택: '{formatted_data['title']}' (유사도: {result.score:.3f})")
            return formatted_data
            
        except Exception as e:
            print(f"❌ 벡터 검색 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod  
    def _create_map_markers(festivals_data: List[Dict]) -> List[Dict]:
        """
        지도 마커 데이터 생성 (기존 형식 유지)
        """
        markers = []
        for festival in festivals_data:
            lat = festival.get('latitude', 0.0)
            lng = festival.get('longitude', 0.0)
            
            if lat and lng and lat != 0.0 and lng != 0.0:
                markers.append({
                    "id": festival['festival_id'],
                    "festival_id": festival['festival_id'],
                    "title": festival['title'],
                    "latitude": float(lat),
                    "longitude": float(lng),
                    "description": festival.get('description', '')[:100] + "...",
                    "image_url": festival.get('image_url'),
                    "detail_url": festival.get('detail_url'),
                    "start_date": festival.get('start_date'),
                    "end_date": festival.get('end_date')
                })
        return markers
    
    @staticmethod
    def _generate_final_response(message: str, festivals_data: List[Dict]) -> str:
        """
        GPT를 통한 최종 응답 생성
        """
        try:
            if festivals_data:
                festival = festivals_data[0]  # 유일한 축제
                
                # 축제 정보를 포함한 자연스러운 응답 생성
                response_messages = [
                    {
                        "role": "system", 
                        "content": "당신은 한국의 축제 정보를 안내하는 친절한 가이드입니다. 사용자가 축제에 대해 질문하면 제공된 정보를 바탕으로 자연스럽고 친근하게 답변해주세요."
                    },
                    {
                        "role": "user",
                        "content": f"""
사용자 질문: {message}

축제 정보:
- 제목: {festival.get('title', 'N/A')}
- 기간: {festival.get('start_date', '')} ~ {festival.get('end_date', '')}
- 설명: {festival.get('description', '')}

위 축제 정보를 바탕으로 사용자의 질문에 친절하고 자세히 답변해주세요.
축제의 특징, 볼거리, 일정 등을 포함하여 설명해주세요.
답변은 자연스럽고 대화체로 작성해주세요.
"""
                    }
                ]
                
                return chat_with_gpt(response_messages)
                
            else:
                # 일반 대화 또는 축제를 찾지 못한 경우
                general_messages = [
                    {
                        "role": "system",
                        "content": "당신은 친절한 축제 정보 가이드입니다. 축제 관련 질문이 아니면 자연스럽게 대화하고, 축제 정보를 찾지 못했다면 정중하게 안내해주세요."
                    },
                    {
                        "role": "user", 
                        "content": message
                    }
                ]
                
                return chat_with_gpt(general_messages)
                
        except Exception as e:
            # GPT 실패 시 기본 응답
            if festivals_data:
                festival = festivals_data[0]
                response = f"🎭 **{festival.get('title', 'N/A')}**에 대해 알려드릴게요!\n\n"
                
                if festival.get('start_date') and festival.get('end_date'):
                    response += f"📅 **기간**: {festival.get('start_date')} ~ {festival.get('end_date')}\n\n"
                
                if festival.get('description'):
                    response += f"📍 **소개**: {festival.get('description')}\n\n"
                
                response += "자세한 정보는 아래 카드를 확인해주세요! 😊"
                return response
            else:
                return "안녕하세요! 축제나 행사에 대해 궁금한 것이 있으시면 언제든 물어보세요! 😊"
    
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