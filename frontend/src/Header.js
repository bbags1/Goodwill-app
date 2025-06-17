import React from 'react';
import { Link } from 'react-router-dom';
import './Header.css'; // Import your styles
import logo from './assets/kiras-logo.jpg'; // Update the path to match the actual location of your logo file

function Header() {
    return (
        <header className="header">
            <img src={logo} alt="Logo" className="logo" />
            <nav className="nav-links">
                <Link to="/ProductList">Products</Link>
                <Link to="/Settings">Settings</Link>
            </nav>
        </header>
    );
}

export default Header;