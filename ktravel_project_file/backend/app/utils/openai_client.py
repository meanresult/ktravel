"""
OpenAI API 클라이언트 - 🚀 최적화 버전 (Streaming 지원)
"""
from openai import OpenAI
from app.core.config import settings
from typing import Generator

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def chat_with_gpt(messages: list, model: str = None, temperature: float = 0.7, max_tokens: int = 350, stream: bool = False) -> str:
    """
    🚀 최적화된 GPT 채팅
    
    Args:
        messages: 대화 메시지 리스트 [{"role": "user", "content": "..."}]
        model: 사용할 모델 (기본값: settings.OPENAI_MODEL, 권장: gpt-4o-mini)
        temperature: 창의성 (0.7-0.8 권장)
        max_tokens: 최대 토큰 수 (350 = 약 250단어, Lumi 응답에 적합)
        stream: 스트리밍 모드 (실시간 응답, 체감 속도 10배!)
    
    Returns:
        GPT 응답 텍스트
    
    Performance Tips:
        - gpt-4o-mini: 2-3초 (빠름! ⚡ 권장)
        - stream=True: 체감 0.5초로 느껴짐! (실제론 같지만 즉시 표시)
        - max_tokens 낮을수록 빠름
        - temperature 낮을수록 빠름 (하지만 0.7-0.8 권장)
    """
    if model is None:
        model = settings.OPENAI_MODEL
    
    try:
        if stream:
            # 🌊 스트리밍 모드: 실시간으로 응답 생성
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,  # 🚀 스트리밍!
                timeout=10
            )
            
            # 스트림 수집
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
            
            return full_response
        else:
            # 일반 모드
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=10
            )
            
            return response.choices[0].message.content
    
    except Exception as e:
        raise Exception(f"OpenAI API 오류: {str(e)}")


def chat_with_gpt_stream(messages: list, model: str = None, temperature: float = 0.7, max_tokens: int = 350) -> Generator[str, None, None]:
    """
    🌊 스트리밍 GPT 채팅 (FastAPI용)
    
    실시간으로 응답을 yield하여 프론트엔드에서 타이핑 효과 구현 가능
    
    Yields:
        응답 청크 (한 글자 또는 단어씩)
    """
    if model is None:
        model = settings.OPENAI_MODEL
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            timeout=10
        )
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        raise Exception(f"OpenAI API 오류: {str(e)}")


def extract_destinations_from_text(text: str) -> list:
    """
    텍스트에서 여행지 추출
    
    Args:
        text: 사용자 메시지
    
    Returns:
        추출된 여행지 리스트
    """
    from app.utils.prompts import DESTINATION_EXTRACTION_PROMPT
    
    messages = [
        {"role": "system", "content": DESTINATION_EXTRACTION_PROMPT},
        {"role": "user", "content": text}
    ]
    
    try:
        response = chat_with_gpt(messages, max_tokens=100)  # 🚀 짧은 응답
        
        # JSON 파싱 시도
        import json
        result = json.loads(response)
        destinations = result.get("destinations", [])
        
        # 빈 문자열이나 None 제거
        destinations = [d.strip() for d in destinations if d and d.strip()]
        
        return destinations
    
    except json.JSONDecodeError:
        # JSON 파싱 실패 시 빈 리스트 반환
        return []
    except Exception as e:
        print(f"여행지 추출 오류: {str(e)}")
        return []