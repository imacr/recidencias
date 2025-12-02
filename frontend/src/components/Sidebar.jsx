import React, { useState, useEffect, useContext } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import logo from "../assets/logo.jpg";
import "./Sidebar.css";
import { NotificationContext } from "./NotificationContext";

const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [showDashboardSubmenu, setShowDashboardSubmenu] = useState(false);
  const [showMantenimientosSubmenu, setShowMantenimientosSubmenu] = useState(false);
  const [showHistorialSubmenu, setShowHistorialSubmenu] = useState(false);
  const [showChoferSubmenu, setShowChoferSubmenu] = useState(false);
  const navigate = useNavigate();
  const { pendientes } = useContext(NotificationContext);
  const { alertasPendientes } = useContext(NotificationContext);
  const { mensajesNuevos } = useContext(NotificationContext);

  const [rol, setRol] = useState(null);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener("resize", handleResize);
    const userRol = localStorage.getItem("rol");
    setRol(userRol);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const toggleSidebar = () => setIsOpen(!isOpen);
  const toggleSubmenu = (submenu, setSubmenu) => setSubmenu(!submenu);

  return (
    <>
      {isMobile && (
        <button className="menu-btn" onClick={toggleSidebar}>
          <i className="fa-solid fa-house"></i>
        </button>
      )}
      {isMobile && isOpen && <div className="overlay" onClick={toggleSidebar}></div>}

      <div className={`sidebar ${isMobile ? (isOpen ? "open" : "") : ""}`}>
        <div className="sidebar-header">
          <img src={logo} alt="Logo" className="logo" />
          {isMobile && <button className="close-btn" onClick={toggleSidebar}></button>}
        </div>

        <nav className="sidebar-menu">

          {/* === Dashboard === */}
          {(rol === "admin" || rol === "usuario") && (
            <div className="menu-item">
              <NavLink
                to="/"
                className={({ isActive }) => (isActive ? "active" : "")}
                onClick={() => toggleSubmenu(showDashboardSubmenu, setShowDashboardSubmenu)}
              >
                <i className="fa fa-th-large"></i> Dashboard
                <i
                  className={`fa submenu-toggle fa-chevron-${showDashboardSubmenu ? "down" : "right"}`}
                  style={{ marginLeft: "auto" }}
                ></i>
              </NavLink>
              {showDashboardSubmenu && (
                <div className="submenu">
                  <NavLink to="/" className={({ isActive }) => (isActive ? "active" : "")}>
                    <i className="fa fa-bar-chart"></i> Reportes
                  </NavLink>
                </div>
              )}
            </div>
          )}

          {/* === Solicitudes (admin) === */}
          {(rol === "admin" || rol === "usuario") && (
            <NavLink to="/admin/solicitudes" className={({ isActive }) => (isActive ? "active" : "")}>
              <i className="fa fa-line-chart"></i> Solicitudes
              {pendientes > 0 && <span className="notification-badge">{pendientes}</span>}
            </NavLink>
          )}

          {/* === Unidades y Usuarios === */}
          {(rol === "admin" || rol === "usuario") && (
            <>
              <NavLink to="/unidades" className={({ isActive }) => (isActive ? "active" : "")}>
                <i className="fa fa-car"></i> Unidades
              </NavLink>
              <NavLink to="/placas" className={({ isActive }) => (isActive ? "active" : "")}>
                <i className="fa-solid fa-clipboard-check"></i> Placas
              </NavLink>
              <NavLink to="/registropago" className={({ isActive }) => (isActive ? "active" : "")}>
                <i className="fa-solid fa-clipboard-check"></i> Tenencia y Refrendo
              </NavLink>
                <NavLink to="/Asignaciones" className={({ isActive }) => (isActive ? "active" : "")}>
                <i className="fa-solid fa-clipboard-check"></i> Asignaciones
              </NavLink>
              
              <NavLink to="/garantias" className={({ isActive }) => (isActive ? "active" : "")}>
                <i className="fa-solid fa-file-lines"></i> Pólizas
              </NavLink>
              <NavLink to="/verificaciones" className={({ isActive }) => (isActive ? "active" : "")}>
                <i className="fa-solid fa-clipboard-check"></i> Verificaciones
              </NavLink>
              

              <NavLink to="/Calendario" className={({ isActive }) => (isActive ? "active" : "")}>
                <i className="fa-solid fa-clipboard-check"></i> Calendario
              </NavLink>
              <NavLink to="/usuarios" className={({ isActive }) => (isActive ? "active" : "")}>
                <i className="fa fa-users"></i> Usuarios
              </NavLink>
              <NavLink to="/Empresas" className={({ isActive }) => (isActive ? "active" : "")}>
                      <i className="fa fa-file-text"></i> Empresa
              </NavLink>
              <NavLink to="/Sucursales" className={({ isActive }) => (isActive ? "active" : "")}>
                      <i className="fa fa-file-text"></i> Sucursales
              </NavLink>


              {/* === Mantenimientos === */}
              <div className="menu-item">
                <NavLink
                  to="#"
                  className={({ isActive }) => (isActive ? "active" : "")}
                  onClick={() => toggleSubmenu(showMantenimientosSubmenu, setShowMantenimientosSubmenu)}
                >
                  <i className="fa fa-cogs"></i> Mantenimientos
                  <i
                    className={`fa submenu-toggle fa-chevron-${showMantenimientosSubmenu ? "down" : "right"}`}
                    style={{ marginLeft: "auto" }}
                  ></i>
                </NavLink>
                {showMantenimientosSubmenu && (
                  <div className="submenu">
                    
                    <NavLink to="/mantenimientos_programado" className={({ isActive }) => (isActive ? "active" : "")}>
                      <i className="fa fa-gear"></i> Mantenimientos menores progremados
                    </NavLink>
                    <NavLink to="/mayores" className={({ isActive }) => (isActive ? "active" : "")}>
                      <i className="fa fa-gear"></i> Mantenimientos mayores progremados
                    </NavLink>
                    <NavLink to="/fallasmecanicas" className={({ isActive }) => (isActive ? "active" : "")}>
                      <i className="fa fa-car"></i> Fallas Mecánicas
                    </NavLink>
                    
                  </div>
                )}
              </div>

              {/* === Historiales === */}
              <div className="menu-item">
                <NavLink
                  to="#"
                  className={({ isActive }) => (isActive ? "active" : "")}
                  onClick={() => toggleSubmenu(showHistorialSubmenu, setShowHistorialSubmenu)}
                >
                  <i className="fa fa-folder-open"></i> Historiales
                  <i
                    className={`fa submenu-toggle fa-chevron-${showHistorialSubmenu ? "down" : "right"}`}
                    style={{ marginLeft: "auto" }}
                  ></i>
                </NavLink>
                {showHistorialSubmenu && (
                  <div className="submenu">
                    <NavLink to="/historialverificaciones" className={({ isActive }) => (isActive ? "active" : "")}>
                      <i className="fa fa-users"></i> Verificaciones
                    </NavLink>
                    <NavLink to="/fallasmecanicas" className={({ isActive }) => (isActive ? "active" : "")}>
                      <i className="fa fa-cogs"></i> Fallas Mecánicas
                    </NavLink>
                    <NavLink to="/Mantenimientos_realizados" className={({ isActive }) => (isActive ? "active" : "")}>
                      <i className="fa fa-wrench"></i> Mantenimientos
                    </NavLink>
                    <NavLink to="/HistorialGarantias" className={({ isActive }) => (isActive ? "active" : "")}>
                      <i className="fa fa-file-text"></i> Pólizas
                    </NavLink>
                    <NavLink to="/historialplacas" className={({ isActive }) => (isActive ? "active" : "")}>
                      <i className="fa fa-file-text"></i> Placas
                    </NavLink>
                    <NavLink to="/historialrefrendo" className={({ isActive }) => (isActive ? "active" : "")}>
                      <i className="fa fa-file-text"></i> Refrendo y Tenencia
                    </NavLink>
                    <NavLink to="/Historialasignaciones" className={({ isActive }) => (isActive ? "active" : "")}>
                      <i className="fa fa-file-text"></i> Asignaciones
                    </NavLink>
                                       
                  </div>
                )}
              </div>
            </>
          )}

          {/* === Acciones Chofer (admin también puede ver) === */}
          {(rol === "chofer" || rol === "admin" || rol === "usuario") && (
            <div className="menu-item">
             <NavLink
              to="/Datoschfer"
              end
              className={({ isActive }) => (isActive ? "active" : "")}
              onClick={() => toggleSubmenu(showChoferSubmenu, setShowChoferSubmenu)}
            >
              <i className="fa fa-folder-open"></i> Acciones Chofer
              <i
                className={`fa submenu-toggle fa-chevron-${showChoferSubmenu ? "down" : "right"}`}
                style={{ marginLeft: "auto" }}
              ></i>
              {mensajesNuevos > 0 && <span className="notification-badge">{mensajesNuevos}</span>}

            </NavLink>

              {showChoferSubmenu && (
                <div className="submenu">
                  <NavLink to="/chofer/solicitudes" className={({ isActive }) => (isActive ? "active" : "")}>
                    <i className="fa fa-users"></i> Solicitud
                  </NavLink>
                  <NavLink to="Solicitudespendiente" className={({ isActive }) => (isActive ? "active" : "")}>
                    <i className="fa fa-cogs"></i> Solicitudes realizadas
                  </NavLink>
                  <NavLink to="/chat_chofer" className={({ isActive }) => (isActive ? "active" : "")}>
                    <i className="fa fa-cogs"></i> Chats
                    {mensajesNuevos > 0 && <span className="notification-badge">{mensajesNuevos}</span>}

                  </NavLink>

                </div>
              )}
              <NavLink to="/botones" className={({ isActive }) => (isActive ? "active" : "")}>
                <i className="fa-solid fa-clipboard-check"></i> Pruebas
              </NavLink>
            

            </div>
          )}
          {/* === Acciones Chofer (admin también puede ver) === */}
          {(rol === "admin" || rol === "usuario") && (
            <div className="menu-item">
             <NavLink
              to="#"
              end
              className={({ isActive }) => (isActive ? "active" : "")}
              onClick={() => toggleSubmenu(showChoferSubmenu, setShowChoferSubmenu)}
            >
              <i className="fa fa-folder-open"></i> Panel de configuracion
              <i
                className={`fa submenu-toggle fa-chevron-${showChoferSubmenu ? "down" : "right"}`}
                style={{ marginLeft: "auto" }}
              ></i>

            </NavLink>

              {showChoferSubmenu && (
                <div className="submenu">
                  <NavLink to="/tipos_mantenimientos" className={({ isActive }) => (isActive ? "active" : "")}>
                      <i className="fa fa-wrench"></i> Tipos de mantenimientos
                    </NavLink>
                    <NavLink to="/frecuencia_mantenimiento" className={({ isActive }) => (isActive ? "active" : "")}>
                      <i className="fa fa-history"></i> Frecuencia por marca
                    </NavLink>

                </div>
              )}
            </div>
          )}
        </nav>
      </div>
    </>
  );
};

export default Sidebar;


