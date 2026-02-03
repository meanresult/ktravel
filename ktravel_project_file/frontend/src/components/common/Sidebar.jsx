import React from 'react';
import './Sidebar.css';
import { Link } from 'react-router-dom';
import { FaStar, FaMusic, FaThLarge, FaCompass, FaCalendar, FaBookmark, FaComments   } from 'react-icons/fa';


const Sidebar = () => {
    return (
        <div className="sidebar">
            {/* 상단 헤더 */}
            <div className="sidebar-header">
                {/* 햄버거 메뉴 아이콘 */}
                <div className="menu-icon">
                </div>
                {/* 제목 */}
                <h1>K-Guidance Menu</h1>
            </div>

                    <li>
                    <Link to="/" >
     <FaThLarge />
    
   <span>HOME</span> 
         </Link>
                    </li>
                    <li>
                        <Link to="/chatbot/demon-hunters">
                            <FaComments />
                            <span>K-chat</span>
                        </Link>
                    </li>
                    <li>
                        <Link to="/k-spotlight">
                            <FaStar />
                            <span>media Spotlight</span>
                        </Link>
                    </li>
                    <li>
                        <Link to="/festivals">
                            <FaMusic />
                            <span>Concert</span>
                        </Link>
                    </li>
                      <li>
                        <Link to="/k-pathidea">
                            <FaCompass />
                            <span>Schedules</span>
                        </Link>
                    </li>
                    <li>
                        <Link to="/dashboard">
                            <FaBookmark />
                            <span>Recommendation</span>
                        </Link>
                    </li>
                  
                
            </div>
        
    );
};

export default Sidebar;