import React, { useState, useEffect } from 'react';
import { MessageCircle, Star, Music, Compass, Bookmark, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import './FeatureShowcase.css'; // CSS 파일 import
import { Link } from 'react-router-dom';

const MotionLink = motion(Link);
const menuCards = [
{
  id: 'K-bot',
  title: 'Chatbot',
  description: "Discover various attractions, popular restaurants, and K-drama filming spots across Korea with ease.",
  icon: <MessageCircle style={{ width: '3rem', height: '3rem', color: 'white' }} strokeWidth={2} />,
  gradient: 'gradient-red',
  IconComponent: MessageCircle,
  path: '/chatbot/demon-hunters'
},
{
  id: 'media-spotlight',
  title: 'Media Spotlight',
  description: "Explore famous K-drama filming locations and find restaurants nearby for a complete experience.",
  icon: <Star style={{ width: '3rem', height: '3rem', color: 'white' }} />,
  gradient: 'gradient-yellow',
  IconComponent: Star,
  path: '/k-spotlight'
},
{
  id: 'concert',
  title: 'Concert',
  description: "Stay updated on upcoming K-pop concerts and live performances, and plan your visit to enjoy them fully.",
  icon: <Music style={{ width: '3rem', height: '3rem', color: 'white' }} />,
  gradient: 'gradient-purple',
  IconComponent: Music,
  path: '/festivals'
},
{
  id: 'schedules',
  title: 'Schedules',
  description: "Intuitively view and adjust your travel itinerary on the map, making it easy to plan each day of your trip.",
  icon: <Compass style={{ width: '3rem', height: '3rem', color: 'white' }} />,
  gradient: 'gradient-green',
  IconComponent: Compass,
  path: '/k-pathidea'
},
{
  id: 'recommendation',
  title: 'Recommendation',
  description: "Receive content suggestions based on your likes to help you discover more interesting places.",
  icon: <Bookmark style={{ width: '3rem', height: '3rem', color: 'white' }} />,
  gradient: 'gradient-blue',
  IconComponent: Bookmark,
  path: '/dashboard'
}

];

const FeatureShowcase = ({ autoPlayInterval = 4000 }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [direction, setDirection] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    if (isPaused) return;
    const interval = setInterval(() => {
      setDirection(1);
      setCurrentIndex(prev => (prev + 1) % menuCards.length);
    }, autoPlayInterval);
    return () => clearInterval(interval);
  }, [currentIndex, autoPlayInterval, isPaused]);

  const handleIconClick = (index) => {
    if (index === currentIndex) return;
    setDirection(index > currentIndex ? 1 : -1);
    setCurrentIndex(index);
    setIsPaused(true);
    setTimeout(() => setIsPaused(false), 8000);
  };

  const handleIconHover = (index) => {
    if (index === currentIndex) return;
    setDirection(index > currentIndex ? 1 : -1);
    setCurrentIndex(index);
  };

  const currentCard = menuCards[currentIndex];

  const cardVariants = {
    enter: (direction) => ({
      x: direction > 0 ? 1000 : -1000,
      opacity: 0
    }),
    center: {
      x: 0,
      opacity: 1
    },
    exit: (direction) => ({
      x: direction > 0 ? -1000 : 1000,
      opacity: 0
    })
  };

  return (
    <div className="feature-showcase-container">
      {/* Card Container */}
      <div className="feature-card-container">
        <AnimatePresence initial={false} custom={direction} mode="wait">
          <motion.div
            key={currentCard.id}
            custom={direction}
            variants={cardVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{
              x: { type: 'spring', stiffness: 300, damping: 30 },
              opacity: { duration: 0.2 }
            }}
            className="feature-card"
          >
            <div className="feature-card-content">
              <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{
                  type: 'spring',
                  stiffness: 200,
                  damping: 15,
                  delay: 0.1
                }}
                className={`feature-icon-circle ${currentCard.gradient}`}
              >
                {currentCard.icon}
              </motion.div>

              <motion.h2
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="feature-title"
              >
                {currentCard.title}
              </motion.h2>

              <motion.p
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="feature-description"
              >
                {currentCard.description}
              </motion.p>

              <MotionLink
                                to={currentCard.path} // ⚠️ path 속성을 사용하여 이동할 URL을 지정합니다.
                                initial={{ y: 20, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                transition={{ delay: 0.4 }}
                                className={`feature-button ${currentCard.gradient}`}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                // onClick 핸들러는 Link 컴포넌트에서는 필요하지 않습니다. (페이지 전환 담당)
                            >
                                GO
                                <ArrowRight style={{ width: '1.25rem', height: '1.25rem' }} />
                            </MotionLink>
                        </div>
                    </motion.div>
                </AnimatePresence>
            </div>

      {/* Icon Navigation */}
      <div className="feature-icon-nav">
        {menuCards.map((card, index) => {
          const IconComponent = card.IconComponent;
          const isActive = index === currentIndex;

          return (
            <motion.button
              key={card.id}
              onClick={() => handleIconClick(index)}
              onMouseEnter={() => handleIconHover(index)}
              className={`feature-icon-button ${isActive ? `active ${card.gradient}` : ''}`}
              whileHover={{ scale: isActive ? 1 : 1.15 }}
              whileTap={{ scale: 0.95 }}
              aria-label={card.title}
              aria-current={isActive}
            >
              {/* Glow effect */}
              {isActive && (
                <motion.div
                  className={`feature-icon-glow ${card.gradient}`}
                  animate={{ opacity: [0.4, 0.8, 0.4] }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: 'easeInOut'
                  }}
                />
              )}

              {/* Icon */}
              <div className={`feature-icon ${isActive ? 'active' : 'inactive'}`}>
                <IconComponent
                  style={{ width: '1.75rem', height: '1.75rem' }}
                  strokeWidth={card.id === 'chatbot' ? 2 : 1.5}
                />
              </div>

              {/* Active ring */}
              {isActive && (
                <motion.div
                  className="feature-active-ring"
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.3 }}
                />
              )}
            </motion.button>
          );
        })}
      </div>
    </div>
  );
};

export default FeatureShowcase;