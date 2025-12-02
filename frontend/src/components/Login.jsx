import React, { useState } from 'react';
import { Link, useNavigate } from "react-router-dom";
import logo from '../assets/fibra.png';
import styles from './Login.module.css'; 
import { API_URL } from "../config"; // Ajusta la ruta según la ubicación del archivo

const Login = ({ onLogin }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await fetch(`${API_URL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            });

            const data = await response.json();

           if (response.ok) {
            // Guardar datos de sesión
            const usuarioId = data.user.id;
            const rol = data.user.rol; // 👈 agrega esto

            localStorage.setItem("usuarioId", usuarioId);
            localStorage.setItem("usuarioNombre", data.user.nombre); // 👈 nombre real
            
            localStorage.setItem("isLoggedIn", "true");
            localStorage.setItem("rol", rol); // 👈 guarda el rol

            // Notifica al componente principal
            onLogin(usuarioId);

            // Redirige según rol
             setTimeout(() => {
                if (rol === "admin") navigate("/");
                else if (rol === "chofer") navigate("/Datoschfer");
                else navigate("/"); // fallback
            }, 50);
        }
        else {
                setError(data.error || 'Credenciales inválidas');
            }
        } catch (err) {
            setError('Error de conexión. No se pudo contactar al servidor.');
            console.error('Login fetch error:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.loginContainer}>
            <div className={styles.loginCard}>
                <img className={styles.logo_login} src={logo} alt="Logo FIBRATEC" />
                <h1 className={styles.loginTitle}>Inicio de Sesión</h1>
                
                {error && <p className={styles.errorMessage}>{error}</p>}
                
                <form onSubmit={handleSubmit} className={styles.loginForm}>
                    <div className={styles.inputContainer}>
                        <i className={`fa-solid fa-user ${styles.icon}`}></i>
                        <input
                            type="text"
                            placeholder="Usuario"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                            disabled={loading}
                        />
                    </div>

                    <div className={styles.inputContainer}>
                        <i className={`fa-solid fa-lock ${styles.icon}`}></i>
                        <input
                            type={showPassword ? 'text' : 'password'}
                            placeholder="Contraseña"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            disabled={loading}
                        />
                        <i 
                            className={`fa-solid ${showPassword ? 'fa-eye-slash' : 'fa-eye'} ${styles.passwordToggleIcon}`}
                            onClick={() => setShowPassword(!showPassword)}
                        ></i>
                    </div>

                    <div className={styles.optionsContainer}>
                        <Link to="/request-reset" className={styles.forgotPassword}>
                            ¿Olvidaste tu contraseña?
                        </Link>
                    </div>
                    
                    <button type="submit" disabled={loading} className={styles.loginButton}>
                        {loading ? 'INGRESANDO...' : 'ENTRAR'}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Login;





