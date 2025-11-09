# app/api/endpoints/chat.py
"""
채팅 API 엔드포인트 (ORM 버전) - 축제 검색 기능 포함
🌊 Streaming 지원 추가!
✅ hours_of_operation, message 에러 수정
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import json
import asyncio

from app.database.connection import get_db
from app.services.chat_service import ChatService
from app.schemas import ChatMessage
from app.core.deps import get_current_user
from app.utils.openai_client import chat_with_gpt_stream
from app.utils.prompts import KPOP_ATTRACTION_QUICK_PROMPT, KPOP_FESTIVAL_QUICK_PROMPT
from app.models.conversation import Conversation

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/send")
async def send_message(
    request: ChatMessage,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GPT에게 메시지 전송 - 일반 방식 (기존)
    
    응답 형식:
    {
        "response": "GPT 응답",
        "convers_id": 123,
        "extracted_destinations": [],
        "results": [...],        # 검색 결과
        "festivals": [...],      # 축제 카드 데이터
        "attractions": [...],    # 관광지 카드 데이터
        "has_festivals": true,
        "has_attractions": true,
        "map_markers": [...]
    }
    """
    try:
        result = ChatService.send_message(
            db=db,
            user_id=current_user['user_id'],
            message=request.message
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 오류: {str(e)}")


@router.post("/send/stream")
async def send_message_streaming(
    request: ChatMessage,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🌊 GPT에게 메시지 전송 - Streaming 방식 (NEW!)
    
    실시간으로 응답이 타이핑되는 것처럼 보임!
    체감 속도: 0.5초로 느껴짐
    
    응답 형식 (Server-Sent Events):
    data: {"type": "searching", "message": "검색 중..."}
    data: {"type": "found", "title": "남산타워"}
    data: {"type": "generating", "message": "Lumi 응답 생성 중..."}
    data: {"type": "chunk", "content": "Hey "}
    data: {"type": "chunk", "content": "Hunters! "}
    data: {"type": "done", "full_response": "...", "result": {...}}
    """
    user_id = current_user['user_id']
    message = request.message
    
    async def generate():
        """SSE 스트림 생성"""
        try:
            # 🚀 1. 키워드 추출 (0.01초)
            analysis = ChatService._analyze_message_fast(message)
            keyword = analysis.get('keyword', message)
            is_random = analysis.get('is_random_recommendation', False)
            
            # 랜덤 추천 처리
            if is_random:
                yield f"data: {json.dumps({'type': 'random', 'message': '랜덤 추천 준비 중...'}, ensure_ascii=False)}\n\n"
                
                random_attractions = ChatService._get_random_attractions(count=10)
                ai_response = ChatService._generate_kpop_random_response(random_attractions)
                
                # 대화 저장
                conversation = Conversation(
                    user_id=user_id,
                    question=message,
                    response=ai_response
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                
                yield f"data: {json.dumps({'type': 'done', 'full_response': ai_response, 'attractions': random_attractions, 'convers_id': conversation.convers_id}, ensure_ascii=False)}\n\n"
                return
            
            # 🔍 2. 검색 시작 알림
            yield f"data: {json.dumps({'type': 'searching', 'message': '🔍 Lumi가 정보를 찾고 있어요...'}, ensure_ascii=False)}\n\n"
            
            # 병렬 검색 (0.6초)
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=2) as executor:
                festival_future = executor.submit(ChatService._search_best_festival, keyword)
                attraction_future = executor.submit(ChatService._search_best_attraction, keyword)
                
                festival = festival_future.result()
                attraction = attraction_future.result()
            
            # 결과 수집
            results = []
            if festival:
                festival['type'] = 'festival'
                results.append(festival)
            if attraction:
                attraction['type'] = 'attraction'
                results.append(attraction)
            
            if not results:
                yield f"data: {json.dumps({'type': 'error', 'message': '어이쿠, Hunters! 그 장소를 찾을 수 없네... 🔥'}, ensure_ascii=False)}\n\n"
                return
            
            # 유사도 높은 것 선택
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            result = results[0]
            
            # ✅ 검색 완료 알림
            yield f"data: {json.dumps({'type': 'found', 'title': result['title'], 'result': result}, ensure_ascii=False)}\n\n"
            
            # 💫 3. GPT 응답 생성 시작 알림
            yield f"data: {json.dumps({'type': 'generating', 'message': '💫 Lumi가 응답하는 중...'}, ensure_ascii=False)}\n\n"
            
            # 프롬프트 생성
            title = result.get('title', '')
            description = result.get('description', '')[:500]
            result_type = result.get('type', 'attraction')
            
            if result_type == 'festival':
                prompt = KPOP_FESTIVAL_QUICK_PROMPT.format(
                    title=title,
                    start_date=result.get('start_date', ''),
                    end_date=result.get('end_date', ''),
                    description=description,
                    message=message  # ✅ 추가!
                )
            else:
                prompt = KPOP_ATTRACTION_QUICK_PROMPT.format(
                    title=title,
                    address=result.get('address', ''),
                    hours_of_operation=result.get('hours_of_operation', '운영시간 정보 없음'),  # ✅ 추가!
                    description=description,
                    message=message  # ✅ 추가!
                )
            
            response_messages = [{"role": "user", "content": prompt}]
            
            # 🌊 4. 스트리밍 응답!
            full_response = ""
            for chunk in chat_with_gpt_stream(response_messages, max_tokens=250, temperature=0.6):
                full_response += chunk
                # 실시간 청크 전송
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                # 자연스러운 타이핑 효과
                await asyncio.sleep(0.02)
            
            # ✅ 5. 완료!
            # 대화 저장
            conversation = Conversation(
                user_id=user_id,
                question=message,
                response=full_response
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            
            # 지도 마커 생성
            map_markers = ChatService._create_map_markers([result])
            
            # 완료 메시지 (전체 데이터 포함)
            completion_data = {
                'type': 'done',
                'full_response': full_response,
                'convers_id': conversation.convers_id,
                'result': result,
                'festivals': [r for r in [result] if r.get('type') == 'festival'],
                'attractions': [r for r in [result] if r.get('type') == 'attraction'],
                'has_festivals': result.get('type') == 'festival',
                'has_attractions': result.get('type') == 'attraction',
                'map_markers': map_markers
            }
            
            yield f"data: {json.dumps(completion_data, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            print(f"❌ Streaming 오류: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx 버퍼링 방지
        }
    )


###################################################
# 아래는 현재 사용하지 않는 엔드포인트 (주석 처리)

# @router.get("/history", response_model=List[ConversationSummary])
# async def get_chat_history(
#     limit: int = 50,
#     current_user: dict = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     대화 히스토리 조회
#     """
#     try:
#         conversations = ChatService.get_conversation_history(
#             db=db,
#             user_id=current_user['user_id'],
#             limit=limit
#         )
        
#         return conversations
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"히스토리 조회 오류: {str(e)}")