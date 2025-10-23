"""
여행지 관련 데이터베이스 쿼리 및 비즈니스 로직 통합
"""

class DestinationQueries:
    """여행지 테이블 쿼리 및 비즈니스 로직"""
    
    # ============================================
    # 기본 CRUD 쿼리
    # ============================================
    
    @staticmethod
    def create_destination(cursor, user_id: int, name: str, extracted_from_convers_id: int = None):
        """새 여행지 생성"""
        query = """
        INSERT INTO destinations (user_id, name, extracted_from_convers_id)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (user_id, name, extracted_from_convers_id))
        return cursor.lastrowid
    
    @staticmethod
    def create_destinations_bulk(cursor, user_id: int, destination_names: list, convers_id: int = None):
        """여러 여행지 한번에 생성"""
        if not destination_names:
            return []
        
        query = """
        INSERT INTO destinations (user_id, name, extracted_from_convers_id)
        VALUES (%s, %s, %s)
        """
        
        inserted_ids = []
        for name in destination_names:
            cursor.execute(query, (user_id, name, convers_id))
            inserted_ids.append(cursor.lastrowid)
        
        return inserted_ids
    
    @staticmethod
    def get_user_destinations(cursor, user_id: int, limit: int = 100, offset: int = 0):
        """사용자의 여행지 목록 조회"""
        query = """
        SELECT destination_id, name, extracted_from_convers_id, created_at
        FROM destinations
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        cursor.execute(query, (user_id, limit, offset))
        return cursor.fetchall()
    
    @staticmethod
    def get_destination_by_id(cursor, destination_id: int):
        """여행지 ID로 조회"""
        query = """
        SELECT destination_id, user_id, name, extracted_from_convers_id, created_at
        FROM destinations
        WHERE destination_id = %s
        """
        cursor.execute(query, (destination_id,))
        return cursor.fetchone()
    
    @staticmethod
    def delete_destination(cursor, destination_id: int, user_id: int):
        """여행지 삭제 (본인 것만)"""
        query = "DELETE FROM destinations WHERE destination_id = %s AND user_id = %s"
        cursor.execute(query, (destination_id, user_id))
        return cursor.rowcount > 0
    
    @staticmethod
    def destination_exists(cursor, user_id: int, name: str) -> bool:
        """같은 이름의 여행지가 이미 존재하는지 확인"""
        query = "SELECT COUNT(*) as count FROM destinations WHERE user_id = %s AND name = %s"
        cursor.execute(query, (user_id, name))
        result = cursor.fetchone()
        return result['count'] > 0
    
    @staticmethod
    def count_user_destinations(cursor, user_id: int):
        """사용자의 총 여행지 수"""
        query = "SELECT COUNT(*) as count FROM destinations WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        return result['count']
    
    # ============================================
    # 비즈니스 로직 (기존 DestinationService에서 이동)
    # ============================================
    
    @staticmethod
    def add_destinations(conn, cursor, user_id: int, destination_names: list, convers_id: int = None):
        """
        여행지 추가 (중복 제거)
        
        Args:
            conn: DB 연결
            cursor: DB 커서
            user_id: 사용자 ID
            destination_names: 여행지 이름 리스트
            convers_id: 대화 ID (선택)
        
        Returns:
            추가된 여행지 ID 리스트
        """
        added_ids = []
        
        for name in destination_names:
            # 중복 체크
            if not DestinationQueries.destination_exists(cursor, user_id, name):
                dest_id = DestinationQueries.create_destination(
                    cursor, user_id, name, convers_id
                )
                added_ids.append(dest_id)
        
        conn.commit()
        return added_ids
    
    @staticmethod
    def get_destinations_count(cursor, user_id: int):
        """
        사용자의 총 여행지 수 (별칭 메서드)
        기존 DestinationService와의 호환성을 위해 유지
        """
        return DestinationQueries.count_user_destinations(cursor, user_id)
    
    @staticmethod
    def delete_destination_with_commit(conn, cursor, destination_id: int, user_id: int):
        """
        여행지 삭제 (커밋 포함)
        기존 DestinationService.delete_destination와 동일한 동작
        
        Args:
            conn: DB 연결
            cursor: DB 커서
            destination_id: 여행지 ID
            user_id: 사용자 ID
        
        Returns:
            삭제 성공 여부
        """
        success = DestinationQueries.delete_destination(
            cursor, destination_id, user_id
        )
        
        if success:
            conn.commit()
        
        return success


# ============================================
# 호환성을 위한 별칭 클래스 (기존 코드 변경 최소화)
# ============================================

class DestinationService:
    """
    기존 DestinationService와의 호환성을 위한 별칭 클래스
    실제 로직은 DestinationQueries에서 처리
    """
    
    @staticmethod
    def add_destinations(conn, cursor, user_id: int, destination_names: list, convers_id: int = None):
        return DestinationQueries.add_destinations(conn, cursor, user_id, destination_names, convers_id)
    
    @staticmethod
    def get_user_destinations(cursor, user_id: int, limit: int = 100):
        return DestinationQueries.get_user_destinations(cursor, user_id, limit)
    
    @staticmethod
    def delete_destination(conn, cursor, destination_id: int, user_id: int):
        return DestinationQueries.delete_destination_with_commit(conn, cursor, destination_id, user_id)
    
    @staticmethod
    def get_destinations_count(cursor, user_id: int):
        return DestinationQueries.get_destinations_count(cursor, user_id)