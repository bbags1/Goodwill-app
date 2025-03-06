import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './Login';
import Welcome from './Welcome';
import ProductList from './ProductList';
import ProductGrid from './ProductGrid'; // Import the ProductGrid component
import Search from './Search'; // Import your Search component
import Settings from './Settings'; // Import the Settings component
import Header from './Header'; // Import your Header component
import './App.css';

function App() {
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [showWelcome, setShowWelcome] = useState(false);

    const handleLogin = () => {
        setIsLoggedIn(true);
        setShowWelcome(true);
        setTimeout(() => setShowWelcome(false), 4000);
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
                    <Header />
                    <Routes>
                        <Route path="/ProductList" element={<ProductList />} />
                        <Route path="/ProductGrid" element={<ProductGrid />} />
                        <Route path="/Search" element={<Search />} />
                        <Route path="/Settings" element={<Settings />} />
                        <Route path="*" element={<Navigate to="/ProductGrid" />} />
                    </Routes>
                </div>
            ) : (
                <Login onLogin={handleLogin} />
            )}
        </div>
    );
}

export default App;