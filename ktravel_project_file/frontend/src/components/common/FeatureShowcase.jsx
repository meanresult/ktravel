import React, { useState, useEffect } from 'react';
import { MessageCircle, Star, Music, Compass, Bookmark, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import './FeatureShowcase.css';
import { Link } from 'react-router-dom';

const MotionLink = motion(Link);

const menuCards = [
  {
    id: 'K-bot',
    title: 'Chatbot',
    description: "Discover various attractions, popular restaurants, and K-drama filming spots across Korea with ease.",
    icon: <MessageCircle style={{ width: '2.5rem', height: '2.5rem', color: 'white' }} strokeWidth={2} />,
    gradient: 'gradient-red',
    IconComponent: MessageCircle,
    path: '/chatbot/demon-hunters'
  },
  {
    id: 'media-spotlight',
    title: 'Media Spotlight',
    description: "Explore famous K-drama filming locations and find restaurants nearby for a complete experience.",
    icon: <Star style={{ width: '2.5rem', height: '2.5rem', color: 'white' }} />,
    gradient: 'gradient-yellow',
    IconComponent: Star,
    path: '/k-spotlight'
  },
  {
    id: 'concert',
    title: 'Concert',
    description: "Stay updated on upcoming K-pop concerts and live performances, and plan your visit to enjoy them fully.",
    icon: <Music style={{ width: '2.5rem', height: '2.5rem', color: 'white' }} />,
    gradient: 'gradient-purple',
    IconComponent: Music,
    path: '/festivals'
  },
  {
    id: 'schedules',
    title: 'Schedules',
    description: "Intuitively view and adjust your travel itinerary on the map, making it easy to plan each day of your trip.",
    icon: <Compass style={{ width: '2.5rem', height: '2.5rem', color: 'white' }} />,
    gradient: 'gradient-green',
    IconComponent: Compass,
    path: '/k-pathidea'
  },
  {
    id: 'recommendation',
    title: 'Recommendation',
    description: "Receive content suggestions based on your likes to help you discover more interesting places.",
    icon: <Bookmark style={{ width: '2.5rem', height: '2.5rem', color: 'white' }} />,
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

  // 어두운 배경 스타일
  const darkCardStyle = {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    width: '100%',
    background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
    borderRadius: '1.5rem',
    padding: '2.5rem',
    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.6)',
    border: '2px solid rgba(255, 255, 255, 0.1)'
  };

  return (
    <div className="feature-showcase-container">
      {/* Card Container */}
      <div style={{position: 'relative', minHeight: '450px', margin: '2rem 0'}}>
        <AnimatePresence mode="wait" initial={false} custom={direction}>
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
            style={darkCardStyle}
          >
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
              gap: '1.5rem'
            }}>
              {/* Icon Circle */}
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
                style={{ margin: '0 auto' }}
              >
                {currentCard.icon}
              </motion.div>

              {/* Title */}
              <motion.h2
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2 }}
                style={{
                  fontSize: '2rem',
                  fontWeight: 700,
                  color: 'white',
                  margin: 0,
                  textAlign: 'center',
                  textShadow: '0 2px 4px rgba(0, 0, 0, 0.3)'
                }}
              >
                {currentCard.title}
              </motion.h2>

              {/* Description */}
              <motion.p
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.3 }}
                style={{
                  fontSize: '1.1rem',
                  color: '#cbd5e1',
                  lineHeight: 1.8,
                  maxWidth: '28rem',
                  margin: 0,
                  textAlign: 'center'
                }}
              >
                {currentCard.description}
              </motion.p>

              {/* GO Button */}
              <MotionLink
                to={currentCard.path}
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="feature-button"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                style={{
                  marginTop: '1rem',
                  padding: '0.75rem 2rem',
                  borderRadius: '9999px',
                  color: 'white',
                  fontWeight: 600,
                  fontSize: '1rem',
                  border: 'none',
                  cursor: 'pointer',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  boxShadow: '0 10px 30px rgba(102, 126, 234, 0.4)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  textDecoration: 'none',
                  minWidth: '120px'
                }}
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

              <div className={`feature-icon ${isActive ? 'active' : 'inactive'}`}>
                <IconComponent
                  style={{ width: '1.75rem', height: '1.75rem' }}
                  strokeWidth={card.id === 'chatbot' ? 2 : 1.5}
                />
              </div>

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