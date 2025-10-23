"""
채팅 서비스 - 수정된 전체 코드
"""
from app.utils.openai_client import chat_with_gpt, extract_destinations_from_text
from app.utils.prompts import GENERAL_CHAT_PROMPT
from app.database.queries.conversation_queries import ConversationQueries
from app.database.queries.destination_queries import DestinationQueries  # ← 수정!

class ChatService:
    """채팅 관련 비즈니스 로직"""
    
    @staticmethod
    def send_message(conn, cursor, user_id: int, message: str):
        """
        메시지 전송 및 GPT 응답 받기
        """
        # GPT에게 메시지 전송
        messages = [
            {"role": "system", "content": GENERAL_CHAT_PROMPT},
            {"role": "user", "content": message}
        ]
        
        gpt_response = chat_with_gpt(messages)
        
        # 대화 저장
        convers_id = ConversationQueries.create_conversation(
            cursor,
            user_id=user_id,
            question=message,
            response=gpt_response,
            fullconverse=None
        )
        
        conn.commit()
        
        # 여행지 추출
        destinations = extract_destinations_from_text(message)
        
        # 여행지가 있으면 DB에 저장 (중복 제거)
        if destinations:
            for name in destinations:
                if not DestinationQueries.destination_exists(cursor, user_id, name):
                    DestinationQueries.create_destination(
                        cursor, user_id, name, convers_id
                    )
            conn.commit()
        
        # 저장된 대화 정보 가져오기
        conversation = ConversationQueries.get_conversation_by_id(cursor, convers_id)
        
        return {
            'convers_id': conversation['convers_id'],
            'question': conversation['question'],
            'response': conversation['response'],
            'datetime': conversation['datetime'],
            'extracted_destinations': destinations
        }
    
    @staticmethod
    def get_conversation_history(cursor, user_id: int, limit: int = 50):
        """대화 히스토리 가져오기"""
        conversations = ConversationQueries.get_user_conversations(
            cursor, user_id, limit=limit
        )
        
        return conversations