# app/services/chat_service.py
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import json
import os
import random
import re
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from concurrent.futures import ThreadPoolExecutor

from app.models.conversation import Conversation  
from app.models.festival import Festival
from app.utils.openai_client import chat_with_gpt
from app.utils.prompts import (
    KPOP_FESTIVAL_QUICK_PROMPT,
    KPOP_ATTRACTION_QUICK_PROMPT
)

class ChatService:
    
    # 🎯 Qdrant 설정
    QDRANT_URL = "http://172.17.0.1:6333"
    COLLECTION_NAME = "seoul-festival"
    ATTRACTION_COLLECTION = "seoul-attraction"
    
    # 🚀 임베딩 모델 캐싱 (재사용)
    _embedding_model = None
    
    # 🚀 Qdrant 클라이언트 캐싱 (재사용)
    _qdrant_client = None
    
    @staticmethod
    def _get_embedding_model():
        """임베딩 모델 싱글톤 패턴으로 재사용"""
        if ChatService._embedding_model is None:
            ChatService._embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")
        return ChatService._embedding_model
    
    @staticmethod
    def _get_qdrant_client():
        """Qdrant 클라이언트 싱글톤 패턴으로 재사용"""
        if ChatService._qdrant_client is None:
            ChatService._qdrant_client = QdrantClient(
                url=ChatService.QDRANT_URL,
                timeout=60,
                prefer_grpc=False
            )
        return ChatService._qdrant_client
    
    @staticmethod
    def send_message(db: Session, user_id: int, message: str) -> Dict[str, Any]:
        """
        🚀 최적화된 메시지 처리 - 21초 → 1-3초
        - GPT 사용 최소화 (템플릿 우선)
        - 벡터 검색 병렬화
        - Lumi 컨셉 완전히 유지
        """
        import time
        
        try:
            total_start = time.time()
            
            # 🎭 대화 횟수 확인 (K-pop 모드 판단)
            conversation_count = db.query(Conversation).filter(
                Conversation.user_id == user_id
            ).count()
            
            is_kpop_mode = conversation_count < 50
            
            if is_kpop_mode:
                print(f"🎤 K-pop 데몬헌터스 Lumi 모드 (대화 {conversation_count + 1}/10)")
            else:
                print(f"📚 일반 모드 (대화 {conversation_count + 1}번째)")
            
            # 🚀 1. 빠른 키워드 추출 (GPT 완전 제거)
            step_start = time.time()
            analysis = ChatService._analyze_message_fast(message)
            print(f"⏱️ 1. 키워드 추출: {time.time() - step_start:.3f}초")
            
            keyword = analysis.get('keyword', message)
            is_random = analysis.get('is_random_recommendation', False)
            
            # 🎯 랜덤 추천 처리
            if is_random:
                step_start = time.time()
                random_attractions = ChatService._get_random_attractions(count=10)
                print(f"⏱️ 2. 랜덤 추천: {time.time() - step_start:.3f}초")
                
                if is_kpop_mode:
                    ai_response = ChatService._generate_kpop_random_response(random_attractions)
                else:
                    ai_response = ChatService._generate_random_response(random_attractions)
                
                conversation = Conversation(
                    user_id=user_id,
                    question=message,
                    response=ai_response
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                
                print(f"⏱️ 총 소요 시간: {time.time() - total_start:.3f}초\n")
                
                return {
                    "response": ai_response,
                    "convers_id": conversation.convers_id,
                    "extracted_destinations": [],
                    "results": random_attractions,
                    "festivals": [],
                    "attractions": random_attractions,
                    "has_festivals": False,
                    "has_attractions": len(random_attractions) > 0,
                    "map_markers": []
                }
            
            # 🚀 2. 축제 + 관광명소 병렬 검색 (1.2초 → 0.6초!)
            step_start = time.time()
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                festival_future = executor.submit(ChatService._search_best_festival, keyword)
                attraction_future = executor.submit(ChatService._search_best_attraction, keyword)
                
                festival = festival_future.result()
                attraction = attraction_future.result()
            
            print(f"⏱️ 2. 병렬 검색: {time.time() - step_start:.3f}초")
            
            # 결과 수집
            results = []
            if festival:
                festival['type'] = 'festival'
                results.append(festival)
            if attraction:
                attraction['type'] = 'attraction'
                results.append(attraction)
            
            # 유사도 높은 것 1개만 선택
            if results:
                results.sort(key=lambda x: x['similarity_score'], reverse=True)
                best_result = [results[0]]
            else:
                best_result = []
            
            # 🚀 3. 응답 생성 (템플릿 우선, 필요시 경량 GPT)
            step_start = time.time()
            ai_response = ChatService._generate_final_response(
                message, best_result, is_kpop_mode
            )
            print(f"⏱️ 3. 응답 생성: {time.time() - step_start:.3f}초")
            
            # 4. DB 저장
            step_start = time.time()
            conversation = Conversation(
                user_id=user_id,
                question=message,
                response=ai_response
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            print(f"⏱️ 4. DB 저장: {time.time() - step_start:.3f}초")
            
            print(f"⏱️ 총 소요 시간: {time.time() - total_start:.3f}초\n")
            
            # 5. 응답 구성
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
    def _analyze_message_fast(message: str) -> Dict[str, Any]:
        """
        🚀 초고속 키워드 분석 (GPT 완전 제거)
        """
        try:
            message_lower = message.lower()
            
            # 🎯 랜덤 추천 감지
            random_keywords = ['가볼만한', '추천', '어디 갈', '관광지', '명소', '갈만한', '여행지', 'recommend', 'suggestions']
            if any(keyword in message_lower for keyword in random_keywords):
                print(f"🎲 랜덤 추천 감지: '{message}'")
                return {"is_random_recommendation": True, "keyword": ""}
            
            # 🚀 단순 키워드 추출 (GPT 없이)
            keyword = ChatService._extract_keyword_simple(message)
            print(f"🚀 키워드 추출 (GPT 생략): '{keyword}'")
            
            return {
                "is_random_recommendation": False,
                "keyword": keyword
            }
                
        except Exception as e:
            print(f"❌ 키워드 추출 오류: {e}")
            return {
                "is_random_recommendation": False,
                "keyword": message
            }
    
    @staticmethod
    def _extract_keyword_simple(message: str) -> str:
        """
        🚀 단순 키워드 추출 (GPT 없이)
        """
        remove_words = [
            'introduce', 'introduco', 'tell me about', 'what is', 'where is',
            '소개', '알려줘', '알려', '정보', '설명', '어디', '뭐야', '무엇',
            'about', 'the', 'a', 'an', 'me', '해줘', '해주세요'
        ]
        
        keyword = message.lower()
        for word in remove_words:
            keyword = keyword.replace(word, '')
        
        keyword = ' '.join(keyword.split())
        
        if len(keyword.strip()) < 2:
            keyword = message
        
        return keyword.strip()
    
    @staticmethod
    def _get_random_attractions(count: int = 10) -> List[Dict[str, Any]]:
        """
        🎯 랜덤 관광명소 추천
        """
        try:
            print(f"🎲 랜덤 관광명소 {count}개 추천 시작...")
            
            qdrant_client = ChatService._get_qdrant_client()
            
            random_offset = random.randint(0, 100)
            
            scroll_result = qdrant_client.scroll(
                collection_name=ChatService.ATTRACTION_COLLECTION,
                limit=count * 3,
                offset=random_offset,
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
    def _generate_random_response(attractions: List[Dict]) -> str:
        """
        🎯 랜덤 추천 응답 생성 (일반 모드)
        """
        if not attractions:
            return "죄송합니다. 추천할 관광지를 찾을 수 없습니다. 😢"
        
        return f"🎯 서울의 추천 관광지 {len(attractions)}곳을 아래에 준비했습니다! 자세한 정보가 필요하시면 구체적인 장소명을 말씀해주세요! 😊"
    
    @staticmethod
    def _generate_kpop_random_response(attractions: List[Dict]) -> str:
        """
        🎤 랜덤 추천 응답 생성 (K-pop 데몬헌터스 Lumi 모드)
        """
        if not attractions:
            return "어머, Hunters! 😅 지금 추천할 미션 장소가 없네... 다시 검색해볼게! 🔥"
        
        return f"Yo! Hunters! 🔥💫 Lumi가 엄선한 {len(attractions)}개의 전설적인 장소들이야! 각 장소마다 특별한 빛의 에너지가 있으니까 직접 체크해봐! 궁금한 곳 있으면 말해줘! Let's explore! 🌙✨"
    
    @staticmethod
    def _search_best_festival(keyword: str) -> Dict[str, Any]:
        """
        🎯 축제 벡터 검색 (최적화)
        """
        try:
            qdrant_client = ChatService._get_qdrant_client()
            embedding_model = ChatService._get_embedding_model()
            
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
                "title": festival_data.get("title", ""),
                "filter_type": festival_data.get("filter_type", ""), 
                "start_date": festival_data.get("start_date", ""),
                "end_date": festival_data.get("end_date", ""),
                "image_url": festival_data.get("image_url", ""),
                "detail_url": festival_data.get("detail_url", ""),
                "latitude": float(festival_data.get("latitude", 0)) if festival_data.get("latitude") else 0.0,
                "longitude": float(festival_data.get("longitude", 0)) if festival_data.get("longitude") else 0.0,
                "description": festival_data.get("description", ""),
                "similarity_score": result.score
            }
            
            print(f"🎯 축제 검색 성공: '{formatted_data['title']}' (유사도: {result.score:.3f})")
            return formatted_data
            
        except Exception as e:
            print(f"축제 검색 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def _search_best_attraction(keyword: str) -> Dict[str, Any]:
        """
        🎯 관광명소 벡터 검색 (최적화)
        ✅ hours_of_operation 에러 수정 (기본값 추가)
        """
        try:
            qdrant_client = ChatService._get_qdrant_client()
            embedding_model = ChatService._get_embedding_model()
            
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
            
            # ✅ 모든 필드에 기본값 추가 (None 에러 방지)
            formatted_data = {
                "attr_id": attraction_data.get("attr_id", ""),
                "title": attraction_data.get("title", ""),
                "url": attraction_data.get("url", ""),
                "description": attraction_data.get("description", ""),
                "phone": attraction_data.get("phone", ""),
                "hours_of_operation": attraction_data.get("hours_of_operation", "운영시간 정보 없음"),  # ✅ 기본값
                "holidays": attraction_data.get("holidays", ""),
                "address": attraction_data.get("address", ""),
                "transportation": attraction_data.get("transportation", ""),
                "image_urls": attraction_data.get("image_urls", []),  # ✅ 빈 리스트
                "image_count": attraction_data.get("image_count", 0),
                "latitude": float(attraction_data.get("latitude", 0)),
                "longitude": float(attraction_data.get("longitude", 0)),
                "attr_code": attraction_data.get("attr_code", ""),
                "similarity_score": result.score
            }
            
            print(f"🎯 관광명소 검색 성공: '{formatted_data['title']}' (유사도: {result.score:.3f})")
            return formatted_data
            
        except Exception as e:
            print(f"관광명소 검색 오류: {e}")
            import traceback
            traceback.print_exc()
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
    def _generate_final_response(message: str, results_data: List[Dict], is_kpop_mode: bool = False) -> str:
        """
        🎤 Lumi 컨셉 완전히 유지 (밸런스 조정)
        - K-pop 모드: 항상 GPT 사용 (매력적인 긴 응답)
        - 일반 모드: 템플릿 사용 (빠른 응답)
        """
        try:
            if not results_data:
                if is_kpop_mode:
                    return "어이쿠, Hunters! 😅 그 장소는 내 데이터베이스에 없네... 다른 멋진 곳 찾아볼까? 🔥"
                else:
                    return "안녕하세요! 축제나 관광명소에 대해 궁금한 것이 있으시면 언제든 물어보세요! 😊"
            
            result = results_data[0]
            result_type = result.get('type', 'festival')
            
            # 🎤 K-pop 모드: 항상 GPT 사용 (Lumi의 매력적인 스토리텔링)
            if is_kpop_mode:
                print("🎤 Lumi GPT 응답 (매력 유지)")
                return ChatService._kpop_gpt_response(message, result, result_type)
            
            # 📚 일반 모드: 템플릿 사용 (빠른 응답)
            else:
                print("📚 일반 템플릿 응답 (GPT 생략)")
                return ChatService._general_template_response(result, result_type)
                
        except Exception as e:
            print(f"❌ 응답 생성 오류: {e}")
            import traceback
            traceback.print_exc()
            if results_data:
                result = results_data[0]
                return f"🎯 {result.get('title')}을(를) 찾았습니다! 아래 정보를 확인해주세요 😊"
            else:
                return "안녕하세요! 궁금한 것이 있으시면 언제든 물어보세요! 😊"
    
    @staticmethod
    def _kpop_template_response(result: Dict, result_type: str) -> str:
        """
        🎤 Lumi 스타일 템플릿 응답 (GPT 없이 즉시 반환)
        - Demon Hunters 로어 자동 매칭
        - 장소별 스토리 삽입
        """
        title = result.get('title', '')
        description = result.get('description', '')
        
        # 🎭 Demon Hunters 장소 로어 (MV, 공연, 멤버 스토리)
        location_lore = {
            '남산': "우리의 궁극적인 감시탑! 🌙✨ 'Light in Darkness' MV 파이널 배틀 촬영지야! 서울 전체를 내려다보며 도시의 빛 에너지와 가장 강하게 연결되는 곳이지 💫⚔️",
            '타워': "우리의 궁극적인 감시탑! 🌙✨ 'Light in Darkness' MV 파이널 배틀 촬영지야!",
            '홍대': "Yo! 우리의 시작점! 🔥 Shadow랑 내가 데뷔 전에 버스킹하던 전설의 땅! 모든 스트릿 퍼포머들이 긍정 에너지를 퍼뜨리는 우리의 훈련장이자 사냥터야! 🎤⚔️",
            '강남': "'Neon Demons' 안무 영상 촬영 장소! 💫 탐욕으로 위장한 악마들이 숨어있는 화려한 구역이지 ⚔️",
            '북촌': "한국 전통 빛의 전사들에 대해 배운 고대 영적 땅! 🌙 전통 의상 컨셉에 영감을 준 곳이야 ✨",
            '한옥': "한국 전통 빛의 전사들에 대해 배운 고대 영적 땅! 🌙",
            '한강': "'Moonlight Hunter' 퍼포먼스 촬영지! 🌙 빛과 어둠을 가르는 정화의 강! 밤에 도시 불빛이 물에 반사되는 모습... 수천 명의 빛의 전사들이 우리와 함께 서있는 것 같아 ⚔️✨",
            '명동': "'Crystal Light' MV 촬영한 쇼핑 지구! ✨ 긍정적인 소비 에너지로 보호받는 곳이지!",
            '이태원': "다양한 빛 에너지가 융합하는 다문화 구역! 💫 국제 팬들이 가장 좋아하는 만남의 장소야!",
            '동대문': "기술과 마법이 만나는 미래형 전장! 🔥 우리 홀로그램 콘서트 장소지!",
            '경복궁': "고대 빛의 전사들이 왕국을 지킨 왕궁! 👑 우리 전통 의상 컨셉에 영감을 줬어 ⚔️",
            '궁': "고대 빛의 전사들이 왕국을 지킨 왕궁! 👑",
            '인사동': "예술적 에너지가 보호 장벽을 만드는 문화 거리! 🎨 내가 가사 영감을 얻는 곳이야 ✨",
            '롯데월드': "기쁨이 어둠을 물리치는 엔터테인먼트 영역! 🎢 깜짝 플래시몹 공연했던 곳! 🔥",
            '코엑스': "숨겨진 빛의 수정이 있다고 전해지는 지하 도시! 💎 우리 팬미팅 비밀 장소야 ✨",
            '서울숲': "나무 사이로 스며드는 빛이 영혼을 치유하는 자연 성소! 🌳 'Forest of Dreams' 뮤직비디오 촬영지 💫",
            '청계천': "어둠에서 부활한 서울을 상징하는 복원된 물길! 🌊 우리 발라드 MV의 로맨틱 스팟 💕",
        }
        
        # 장소명에서 키워드 찾기
        lore = ""
        for place, story in location_lore.items():
            if place in title:
                lore = f"\n\n{story}"
                break
        
        if result_type == 'festival':
            start_date = result.get('start_date', '')
            end_date = result.get('end_date', '')
            
            response = f"✨ Oh! '{title}'! Legendary 축제 발견! 💫\n\n"
            response += f"📅 {start_date} ~ {end_date}\n"
            
            if description:
                # description 요약 (처음 200자)
                desc_short = description[:200] + "..." if len(description) > 200 else description
                response += f"\n{desc_short}\n"
            
            # 로어가 있으면 추가, 없으면 기본 멘트
            if lore:
                response += lore
            else:
                response += "\n이 축제, 엄청 Dope할 것 같은데? 🔥 우리의 새로운 미션 장소가 될 수도!"
            
            response += "\n\n아래 카드에서 Details 체크해봐, Hunters! Let's go! ⚔️✨"
        
        else:  # attraction
            address = result.get('address', '')
            hours = result.get('hours_of_operation', '')
            
            response = f"🔥 Yo! '{title}'! 우리의 미션 장소! 💫\n\n"
            
            if address:
                response += f"📍 {address}\n"
            if hours and hours != "운영시간 정보 없음":
                response += f"⏰ {hours}\n"
            
            if description:
                desc_short = description[:200] + "..." if len(description) > 200 else description
                response += f"\n{desc_short}\n"
            
            # 로어가 있으면 추가, 없으면 기본 멘트
            if lore:
                response += lore
            else:
                response += "\n이곳 꼭 가봐야 해, Hunters! Legendary spot! 🌙 특별한 빛 에너지가 느껴질 거야!"
            
            response += "\n\nMore info 아래 카드에서! ✨⚔️"
        
        return response
    
    @staticmethod
    def _kpop_gpt_response(message: str, result: Dict, result_type: str) -> str:
        """
        🎤 Lumi 스타일 GPT 응답 (매력적인 긴 응답)
        - description 전체 사용
        - 4-6문장 길이 권장
        """
        title = result.get('title', '')
        description = result.get('description', '')  # 🎤 전체 사용!
        
        if result_type == 'festival':
            prompt = KPOP_FESTIVAL_QUICK_PROMPT.format(
                title=title,
                start_date=result.get('start_date', ''),
                end_date=result.get('end_date', ''),
                description=description[:500]  # ✅ 500자로 제한
            )
        else:
            prompt = KPOP_ATTRACTION_QUICK_PROMPT.format(
                title=title,
                address=result.get('address', ''),
                description=description[:500]  # ✅ 500자로 제한
            )
        
        response_messages = [{"role": "user", "content": prompt}]
        
        return chat_with_gpt(response_messages, max_tokens=250, temperature=0.6)
    
    @staticmethod
    def _general_template_response(result: Dict, result_type: str) -> str:
        """
        📚 일반 모드 템플릿 응답 (GPT 없이)
        """
        title = result.get('title', '')
        description = result.get('description', '')
        
        if result_type == 'festival':
            start_date = result.get('start_date', '')
            end_date = result.get('end_date', '')
            
            response = f"🎉 '{title}' 축제 정보입니다!\n\n"
            response += f"📅 기간: {start_date} ~ {end_date}\n\n"
            
            if description:
                desc_short = description[:300] + "..." if len(description) > 300 else description
                response += f"{desc_short}\n\n"
            
            response += "자세한 정보는 아래 카드에서 확인해주세요! 😊"
        
        else:  # attraction
            address = result.get('address', '')
            hours = result.get('hours_of_operation', '')
            
            response = f"📍 '{title}' 정보입니다!\n\n"
            
            if address:
                response += f"📍 주소: {address}\n"
            if hours and hours != "운영시간 정보 없음":
                response += f"⏰ 운영시간: {hours}\n\n"
            
            if description:
                desc_short = description[:300] + "..." if len(description) > 300 else description
                response += f"{desc_short}\n\n"
            
            response += "추가 정보는 아래 카드를 확인해주세요! 😊"
        
        return response
    
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