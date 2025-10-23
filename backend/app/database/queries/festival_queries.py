"""
축제 관련 데이터베이스 쿼리 및 비즈니스 로직 통합
"""

class FestivalQueries:
    """축제 테이블 쿼리 및 비즈니스 로직"""
    
    # ============================================
    # 기본 CRUD 쿼리
    # ============================================
    
    @staticmethod
    def get_all(cursor, filter_type: str = None, limit: int = 100, offset: int = 0):
        """모든 축제 조회"""
        if filter_type:
            query = """
            SELECT * FROM fastival 
            WHERE filter_type = %s
            LIMIT %s OFFSET %s
            """
            cursor.execute(query, (filter_type, limit, offset))
        else:
            query = """
            SELECT * FROM fastival 
            LIMIT %s OFFSET %s
            """
            cursor.execute(query, (limit, offset))
        
        return cursor.fetchall()
    
    @staticmethod
    def get_by_id(cursor, festival_id: int):
        """특정 축제 조회"""
        query = """
        SELECT * FROM fastival 
        WHERE fastival_id = %s
        """
        cursor.execute(query, (festival_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_ongoing(cursor):
        """진행 중인 축제 조회"""
        query = """
        SELECT * FROM fastival 
        WHERE start_date <= CURDATE() 
        AND end_date >= CURDATE()
        """
        cursor.execute(query)
        return cursor.fetchall()
    
    @staticmethod
    def get_upcoming(cursor):
        """예정된 축제 조회"""
        query = """
        SELECT * FROM fastival 
        WHERE start_date > CURDATE()
        ORDER BY start_date ASC
        """
        cursor.execute(query)
        return cursor.fetchall()
    
    @staticmethod
    def search(cursor, search_query: str):
        """축제 검색 (제목, 설명)"""
        query = """
        SELECT * FROM fastival 
        WHERE title LIKE %s 
        OR description LIKE %s
        """
        search_term = f"%{search_query}%"
        cursor.execute(query, (search_term, search_term))
        return cursor.fetchall()
    
    @staticmethod
    def count_all(cursor, filter_type: str = None):
        """전체 축제 수 조회"""
        if filter_type:
            query = "SELECT COUNT(*) as count FROM fastival WHERE filter_type = %s"
            cursor.execute(query, (filter_type,))
        else:
            query = "SELECT COUNT(*) as count FROM fastival"
            cursor.execute(query)
        
        result = cursor.fetchone()
        return result['count']
    
    @staticmethod
    def get_by_date_range(cursor, start_date, end_date):
        """특정 날짜 범위의 축제 조회"""
        query = """
        SELECT * FROM fastival 
        WHERE (start_date BETWEEN %s AND %s)
        OR (end_date BETWEEN %s AND %s)
        OR (start_date <= %s AND end_date >= %s)
        ORDER BY start_date ASC
        """
        cursor.execute(query, (start_date, end_date, start_date, end_date, start_date, end_date))
        return cursor.fetchall()
    
    @staticmethod
    def festival_exists(cursor, festival_id: int) -> bool:
        """축제 존재 여부 확인"""
        query = "SELECT COUNT(*) as count FROM fastival WHERE fastival_id = %s"
        cursor.execute(query, (festival_id,))
        result = cursor.fetchone()
        return result['count'] > 0
    
    # ============================================
    # 비즈니스 로직 (기존 endpoint에서 이동)
    # ============================================
    
    @staticmethod
    def get_all_festivals_with_error_handling(cursor, filter_type: str = None, skip: int = 0, limit: int = 100):
        """
        모든 축제 조회 (에러 핸들링 포함)
        기존 endpoint의 비즈니스 로직을 이동
        """
        try:
            festivals = FestivalQueries.get_all(cursor, filter_type, limit, skip)
            return {"success": True, "data": festivals}
        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_festival_by_id_with_validation(cursor, festival_id: int):
        """
        특정 축제 조회 (검증 포함)
        기존 endpoint의 비즈니스 로직을 이동
        """
        try:
            festival = FestivalQueries.get_by_id(cursor, festival_id)
            if not festival:
                return {"success": False, "error": "Festival not found", "status_code": 404}
            return {"success": True, "data": festival}
        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_ongoing_festivals_with_error_handling(cursor):
        """
        진행 중인 축제 조회 (에러 핸들링 포함)
        """
        try:
            festivals = FestivalQueries.get_ongoing(cursor)
            return {"success": True, "data": festivals}
        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_upcoming_festivals_with_error_handling(cursor):
        """
        예정된 축제 조회 (에러 핸들링 포함)
        """
        try:
            festivals = FestivalQueries.get_upcoming(cursor)
            return {"success": True, "data": festivals}
        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def search_festivals_with_error_handling(cursor, search_query: str):
        """
        축제 검색 (에러 핸들링 포함)
        """
        try:
            festivals = FestivalQueries.search(cursor, search_query)
            return {"success": True, "data": festivals}
        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
            return {"success": False, "error": str(e)}


# ============================================
# 호환성을 위한 별칭 클래스 (기존 코드 변경 최소화)
# ============================================

class FestivalService:
    """
    기존 FestivalService와의 호환성을 위한 별칭 클래스
    실제 로직은 FestivalQueries에서 처리
    """
    
    @staticmethod
    def get_all_festivals(cursor, filter_type=None, skip=0, limit=100):
        return FestivalQueries.get_all_festivals_with_error_handling(cursor, filter_type, skip, limit)
    
    @staticmethod
    def get_festival_by_id(cursor, festival_id):
        return FestivalQueries.get_festival_by_id_with_validation(cursor, festival_id)
    
    @staticmethod
    def get_ongoing_festivals(cursor):
        return FestivalQueries.get_ongoing_festivals_with_error_handling(cursor)
    
    @staticmethod
    def get_upcoming_festivals(cursor):
        return FestivalQueries.get_upcoming_festivals_with_error_handling(cursor)
    
    @staticmethod
    def search_festivals(cursor, query):
        return FestivalQueries.search_festivals_with_error_handling(cursor, query)