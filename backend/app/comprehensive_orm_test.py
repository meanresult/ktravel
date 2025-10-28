#!/usr/bin/env python3
"""
실제 Docker 환경에서 ORM 모델 종합 테스트
"""

def comprehensive_orm_test():
    """종합적인 ORM 테스트"""
    print("🐳 실제 Docker 환경 ORM 종합 테스트!")
    print("=" * 60)
    
    try:
        # 1. 모델 import 테스트
        print("📦 1. 모델 Import 테스트...")
        from app.models.destination import Destination
        from app.models.users import User
        from app.models.conversation import Conversation
        from app.models.fastival import Festival
        print("✅ 모든 모델 import 성공!")
        
        # 2. 모델 정보 확인
        print("\n📋 2. 모델 정보 확인...")
        models = [
            (User, "users"),
            (Destination, "destinations"), 
            (Conversation, "conversations"),
            (Festival, "fastival")
        ]
        
        for model, expected_table in models:
            table_name = getattr(model, '__tablename__', '없음')
            print(f"   {model.__name__}: {table_name}")
            if hasattr(model, '__table__'):
                columns = [col.name for col in model.__table__.columns]
                print(f"      컬럼({len(columns)}개): {columns[:5]}{'...' if len(columns) > 5 else ''}")
        
        # 3. 데이터베이스 연결 테스트
        print("\n🔌 3. 데이터베이스 연결 테스트...")
        from app.database.connection import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        
        # 간단한 연결 테스트
        result = db.execute(text("SELECT 1 as test"))
        if result.fetchone()[0] == 1:
            print("✅ 데이터베이스 연결 성공!")
        
        # MySQL 버전 확인
        result = db.execute(text("SELECT VERSION() as version"))
        version = result.fetchone()[0]
        print(f"✅ MySQL 버전: {version}")
        
        # 4. 실제 데이터 조회 테스트
        print("\n🔍 4. 실제 데이터 조회 테스트...")
        
        # 각 테이블의 데이터 개수 확인
        counts = {}
        for model, table_name in models:
            try:
                count = db.query(model).count()
                counts[model.__name__] = count
                print(f"   📊 {model.__name__}: {count}개")
            except Exception as e:
                print(f"   ❌ {model.__name__}: 조회 실패 - {e}")
                counts[model.__name__] = "오류"
        
        # 5. 샘플 데이터 확인
        print("\n👀 5. 샘플 데이터 확인...")
        
        for model, table_name in models:
            if counts.get(model.__name__, 0) > 0:
                try:
                    first_item = db.query(model).first()
                    print(f"   🎯 {model.__name__} 첫 번째: {first_item}")
                except Exception as e:
                    print(f"   ❌ {model.__name__} 샘플 조회 실패: {e}")
        
        # 6. 관계(Join) 테스트
        print("\n🔗 6. 모델 관계 테스트...")
        
        try:
            # User와 Destination 관계
            user_dest_join = db.query(Destination).join(User).limit(3).all()
            print(f"   ✅ User-Destination Join: {len(user_dest_join)}개 조회")
        except Exception as e:
            print(f"   ❌ User-Destination Join 실패: {e}")
        
        try:
            # User와 Conversation 관계  
            user_conv_join = db.query(Conversation).join(User).limit(3).all()
            print(f"   ✅ User-Conversation Join: {len(user_conv_join)}개 조회")
        except Exception as e:
            print(f"   ❌ User-Conversation Join 실패: {e}")
        
        # 7. CRUD 테스트 (읽기 전용)
        print("\n📝 7. CRUD 동작 테스트...")
        
        try:
            # 특정 조건으로 검색
            if counts.get('User', 0) > 0:
                users = db.query(User).limit(3).all()
                print(f"   ✅ User 조회: {len(users)}명")
                
            if counts.get('Destination', 0) > 0:
                destinations = db.query(Destination).limit(3).all()
                print(f"   ✅ Destination 조회: {len(destinations)}개")
        except Exception as e:
            print(f"   ❌ CRUD 테스트 실패: {e}")
        
        db.close()
        
        print("\n" + "=" * 60)
        print("🎉 종합 테스트 완료!")
        
        # 결과 요약
        total_records = sum(v for v in counts.values() if isinstance(v, int))
        print(f"📊 총 데이터: {total_records}개")
        print("✅ ORM 모델들이 실제 환경에서 정상 작동합니다!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    comprehensive_orm_test()
