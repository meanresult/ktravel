import React, { useState, useEffect } from 'react';
import '../styles/ScheduleTable.css';

// ⚠️ 참고: 컴포넌트 인자에서 scheduleId는 사용하지만, sessionId는 내부에서 로컬 스토리지에서 가져옵니다.
//       외부에서 받아오는 props는 주석 처리하거나 제거할 수 있습니다.
const ScheduleTable = ({ scheduleId }) => { 
    const [dayTitles, setDayTitles] = useState([]);
    const [selectedDayTitle, setSelectedDayTitle] = useState('');
    const [description, setDescription] = useState('');
    const [authError, setAuthError] = useState(null); // 인증 에러 상태 추가
    
    // 세션 ID를 로컬 스토리지에서 가져옵니다.
    const getSessionId = () => localStorage.getItem('session_id');

    // ✅ 공통 fetch 함수 (인증 및 에러 처리 강화)
    const fetchWithAuth = async (url, options = {}) => {
        const sessionId = getSessionId(); // 로컬 스토리지에서 토큰 가져오기
        setAuthError(null); // 새로운 요청 시작 시 에러 초기화

        if (!sessionId) {
            const error = new Error("세션이 없습니다. 로그인해주세요");
            setAuthError(error.message);
            throw error;
        }

        const headers = {
            ...options.headers,
            // 챗봇 페이지와 동일하게 'Bearer <sessionId>' 형식 사용
            Authorization: `Bearer ${sessionId}`, 
            'Content-Type': 'application/json'
        };

        // ➡️ DEBUG: Authorization Header 출력 (디버깅 목적)
        // console.log("➡️ DEBUG (FETCH): Authorization Header:", headers.Authorization);

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            // 챗봇 페이지와 동일한 401 Unauthorized 처리 로직
            if (response.status === 401) {
                const error = new Error('로그인이 만료되었습니다. 다시 로그인해주세요.');
                setAuthError(error.message); // 에러 상태 업데이트
                localStorage.removeItem('session_id'); // 토큰 삭제
                
                // 챗봇 페이지와 동일하게 리디렉션 처리
                setTimeout(() => {
                    window.location.href = '/'; // 메인 페이지로 이동
                }, 2000); 

                throw error;
            }

            if (!response.ok) {
                throw new Error(`API 요청 실패: ${response.status} ${response.statusText}`);
            }

            return response;

        } catch (error) {
            // 이 throw는 위 401 처리에서 이미 이루어졌거나, 네트워크 에러일 때 실행됩니다.
            console.error("❌ fetch 실패:", error);
            throw error;
        }
    };

    // 1️⃣ day_titles 가져오기
    useEffect(() => {
        const sessionId = getSessionId();
        if (!sessionId) return; // 토큰 없으면 API 호출 방지

        fetchWithAuth('http://localhost:8000/api/schedules/day_titles')
          .then(res => res.json())
          .then(data => {
            setDayTitles(data.map(d => d.day_title)); 
            if (data.length > 0) setSelectedDayTitle(data[0].day_title);
          })
          .catch(err => console.error("❌ day_titles fetch 실패:", err.message));
    }, []); // sessionId가 아닌 빈 배열로 변경: 컴포넌트 마운트 시 한 번만 실행

    // 2️⃣ schedule 상세 가져오기
    useEffect(() => {
      const sessionId = getSessionId();
      if (!scheduleId || !sessionId) return;

      fetchWithAuth(`http://localhost:8000/api/schedules/${scheduleId}`)
        .then(res => res.json())
        .then(data => {
          if (data.day_title) setSelectedDayTitle(data.day_title);
          if (data.description) setDescription(data.description);
        })
        .catch(err => console.error("❌ Schedule fetch 실패:", err.message));
    }, [scheduleId]); // sessionId가 아닌 빈 배열로 변경: 컴포넌트 마운트 시 한 번만 실행 (prop 의존성 유지)

    // 3️⃣ 선택된 day_title에 따른 description 갱신
    useEffect(() => {
        const sessionId = getSessionId();
        if (!selectedDayTitle || !sessionId) return;
        
        // selectedDayTitle 변경 시 항상 호출되도록 로직 유지
        fetchWithAuth(
          `http://localhost:8000/api/schedules/description?day_title=${encodeURIComponent(selectedDayTitle)}`
        )
          .then(res => res.json())
          .then(data => setDescription(data.description || ''))
          .catch(err => console.error("❌ description fetch 실패:", err.message));
    }, [selectedDayTitle]); // sessionId 의존성 제거

    // 4️⃣ description 저장
    const handleSave = () => {
        const sessionId = getSessionId();
        if (!selectedDayTitle || !sessionId) return;

        fetchWithAuth(
          `http://localhost:8000/api/schedules/update_description?day_title=${encodeURIComponent(selectedDayTitle)}&description=${encodeURIComponent(description)}`,
          { method: "PUT" }
        )
          .then(res => res.json())
          .then(() => alert("✅ 저장되었습니다!"))
          .catch(err => {
            console.error("❌ 저장 실패", err.message);
            // 401 에러는 fetchWithAuth에서 이미 처리됩니다.
            if (!authError) {
              alert("❌ 저장 실패");
            }
          });
    };

    const days = ['Location', 'Estimated Cost', 'Place of use', 'Memo', 'Notice'];
    const times = ['9:00', '10:00', '11:00'];

    return (
      <div className="kschedule-container">
        <header className="kschedule-header">
          <h1>🗓️ Schedule Management and Editor</h1>
        </header>

        {/* 🚨 인증 에러 메시지 출력 영역 추가 🚨 */}
        {authError && (
            <div className="kdh-error-message">
                <p>🛑 **에러:** {authError}</p>
                {/* 챗봇 페이지의 리디렉션 스타일 */}
                {authError.includes('로그인') && (
                    <p>잠시 후 메인 페이지로 이동합니다...</p>
                )}
            </div>
        )}

        {/* 인증 에러가 발생하면 나머지 컴포넌트는 숨김 */}
        {!authError && (
          <div className="kschedule-details">
            <label>Day Title</label>
            <select
              className="kschedule-select"
              value={selectedDayTitle}
              onChange={(e) => setSelectedDayTitle(e.target.value)}
            >
              {dayTitles.map(day => (
                <option key={day} value={day}>{day}</option>
              ))}
            </select>

            <label>Description</label>
            <textarea
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />

            <button className="kschedule-btn kschedule-btn-success" onClick={handleSave}>
              ✅ Save
            </button>
          </div>
        )}
        
        {/* ... (나머지 테이블 렌더링 로직) */}
        {!authError && (
            <div className="kschedule-table-wrapper">
              <table className="kschedule-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    {days.map((day, idx) => <th key={idx}>{day}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {times.map((time, ti) => (
                    <tr key={ti}>
                      <td className="kschedule-time-cell">{time}</td>
                      {days.map((_, di) => (
                        <td key={di} className="kschedule-schedule-cell"></td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
        )}

        <div className="kschedule-table-dots">
          <span>...</span>
        </div>
      </div>
    );
};

export default ScheduleTable;