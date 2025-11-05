import React, { useState, useEffect } from 'react';
import '../styles/ScheduleTable.css';

// ⭐ onDayTitleChange prop 추가
const ScheduleTable = ({ scheduleId, onDayTitleChange }) => {
    const [token, setToken] = useState(localStorage.getItem('session_id'));
    
    const [dayTitles, setDayTitles] = useState([]);
    const [selectedDayTitle, setSelectedDayTitle] = useState('');
    const [description, setDescription] = useState('');
    const [authError, setAuthError] = useState(null);

    const fetchWithAuth = async (url, options = {}) => {
        setAuthError(null);

        if (!token) {
            const error = new Error("세션이 없습니다. 로그인해주세요");
            setAuthError(error.message);
            throw error; 
        }

        const headers = {
            ...options.headers,
            Authorization: `Bearer ${token}`, 
            'Content-Type': 'application/json'
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.status === 401) {
                const error = new Error('로그인이 만료되었습니다. 다시 로그인해주세요.');
                setAuthError(error.message); 
                localStorage.removeItem('session_id');
                setToken(null);

                setTimeout(() => {
                    window.location.href = '/'; 
                }, 2000); 

                throw error;
            }
            
            if (!response.ok) {
                const errorDetail = await response.json().catch(() => ({}));
                const errorMessage = errorDetail.detail || `API 요청 실패: ${response.status} ${response.statusText}`;
                throw new Error(errorMessage);
            }

            return response;

        } catch (error) {
            console.error("❌ fetch 실패:", error);
            throw error;
        }
    };

    // 1️⃣ day_titles 가져오기
    useEffect(() => {
        if (!token) return; 

        console.log("🔍 day_titles API 호출 시작");
        
        fetchWithAuth('http://localhost:8000/api/schedules/day_titles')
          .then(res => res.json())
          .then(data => {
            console.log("✅ day_titles 응답 데이터:", data);
            
            setDayTitles(data.map(d => d.day_title)); 
            
            if (data.length > 0) {
                setSelectedDayTitle(data[0].day_title);
                console.log("✅ 첫 번째 day_title 선택:", data[0].day_title);
                
                // ⭐ 첫 번째 일정 선택 시 부모에게 알림
                if (onDayTitleChange) {
                    onDayTitleChange(data[0].day_title);
                }
            } else {
                console.warn("⚠️ day_titles가 비어있습니다");
            }
          })
          .catch(err => {
            console.error("❌ day_titles fetch 실패:", err.message);
          });
          
    }, [token]);

    // 2️⃣ schedule 상세 가져오기
    useEffect(() => {
      if (!scheduleId || !token) return;

      console.log(`🔍 Schedule ${scheduleId} 상세 정보 가져오기`);

      fetchWithAuth(`http://localhost:8000/api/schedules/${scheduleId}`)
        .then(res => res.json())
        .then(data => {
          console.log("✅ Schedule 상세 데이터:", data);
          if (data.day_title) {
            setSelectedDayTitle(data.day_title);
            // ⭐ 부모에게 알림
            if (onDayTitleChange) {
                onDayTitleChange(data.day_title);
            }
          }
          if (data.description) setDescription(data.description);
        })
        .catch(err => console.error("❌ Schedule fetch 실패:", err.message));
        
    }, [scheduleId, token]);

    // 3️⃣ 선택된 day_title에 따른 description 갱신
    useEffect(() => {
        if (!selectedDayTitle || !token) return;
        
        console.log(`🔍 ${selectedDayTitle}의 description 가져오기`);
        
        fetchWithAuth(
          `http://localhost:8000/api/schedules/description?day_title=${encodeURIComponent(selectedDayTitle)}`
        )
          .then(res => res.json())
          .then(data => {
            console.log("✅ description 데이터:", data);
            setDescription(data.description || '');
          })
          .catch(err => console.error("❌ description fetch 실패:", err.message));
          
    }, [selectedDayTitle, token]);

    // 4️⃣ description 저장
    const handleSave = () => {
        if (!selectedDayTitle || !token) return;

        console.log(`💾 저장 시작: ${selectedDayTitle}`);

        fetchWithAuth(
          `http://localhost:8000/api/schedules/update_description?day_title=${encodeURIComponent(selectedDayTitle)}&description=${encodeURIComponent(description)}`,
          { method: "PUT" }
        )
          .then(res => res.json())
          .then((data) => {
            console.log("✅ 저장 성공:", data);
            alert("✅ 저장되었습니다!");
          })
          .catch(err => {
            console.error("❌ 저장 실패", err.message);
            if (!authError) {
              alert(`❌ 저장 실패: ${err.message}`);
            }
          });
    };

    // ⭐ day_title 변경 핸들러
    const handleDayTitleChange = (e) => {
        const newDayTitle = e.target.value;
        setSelectedDayTitle(newDayTitle);
        
        // 부모 컴포넌트에 변경 알림
        if (onDayTitleChange) {
            onDayTitleChange(newDayTitle);
        }
    };

    const days = ['Location', 'Estimated Cost', 'Place of use', 'Memo', 'Notice'];
    const times = ['9:00', '10:00', '11:00'];

    return (
        <div className="kschedule-container">
            <header className="kschedule-header">
                <h1>🗓️ Schedule Management and Editor</h1>
            </header>

            {authError && (
                <div className="kdh-error-message">
                    <p>🛑 **에러:** {authError}</p>
                    {authError.includes('로그인') && (
                        <p>잠시 후 메인 페이지로 이동합니다...</p>
                    )}
                </div>
            )}

            {!authError && (
                <>
                    <div className="kschedule-details">
                        <label>Day Title</label>
                        <select
                          className="kschedule-select"
                          value={selectedDayTitle}
                          onChange={handleDayTitleChange} // ⭐ 변경됨
                        >
                            {dayTitles.length === 0 && (
                                <option value="">일정이 없습니다</option>
                            )}
                            {dayTitles.map((day, idx) => (
                                <option key={idx} value={day}>{day}</option>
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
                </>
            )}

            <div className="kschedule-table-dots">
                <span>...</span>
            </div>
        </div>
    );
};

export default ScheduleTable;