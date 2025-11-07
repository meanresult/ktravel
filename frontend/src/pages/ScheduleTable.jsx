import React, { useState, useEffect, useCallback } from 'react';
import { Trash2, GripVertical } from 'lucide-react'; 
import '../styles/ScheduleTable.css';
import { DragDropContext, Droppable, Draggable } from "react-beautiful-dnd";

// ✅ 컴포넌트 외부 함수: 인증 기반 Fetch 로직 (useCallback 의존성 최소화 목적)
const globalFetchWithAuth = async (url, options = {}, token, setToken, setAuthError) => {
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
        const response = await fetch(url, { ...options, headers });

        if (response.status === 401) {
            const error = new Error('로그인이 만료되었습니다. 다시 로그인해주세요.');
            setAuthError(error.message); 
            localStorage.removeItem('session_id');
            setToken(null);
            setTimeout(() => { window.location.href = '/'; }, 2000); 
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


const ScheduleTable = ({ scheduleId, onDayTitleChange }) => {
    const [token, setToken] = useState(localStorage.getItem('session_id'));
    const [dayTitles, setDayTitles] = useState([]);
    const [selectedDayTitle, setSelectedDayTitle] = useState('');
    const [description, setDescription] = useState('');
    const [authError, setAuthError] = useState(null);
    const [isLoadingDestinations, setIsLoadingDestinations] = useState(false); 
    
    // 삭제 모드 (행/열)
    const [isDeletionModeActive, setIsDeletionModeActive] = useState(false); 

    // 기본 데이터
    const initialDays = ['Location', 'Estimated Cost', 'Place of use', 'Memo', 'Notice'];
    const initialTimes = ['9:00', '10:00', '11:00'];
    const locationColumnName = 'Location';
    const [scheduleTimes, setScheduleTimes] = useState(initialTimes);
    const [scheduleDays, setScheduleDays] = useState(initialDays);
    
    // 셀 데이터 (time-day 키)
    const [cellData, setCellData] = useState({});
    
    // 유틸리티 함수: ID 안전하게 변경 (DnD 오류 방지)
    const sanitizeId = useCallback((str) => String(str).replace(/[^a-zA-Z0-9_-]/g, '_'), []);
    
    // fetchWithAuth를 전역 함수에 연결
    const fetchWithAuth = useCallback((url, options = {}) => 
        globalFetchWithAuth(url, options, token, setToken, setAuthError), 
    [token]);


    // --- 🚨 목적지 데이터 Fetch 및 연동 로직 (핵심) ---
    const fetchDestinations = useCallback(async () => {
    if (!selectedDayTitle || !token) return;

    setIsLoadingDestinations(true);
    
    try {
        const response = await fetchWithAuth(
            `http://localhost:8000/api/destinations/by-schedule?day_title=${encodeURIComponent(selectedDayTitle)}`
        );

        const destinations = await response.json();
        const numDestinations = destinations.length;
        const locationColumnName = 'Location'; 
        let newTimesArray = []; // 새로 계산된 시간 배열을 저장할 임시 변수

        // 1. 시간 행 (scheduleTimes) 동적 조정 및 업데이트
        setScheduleTimes(prevTimes => {
            const numCurrentTimes = prevTimes.length;
            
            // A. 목적지 수가 현재 행보다 적거나 같을 때: 행을 잘라냄 (유동적 줄이기)
            if (numDestinations <= numCurrentTimes) {
                newTimesArray = prevTimes.slice(0, numDestinations);
                return newTimesArray;
            }
            
            // B. 목적지 수가 현재 행보다 많을 때: 행을 추가 (유동적 늘리기)
            const timesToAdd = numDestinations - numCurrentTimes;
            newTimesArray = [...prevTimes];

            for (let i = 0; i < timesToAdd; i++) {
                const lastTimeStr = newTimesArray[newTimesArray.length - 1] || '08:00';
                const [hourStr, minuteStr] = lastTimeStr.split(':');
                let hour = parseInt(hourStr);
                let minute = parseInt(minuteStr);
                
                hour = (hour + 1) % 24; 
                const newTime = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
                newTimesArray.push(newTime);
            }
            return newTimesArray;
        });
        
        // 2. 데이터 매핑 로직 (newTimesArray를 사용하여 즉시 실행)
        let newLocationData = {};

        // newTimesArray는 setScheduleTimes 내에서 계산된 목적지 수만큼의 길이입니다.
        for(let i = 0; i < newTimesArray.length; i++) {
            const time = newTimesArray[i];
            const destinationName = destinations[i]?.name;
            
            if (time && destinationName) {
                const key = `${time}-${locationColumnName}`; 
                newLocationData[key] = destinationName;
            }
        }

        // 3. cellData 업데이트 (Location 열만 새 데이터로 덮어쓰고, 기존 데이터는 유지)
        setCellData(prevCellData => {
            // 다른 열의 데이터(메모, 비용 등)는 유지
            const updatedCellData = { ...prevCellData };
            
            // Location 열 데이터는 새로 가져온 것으로 덮어씀
            return {
                ...updatedCellData, 
                ...newLocationData
            };
        });

    } catch (error) {
        console.error("❌ 목적지 조회 및 연동 실패:", error.message);
    } finally {
        setIsLoadingDestinations(false);
    }
}, [selectedDayTitle, token, fetchWithAuth, scheduleDays]);

    // selectedDayTitle 변경 시 목적지 데이터를 다시 가져옵니다.
    useEffect(() => {
        fetchDestinations();
    }, [fetchDestinations]);
    // -----------------------------------------------------------------


    // --- 기존 데이터 Fetch 로직 ---
    
    // day_titles 호출
    useEffect(() => {
        if (!token) return; 
        fetchWithAuth('http://localhost:8000/api/schedules/day_titles')
          .then(res => res.json())
          .then(data => {
            setDayTitles(data.map(d => d.day_title)); 
            if (data.length > 0 && !selectedDayTitle) {
                setSelectedDayTitle(data[0].day_title);
                if (onDayTitleChange) onDayTitleChange(data[0].day_title);
            }
          })
          .catch(err => { console.error("❌ day_titles fetch 실패:", err.message); });
    }, [token, fetchWithAuth, onDayTitleChange]);

    // schedule 상세 가져오기 
useEffect(() => {
  if (!scheduleId || !token) return;

  fetchWithAuth(`http://localhost:8000/api/schedules/${scheduleId}`)
    .then(res => res.json())
    .then(data => {
      const dayTitle = data.day_title || '';
      setSelectedDayTitle(dayTitle);
      if (onDayTitleChange) onDayTitleChange(dayTitle);

      setDescription(data.description || '');
    })
    .catch(err => console.error("❌ Schedule fetch 실패:", err.message));
}, [scheduleId, token, fetchWithAuth, onDayTitleChange]);


    // description 갱신
    useEffect(() => {
        if (!selectedDayTitle || !token) return;
        fetchWithAuth(
          `http://localhost:8000/api/schedules/description?day_title=${encodeURIComponent(selectedDayTitle)}`
        )
          .then(res => res.json())
          .then(data => {
            setDescription(data.description || '');
          })
          .catch(err => console.error("❌ description fetch 실패:", err.message));
    }, [selectedDayTitle, token, fetchWithAuth]);

    
    // --- 핸들러 함수들 ---
    
    // description 저장
    const handleSave = () => {
        if (!selectedDayTitle || !token) return;

        fetchWithAuth(
          `http://localhost:8000/api/schedules/update_description?day_title=${encodeURIComponent(selectedDayTitle)}&description=${encodeURIComponent(description)}`,
          { method: "PUT" }
        )
          .then(res => res.json())
          .then((data) => {
            console.log("✅ 저장 성공:", data);
          })
          .catch(err => {
            console.error("❌ 저장 실패", err.message);
          });
    };

    const handleDayTitleChange = (e) => {
        const newDayTitle = e.target.value;
        setSelectedDayTitle(newDayTitle);
        if (onDayTitleChange) {
            onDayTitleChange(newDayTitle);
        }
    };
    
    // 셀 값 가져오기
    const getCellValue = (time, day) => {
        const key = `${time}-${day}`; 
        return cellData[key] || '';
    };
    
    // 셀 값 변경하기
    const handleCellChange = (time, day, value) => {
        const key = `${time}-${day}`;
        setCellData(prev => ({
            ...prev,
            [key]: value
        }));
    };
    
    // 행 추가
    const handleAddRow = () => {
        const sortedTimes = [...scheduleTimes].sort((a, b) => {
            return new Date(`2000/01/01 ${a}`) - new Date(`2000/01/01 ${b}`);
        });
        
        let newTime;
        if (sortedTimes.length > 0) {
            const lastTimeStr = sortedTimes[sortedTimes.length - 1];
            const [hourStr, minuteStr] = lastTimeStr.split(':');
            let hour = parseInt(hourStr);
            let minute = parseInt(minuteStr);
            hour = (hour + 1) % 24; 
            newTime = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
        } else {
            newTime = '09:00'; 
        }

        if (scheduleTimes.includes(newTime)) {
             const [hourStr, minuteStr] = newTime.split(':');
             const minute = parseInt(minuteStr) + 1;
             newTime = `${hourStr}:${String(minute).padStart(2, '0')}`;
        }

        const updatedTimes = [...scheduleTimes, newTime].sort((a, b) => {
            return new Date(`2000/01/01 ${a}`) - new Date(`2000/01/01 ${b}`);
        });
        setScheduleTimes(updatedTimes);
    };
    
    const toggleDeletionMode = () => { setIsDeletionModeActive(prev => !prev); };
    
    // 행 삭제
    const handleRemoveTimeSlot = useCallback((timeToRemove) => {
        if (!isDeletionModeActive) return;
        if (window.confirm(`정말로 ${timeToRemove} 라인(행)을 삭제하시겠습니까?`)) {
            setScheduleTimes(scheduleTimes.filter(time => time !== timeToRemove));
            setCellData(prevData => {
                const newData = { ...prevData };
                scheduleDays.forEach(day => { delete newData[`${timeToRemove}-${day}`]; });
                return newData;
            });
        }
    }, [isDeletionModeActive, scheduleTimes, scheduleDays]);

    // 열 삭제
    const handleRemoveColumn = useCallback((columnToRemove) => {
        if (!isDeletionModeActive) return;
        if (window.confirm(`정말로 항목(열) '${columnToRemove}'을(를) 삭제하시겠습니까?`)) {
            setScheduleDays(scheduleDays.filter(day => day !== columnToRemove));
            setCellData(prevData => {
                const newData = { ...prevData };
                scheduleTimes.forEach(time => { delete newData[`${time}-${columnToRemove}`]; });
                return newData;
            });
        }
    }, [isDeletionModeActive, scheduleDays, scheduleTimes]);
    
    const handleAddColumn = () => {
        const newColumn = prompt("추가할 항목(열 이름)을 입력해주세요:");
        if (newColumn && !scheduleDays.includes(newColumn)) {
            setScheduleDays([...scheduleDays, newColumn]);
        } else if (newColumn) {
            alert(`항목 '${newColumn}'은 이미 존재합니다.`);
        }
    };
    
    const handleDownloadCSV = () => {
        const header = ["Time", ...scheduleDays].join(",");
        
        const rows = scheduleTimes.map(time => {
            const safeTime = `${time}`; 
            const rowData = scheduleDays.map(day => {
                let value = getCellValue(time, day) || "";
                if (value.includes(',') || value.includes('"')) {
                    value = `"${value.replace(/"/g, '""')}"`;
                }
                if (!value.startsWith('"') && value.trim().length > 0) {
                    value = `"${value}"`;
                }
                return value;
            });
            return [safeTime, ...rowData].join(",");
        });

        const csvContent = [header, ...rows].join("\n");
        const BOM = "\uFEFF";
        const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });

        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `${selectedDayTitle || 'Schedule'}_Details.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // Drag & Drop 처리
    const onDragEnd = (result) => {
        const { source, destination, type } = result;
        if (!destination || isDeletionModeActive) return;

        if (type === 'ROW') {
            const newTimes = Array.from(scheduleTimes);
            const [removed] = newTimes.splice(source.index, 1);
            newTimes.splice(destination.index, 0, removed);
            setScheduleTimes(newTimes);
        }

        if (type === 'COLUMN') {
            const newDays = Array.from(scheduleDays);
            const [removed] = newDays.splice(source.index, 1);
            newDays.splice(destination.index, 0, removed);
            setScheduleDays(newDays);
        }
    };

    return (
        <div className="kschedule-container">
            <header className="kschedule-header">
                <h1>🗓️ Schedule Management and Editor</h1>
                {isLoadingDestinations && <p style={{color: '#007bff'}}>⏳ 목적지 데이터를 불러오는 중...</p>}
            </header>

            {authError && (
                <div className="kdh-error-message">
                    <p>🛑 **에러:** {authError}</p>
                    {authError.includes('로그인') && <p>잠시 후 메인 페이지로 이동합니다...</p>}
                </div>
            )}

            {!authError && (
                <>
                    {/* 상단: Details */}
                    <div className="kschedule-details">
                        <label>Day Title</label>
                        <select
                            className="kschedule-select"
                            value={selectedDayTitle}
                            onChange={handleDayTitleChange}
                        >
                            {dayTitles.length === 0 && <option value="">No Schedule!</option>}
                            {dayTitles.map((day) => (
                                <option key={day} value={day}>{day}</option>
                            ))}
                        </select>

                        <label>Description</label>
                        <textarea
                            rows={1}
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                        />

                        <button className="kschedule-btn-success" onClick={handleSave}>
                            ✅ Save
                        </button>
                    </div>
                    
                    {/* 툴바 */}
                    <div className="kschedule-toolbar">
                        <button onClick={handleAddRow} className="kschedule-btn-primary">➕ Add Row</button>
                        
                        <button 
                            onClick={toggleDeletionMode} 
                            style={{ background: isDeletionModeActive ? '#ef4444' : '#cc0000', color: 'white' }}
                            className="kschedule-btn-danger"
                        >
                            <Trash2 size={16} style={{ marginRight: isDeletionModeActive ? '0' : '0.5rem' }} /> 
                            {isDeletionModeActive ? 'Deletion Mode (ON)' : 'Deletion Mode (OFF)'}
                        </button>
                        
                        <button onClick={handleAddColumn} className="kschedule-btn-secondary">➕ Add Columns</button>
                        <button onClick={handleDownloadCSV} className="kschedule-btn-info">📥 CSV Download</button>
                    </div>

                    
                    {/* 테이블 (DragDropContext 적용) */}
                    <div className="kschedule-table-wrapper">
                        <DragDropContext onDragEnd={onDragEnd}>
                            <table className="kschedule-table">
                                {/* -----------------------
                                    헤더: 열 드래그 가능
                                   ----------------------- */}
                                <Droppable droppableId="droppable-columns" direction="horizontal" type="COLUMN">
                                    {(provided) => (
                                        <thead ref={provided.innerRef} {...provided.droppableProps}>
                                            <tr>
                                                {/* 시간 헤더: 드래그 핸들 아님 (삭제 모드 클릭으로 처리) */}
                                                <th className={isDeletionModeActive ? 'kschedule-delete-mode' : ''}>Time</th>

                                                {scheduleDays.map((day, idx) => (
                                                    <Draggable
                                                        key={`col-${day}-${idx}`}
                                                        draggableId={`col-${day}-${idx}`}
                                                        index={idx}
                                                        isDragDisabled={isDeletionModeActive} // 삭제 모드면 드래그 비활성화
                                                    >
                                                        {(provided, snapshot) => (
                                                            <th
                                                                ref={provided.innerRef}
                                                                {...provided.draggableProps}
                                                                {...provided.dragHandleProps}
                                                                className={isDeletionModeActive ? 'kschedule-column-header-deletable' : ''}
                                                                onClick={() => handleRemoveColumn(day)}
                                                                style={{
                                                                    // 드래그 중 약간 시각적 변화 (기본 스타일 유지)
                                                                    ...provided.draggableProps.style
                                                                }}
                                                            >
                                                                {day}
                                                            </th>
                                                        )}
                                                    </Draggable>
                                                ))}

                                                {provided.placeholder}
                                            </tr>
                                        </thead>
                                    )}
                                </Droppable>

                                {/* -----------------------
                                    바디: 행(시간) 드래그 가능
                                   ----------------------- */}
                                <Droppable droppableId="droppable-rows" type="ROW">
                                    {(provided) => (
                                        <tbody ref={provided.innerRef} {...provided.droppableProps}>
                                            {scheduleTimes.map((time, ti) => (
                                                <Draggable
                                                    key={`row-${time}-${ti}`}
                                                    draggableId={`row-${time}-${ti}`}
                                                    index={ti}
                                                    isDragDisabled={isDeletionModeActive} // 삭제 모드면 드래그 비활성화
                                                >
                                                    {(provided, snapshot) => (
                                                        <tr
                                                            ref={provided.innerRef}
                                                            {...provided.draggableProps}
                                                            // 스타일은 기본 유지
                                                        >
                                                            {/* 시간 셀: dragHandle 로 사용 (헤더 잡고 움직일 수 있게), 클릭은 삭제 기능 유지 */}
                                                            <td
                                                                className={`kschedule-time-cell ${isDeletionModeActive ? 'kschedule-time-cell-deletable' : ''}`}
                                                                {...provided.dragHandleProps}
                                                                onClick={() => handleRemoveTimeSlot(time)}
                                                            >
                                                                {time}
                                                            </td>

                                                            {scheduleDays.map((day, di) => (
                                                                <td 
                                                                    key={di} 
                                                                    className="kschedule-schedule-cell"
                                                                >
                                                                    <input
                                                                        type="text"
                                                                        value={getCellValue(time, day)}
                                                                        onChange={(e) => handleCellChange(time, day, e.target.value)}
                                                                        className="kschedule-cell-input"
                                                                        placeholder=" "
                                                                    />
                                                                </td>
                                                            ))}
                                                        </tr>
                                                    )}
                                                </Draggable>
                                            ))}

                                            {provided.placeholder}
                                        </tbody>
                                    )}
                                </Droppable>
                            </table>
                        </DragDropContext>
                    </div>
                </>
            )}
        </div>
    );
};

export default ScheduleTable;
