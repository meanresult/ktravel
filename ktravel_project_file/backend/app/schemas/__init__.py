# backend/app/schemas/__init__.py

# User 스키마들
from .user_schema import (
    UserBase,
    UserCreate, 
    UserResponse,
    UserLogin,
    Token,
    TokenData
)

# Destination 스키마들  
from .destination_schema import (
    DestinationBase,
    DestinationCreate,
    DestinationResponse,
    DestinationFromConversation,
    DestinationAddRequest,
    DestinationAddResponse
)

# Conversation 스키마들
from .conversation_schema import (
    ConversationBase,
    ConversationCreate,
    ConversationResponse,
    ChatMessage,
    ChatResponse
)

# Festival 스키마들
from .festival_schema import (
    FestivalBase,
    FestivalResponse,
    FestivalCard,
    MapMarker
)

from .concert_schema import (
    ConcertBase,
    ConcertCreate,
    ConcertUpdate,
    ConcertResponse,
    ConcertSummary,
    ConcertsResponse,
    OngoingConcertsResponse,
    ConcertSearch,
    ConcertDateRange
)

from .schedule_schema import ScheduleEdit, ScheduleResponse

# KContent 스키마들
from .kcontent_schema import (
    KContentCreate,
    KContentEdit,
    KContentResponse
)

from .schedule_table_meta_schema import (
    ScheduleTableRowData, 
    UpdateScheduleTableRequest, 
    ScheduleTableDataResponse
)

# ✅ 북마크 스키마 (BookmarkBase 제거!)
from .bookmarkschema import (
    PlaceType,              # ✅ 추가
    BaseResponse,
    BookmarkCreate,
    BookmarkListResponse,
    BookmarkForRecommend,   # ✅ 추가
)

from .recommend_schema import (
    BookmarkBasedRecommendRequest,
    RecommendedItem,
    BookmarkBasedRecommendResponse,
)

__all__ = [
    # User
    "UserBase", "UserCreate", "UserResponse", 
    "UserLogin", "Token", "TokenData",
    
    # Destination  
    "DestinationBase", "DestinationCreate",
    "DestinationResponse", "DestinationFromConversation",
    "DestinationAddRequest", "DestinationAddResponse",
    
    # Conversation
    "ConversationBase", "ConversationCreate", 
    "ConversationResponse", "ChatMessage", "ChatResponse",
    
    # Concert
    "ConcertBase", "ConcertCreate", "ConcertUpdate", "ConcertResponse",
    "ConcertSummary", "ConcertsResponse", "OngoingConcertsResponse",
    "ConcertSearch", "ConcertDateRange",
    
    # Festival
    "FestivalBase", "FestivalResponse", "FestivalCard", "MapMarker",
    
    # Schedule
    "ScheduleEdit", "ScheduleResponse",

    # KContent
    "KContentCreate", "KContentEdit", "KContentResponse",
    
    # Schedule Table
    "ScheduleTableRowData", "UpdateScheduleTableRequest", "ScheduleTableDataResponse",

    # ✅ Bookmark (BookmarkBase 제거, PlaceType 추가)
    "PlaceType",            # ✅ 추가
    "BaseResponse",
    "BookmarkCreate",
    "BookmarkListResponse",
    "BookmarkForRecommend", # ✅ 추가
    
    # Recommend
    "BookmarkBasedRecommendRequest",
    "RecommendedItem",
    "BookmarkBasedRecommendResponse",
]