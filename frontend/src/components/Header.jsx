import React, { useState, useEffect, useContext } from "react";
import { useNavigate } from "react-router-dom";
import "./Header.css";
import { NotificationContext } from "./NotificationContext";

const Header = ({ onLogout, toggleSidebar, onChangePassword }) => {
  const { alertasPendientes } = useContext(NotificationContext);

  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [showMenu, setShowMenu] = useState(false);
  const [userName, setUserName] = useState("");

  const navigate = useNavigate();

  // Detectar tamaño de pantalla
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Cargar nombre de usuario
  useEffect(() => {
    const storedUser = localStorage.getItem("usuarioNombre");
    if (storedUser) setUserName(storedUser);
  }, []);

  return (
    <header className="app-header">
      <div className="header-left">
        {!isMobile && (
          <button className="main-action-btn" onClick={toggleSidebar}>
            <i className="fa-solid fa-house"></i>
          </button>
        )}
      </div>

      <div className="header-right">

        {/* Ícono de Alertas con badge */}
        <button 
          className="alert-button"
          onClick={() => navigate("/Alertas")}
          style={{ position: "relative", marginRight: "15px" }}
        >
          <i className="fa fa-bell"></i>

          {alertasPendientes > 0 && (
            <span className="notification-badge-header">
              {alertasPendientes}
            </span>
          )}
        </button>


        <div className="user-menu-container">
          <button
            className="user-menu-btn"
            onClick={() => setShowMenu(!showMenu)}
            style={{ display: "flex", alignItems: "center", gap: "5px" }}
          >
            <i className="fa fa-user"></i>
            {!isMobile && <span>{userName}</span>}
          </button>

          {showMenu && (
            <div className="user-menu-dropdown">
              <button
                className="dropdown-item"
                onClick={() => {
                  setShowMenu(false);
                  onChangePassword();
                }}
              >
                <i className="fa fa-key" /> Cambiar contraseña
              </button>

              <button
                className="dropdown-item"
                onClick={() => {
                  setShowMenu(false);
                  onLogout();
                }}
              >
                <i className="fa fa-sign-out-alt" /> Cerrar sesión
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
