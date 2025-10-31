# app/services/chat_service.py
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import json

from app.models.conversation import Conversation  
from app.models.festival import Festival
from app.utils.openai_client import chat_with_gpt

class ChatService:
    
    @staticmethod
    def send_message(db: Session, user_id: int, message: str) -> Dict[str, Any]:
        """
        메시지 처리 및 응답 생성
        GPT가 축제 검색 필요 여부 판단 + 키워드 추출
        """
        try:
            # 1. GPT에게 축제 검색 필요 여부 + 키워드 추출 요청
            festival_query_result = ChatService._analyze_message_with_gpt(message)
            
            festivals_data = []
            if festival_query_result.get('is_festival_query') and festival_query_result.get('keyword'):
                # 2. DB LIKE 검색
                festival = ChatService._search_festival(db, festival_query_result['keyword'])
                if festival:
                    festivals_data = [festival.to_dict()]
            
            # 3. GPT 최종 응답 생성
            ai_response = ChatService._generate_final_response(message, festivals_data)
            
            # 4. 대화 저장 (올바른 필드명 사용)
            conversation = Conversation(
                user_id=user_id,
                question=message,        # message → question 수정
                response=ai_response
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            
            # 5. 응답 구성 (올바른 필드명 사용)
            return {
                "response": ai_response,
                "convers_id": conversation.convers_id,  # conversation_id → convers_id 수정
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
        GPT를 사용해 메시지 분석: 축제 검색 필요 여부 + 키워드 추출
        """
        try:
            analysis_messages = [
                {
                    "role": "system",
                    "content": """당신은 사용자의 메시지를 분석하여 축제 정보 검색이 필요한지 판단하는 전문가입니다.

사용자가 특정 축제나 행사에 대한 정보를 요청하는 경우에만 is_festival_query를 true로 설정하고, 검색할 키워드를 추출해주세요.

응답은 반드시 JSON 형식으로 해주세요:
{
    "is_festival_query": true/false,
    "keyword": "검색할 키워드" (축제 검색이 필요한 경우만)
}

예시:
- "창경궁 야연에 대해 알려줘" → {"is_festival_query": true, "keyword": "창경궁 야연"}
- "한강 빛축제 정보 줘" → {"is_festival_query": true, "keyword": "한강 빛축제"}  
- "안녕하세요" → {"is_festival_query": false}
- "오늘 날씨 어때?" → {"is_festival_query": false}"""
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
                return result
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 기본값
                return {"is_festival_query": False}
                
        except Exception as e:
            print(f"GPT 메시지 분석 오류: {e}")
            return {"is_festival_query": False}
    
    @staticmethod
    def _search_festival(db: Session, keyword: str) -> Festival:
        """
        DB LIKE 검색으로 축제 찾기 (첫 번째 결과)
        """
        return db.query(Festival).filter(
            Festival.title.like(f'%{keyword}%')
        ).first()
    
    @staticmethod
    def _create_map_markers(festivals_data: List[Dict]) -> List[Dict]:
        """
        지도 마커 데이터 생성
        """
        markers = []
        for festival in festivals_data:
            lat = festival.get('latitude', 0.0)
            lng = festival.get('longitude', 0.0)
            
            if lat and lng and lat != 0.0 and lng != 0.0:
                markers.append({
                    "id": festival['festival_id'],
                    "festival_id": festival['festival_id'],  # 🎯 이거 추가!
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
                festival = festivals_data[0]
                
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
- 제목: {festival['title']}
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
                response = f"🎭 **{festival['title']}**에 대해 알려드릴게요!\n\n"
                
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
        대화 히스토리 조회 (올바른 필드명 사용)
        """
        conversations = db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.datetime.desc()).limit(limit).all()  # created_at → datetime 수정
        
        return [
            {
                "conversation_id": conv.convers_id,  # conversation_id → convers_id 수정
                "message": conv.question,            # message → question 수정
                "response": conv.response,
                "created_at": conv.datetime.isoformat()  # created_at → datetime 수정
            }
            for conv in reversed(conversations)
        ]