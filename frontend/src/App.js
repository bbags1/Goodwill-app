import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './Login';
import Welcome from './Welcome';
import ProductList from './ProductList';
import Settings from './Settings'; // Import the Settings component
import Header from './Header'; // Import your Header component
import './App.css';

function App() {
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [showWelcome, setShowWelcome] = useState(false);

    // Check localStorage for login state on app load
    useEffect(() => {
        const savedLoginState = localStorage.getItem('isLoggedIn');
        if (savedLoginState === 'true') {
            setIsLoggedIn(true);
        }
    }, []);

    const handleLogin = () => {
        setIsLoggedIn(true);
        localStorage.setItem('isLoggedIn', 'true');
        setShowWelcome(true);
        setTimeout(() => setShowWelcome(false), 4000);
    };

    const handleLogout = () => {
        setIsLoggedIn(false);
        localStorage.removeItem('isLoggedIn');
    };

    return (
        <div>
            {isLoggedIn ? (
                <div>
                    {showWelcome && (
                        <div className="modal">
                            <Welcome />
                        </div>
                    )}
                    <Header onLogout={handleLogout} />
                    <Routes>
                        <Route path="/ProductList" element={<ProductList />} />
                        <Route path="/Settings" element={<Settings />} />
                        <Route path="*" element={<Navigate to="/ProductList" />} />
                    </Routes>
                </div>
            ) : (
                <Login onLogin={handleLogin} />
            )}
        </div>
    );
}

export default App;