import React, { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

// Componentes y Páginas
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import Login from "./components/Login";
import Dashboard from "./pages/Dashboard";
import Usuarios from "./pages/Usuarios";
import Garantias from "./pages/Garantias";
import RequestReset from "./pages/RequestReset";
import ResetPassword from "./pages/ResetPassword";
import Unidades from "./pages/Unidades";
import Verificaciones from "./pages/Verificaciones";
import ChoferFallas from "./pages/ChoferFallas";
import AdminSolicitudes from "./pages/AdminSolicitudes";
import ListaSolicitudes from "./components/Lista_solicitudeschofer";
import FallasMecanicas from "./pages/FallasMecanicas";
import { NotificationProvider } from "./components/NotificationContext";
import HistorialPlacas from "./pages/historial_placas";
import Placas from "./pages/Placas";
import RegistroPago from "./pages/Refrendo_tenencia";
import HistorialRefrendo from "./pages/Historial_refrendo_tenecia";
import Swal from "sweetalert2";

// Estilos
import "./App.css";
import "bootstrap/dist/css/bootstrap.min.css";
import BotonAlertas from "./pages/botonespruebas";
import HistorialVerificaciones from "./pages/Historial_verificaciones";
import Mantenimientos from "./pages/Mantenimientos";
import TiposMantenimiento from "./pages/TiposMantenimientos";
import FrecuenciasPorMarca from "./pages/FrecuenciasPorMarca";
import MantenimientosProgramados from "./pages/MantenimientosProgramados";
import Asignaciones from "./pages/Asignaciones";
import CalendarioAnual from "./pages/Calendario";
import HistorialGarantias from "./pages/Historial_garantias";
import HistorialAsignaciones from "./pages/Historial_asignaciones";
import ListaSolicitudesEdicion from "./pages/SolicitudesPendientes";
import Mensajeschofer from "./pages/mensajes_chofer";
import DatosChoferUnidad from "./pages/DatosChoferUnidad";
import Empresas from "./pages/empresa";
import Sucursales from "./pages/sucursales";
import CambiarContraseña from "./pages/Cambiarcontrasenia";
import Alertas from "./pages/Alertas";
import HistorialMantenimientos from "./pages/mantenimientos_realizados";
import MantenimientosMayores from "./pages/mantenimeintosmayores";

//import Mensajeschofer from "./pages/chofer_mensajes";
// ====================================================
// CONTENIDO PRINCIPAL DE LA APP
// ====================================================
function AppContent({ isLoggedIn, onLogin, onLogout, loading, usuarioId }) {
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [rol, setRol] = useState(null);
  const toggleSidebar = () => setSidebarVisible(!sidebarVisible);
const [showChangePassword, setShowChangePassword] = useState(false);

  // Recuperar rol al cargar
  useEffect(() => {
    const userRol = localStorage.getItem("rol");
    
    setRol(userRol);
  }, [isLoggedIn]);

  // === AUTO LOGOUT POR INACTIVIDAD ===
  useEffect(() => {
    if (!isLoggedIn) return;

    const AUTO_LOGOUT_TIME = 60 * 60 * 1000; // 1 hora
    let logoutTimer;

    const resetTimer = () => {
      clearTimeout(logoutTimer);
      logoutTimer = setTimeout(() => {
        onLogout();
        Swal.fire({
          title: "Sesión Expirada",
          text: "Has sido desconectado por inactividad.",
          icon: "warning",
          confirmButtonColor: "#dc3545",
          timer: 5000,
          timerProgressBar: true,
        });
      }, AUTO_LOGOUT_TIME);
    };

    window.addEventListener("mousemove", resetTimer);
    window.addEventListener("keydown", resetTimer);
    window.addEventListener("scroll", resetTimer);
    window.addEventListener("click", resetTimer);

    resetTimer();
    return () => {
      clearTimeout(logoutTimer);
      window.removeEventListener("mousemove", resetTimer);
      window.removeEventListener("keydown", resetTimer);
      window.removeEventListener("scroll", resetTimer);
      window.removeEventListener("click", resetTimer);
    };
  }, [isLoggedIn, onLogout]);

  if (loading) return <div className="centered-loader">Cargando...</div>;

  return (
    <div className="app-container">
      {isLoggedIn ? (
        <>
          {sidebarVisible && <Sidebar />}
          <div className={`main-content ${sidebarVisible ? "" : "full-width"}`}>
          <Header onLogout={onLogout} toggleSidebar={toggleSidebar} />

            <div className="content">
              <Routes>
                {/* Rutas generales solo si no es chofer */}
                {rol !== "chofer" && (
                  <>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/usuarios" element={<Usuarios />} />
                    <Route path="/garantias" element={<Garantias />} />
                    <Route path="/verificaciones" element={<Verificaciones />} />
                    <Route path="/unidades" element={<Unidades />} />
                    <Route path="/admin/solicitudes" element={<AdminSolicitudes />} />
                    <Route path="/fallasmecanicas" element={<FallasMecanicas />} />
                    <Route path="/registropago" element={<RegistroPago />} />
                    <Route path="/placas" element={<Placas />} />
                    <Route path="/historialplacas" element={<HistorialPlacas />} />
                    <Route path="/historialrefrendo" element={<HistorialRefrendo />} />
                    <Route path="/botones" element={<BotonAlertas />} />
                    <Route path="/historialverificaciones" element={<HistorialVerificaciones />} />
                    <Route path="/mantenimientos" element={<Mantenimientos />} />
                    <Route path="/tipos_mantenimientos" element={<TiposMantenimiento />} />
                    <Route path="/frecuencia_mantenimiento" element={<FrecuenciasPorMarca />} />
                    <Route path="/mantenimientos_programado" element={<MantenimientosProgramados />} />
                    <Route path="/Asignaciones" element={<Asignaciones />} />
                    <Route path="/Calendario" element={<CalendarioAnual />} />
                    <Route path="/HistorialGarantias" element={<HistorialGarantias />} />
                    <Route path="/Historialasignaciones" element={<HistorialAsignaciones />} />
                    <Route path="/Empresas" element={<Empresas />} />
                    <Route path="/Sucursales" element={<Sucursales />} />
                    <Route path="/Mantenimientos_realizados" element={<HistorialMantenimientos />} />
                    <Route path="/mayores" element={<MantenimientosMayores />} />

                  </>
                )}

                {/* Rutas solo para chofer */}
                {(rol === "chofer" || rol === "admin" || rol === "usuario") && (
                  <>
                    <Route path="/chofer/solicitudes" element={<ChoferFallas usuarioId={usuarioId} />} />
                    <Route path="/chofer/listasolicitudes" element={<ListaSolicitudes usuarioId={usuarioId} />} />
                    <Route path="/Solicitudespendiente" element={<ListaSolicitudesEdicion />} />
                    <Route path="/chat_chofer" element={<Mensajeschofer />} />
                    <Route path="/Datoschfer" element={<DatosChoferUnidad />} />
                    <Route path="/Cambiarcontra" element={<CambiarContraseña usuarioId={usuarioId} />} />
                    <Route path="/Alertas" element={<Alertas />} />
       


                  </>
                )}


                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>

            </div>
          </div>
        </>
      ) : (
        <div className="full-screen-login">
          <Routes>
            <Route path="/login" element={<Login onLogin={onLogin} />} />
            <Route path="/request-reset" element={<RequestReset />} />
            <Route path="/reset-password/:token" element={<ResetPassword />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </div>
      )}
    </div>
  );
}


// ====================================================
// COMPONENTE PRINCIPAL APP
// ====================================================
export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [usuarioId, setUsuarioId] = useState(null);
  const [loading, setLoading] = useState(true);

  // Al iniciar la app, recuperar estado de sesión
  useEffect(() => {
    const loggedIn = localStorage.getItem("isLoggedIn") === "true";
    const id = localStorage.getItem("usuarioId");
    setIsLoggedIn(loggedIn);
    setUsuarioId(id);
    setLoading(false);
  }, []);

  // Cuando inicia sesión correctamente
  const handleLogin = () => {
    setIsLoggedIn(true);
    setUsuarioId(localStorage.getItem("usuarioId"));
    


  };

const handleLogout = () => {
  localStorage.removeItem("isLoggedIn");
  localStorage.removeItem("usuarioId");
  localStorage.removeItem("rol"); // 👈 limpia el rol también
  setIsLoggedIn(false);
  setUsuarioId(null);
};


  return (
    <NotificationProvider>
    <Router>
      <AppContent
        isLoggedIn={isLoggedIn}
        onLogin={handleLogin}
        onLogout={handleLogout}
        usuarioId={usuarioId}
        loading={loading}
      />
    </Router>
    </NotificationProvider>
  );
}
