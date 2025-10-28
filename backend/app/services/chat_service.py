"""
채팅 서비스 - ORM 버전
"""
from app.utils.openai_client import chat_with_gpt, extract_destinations_from_text
from app.utils.prompts import GENERAL_CHAT_PROMPT
from app.models.conversation import Conversation
from app.models.destination import Destination
from sqlalchemy.orm import Session

class ChatService:
    """채팅 관련 비즈니스 로직 (ORM 버전)"""
    
    @staticmethod
    def send_message(db: Session, user_id: int, message: str):
        """
        메시지 전송 및 GPT 응답 받기 (ORM 버전)
        """
        # GPT에게 메시지 전송
        messages = [
            {"role": "system", "content": GENERAL_CHAT_PROMPT},
            {"role": "user", "content": message}
        ]
        
        gpt_response = chat_with_gpt(messages)
        
        # 대화 저장
        new_conversation = Conversation(
            user_id=user_id,
            question=message,
            response=gpt_response,
            fullconverse=None
        )
        
        db.add(new_conversation)
        db.commit()
        db.refresh(new_conversation)
        
        # 여행지 추출
        destinations = extract_destinations_from_text(message)
        
        # 여행지가 있으면 DB에 저장 (중복 제거)
        if destinations:
            for name in destinations:
                # 중복 체크
                existing = db.query(Destination).filter(
                    Destination.user_id == user_id,
                    Destination.name == name
                ).first()
                
                if not existing:
                    new_destination = Destination(
                        user_id=user_id,
                        name=name,
                        extracted_from_convers_id=new_conversation.convers_id
                    )
                    db.add(new_destination)
            
            db.commit()
        
        return {
            'convers_id': new_conversation.convers_id,
            'question': new_conversation.question,
            'response': new_conversation.response,
            'datetime': new_conversation.datetime,
            'extracted_destinations': destinations
        }
    
    @staticmethod
    def get_conversation_history(db: Session, user_id: int, limit: int = 50):
        """대화 히스토리 가져오기 (ORM 버전)"""
        conversations = db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(
            Conversation.datetime.desc()
        ).limit(limit).all()
        
        # 딕셔너리 형태로 변환 (기존 인터페이스 유지)
        result = []
        for conv in conversations:
            result.append({
                'convers_id': conv.convers_id,
                'question': conv.question,
                'response': conv.response,
                'datetime': conv.datetime
            })
        
        return result