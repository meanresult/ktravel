import React from 'react';
import Sidebar from '../components/common/Sidebar.jsx';
import KpopFestivalPage from './Kpop_FestivalPage.jsx'; 
import '../styles/KpopFestival_MapLayout.css';

function KpopFestival_MapLayout() {
    return (
        <>
            <Sidebar />
            
            <div className="layout-container">
                <div className="festival-area-full">
                    <KpopFestivalPage isEmbedded={false} />
                </div>
            </div>
        </>
    );
}

export default KpopFestival_MapLayout;