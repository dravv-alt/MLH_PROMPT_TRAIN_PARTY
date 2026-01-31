import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export function useAuth() {
    return useContext(AuthContext);
}

export function AuthProvider({ children }) {
    const [user, setUser] = useState(() => {
        const storedUser = localStorage.getItem('mlh_user');
        return storedUser ? JSON.parse(storedUser) : null;
    });
    const [loading, setLoading] = useState(false);

    // No need for useEffect just for this initialization anymore


    const signup = (name, pin) => {
        const newUser = { name, pin, joinDate: new Date().toISOString() };
        localStorage.setItem('mlh_user', JSON.stringify(newUser));
        setUser(newUser);
        return true;
    };

    const login = (pin) => {
        const storedUser = JSON.parse(localStorage.getItem('mlh_user'));
        if (storedUser && storedUser.pin === pin) {
            setUser(storedUser);
            return true;
        }
        return false;
    };

    const logout = () => {
        // We don't necessarily clear data, just current session state if we wanted
        // But for local auth, "logout" usually means just clearing the user state so they have to enter PIN again.
        setUser(null);
        // Note: We DO NOT remove 'mlh_user' from localStorage, or they lose their data!
    };

    const userExists = () => {
        return !!localStorage.getItem('mlh_user');
    };

    const value = {
        user,
        signup,
        login,
        logout,
        userExists,
        loading
    };

    return (
        <AuthContext.Provider value={value}>
            {!loading && children}
        </AuthContext.Provider>
    );
}
