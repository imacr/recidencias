import React, { useEffect, useState } from "react";
import { API_URL } from "../config";
import { useNavigate } from "react-router-dom";
import "./Alertas.css";

export default function Alertas() {
  const [alertas, setAlertas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtro, setFiltro] = useState("todas");
  const [porPagina, setPorPagina] = useState(10);
  const [pagina, setPagina] = useState(1);

  const navigate = useNavigate();

  const irASeccion = (alerta) => {
  switch (alerta.tipo_alerta) {
    case "placa":
      navigate("/placas");
      break;
    case "refrendo_tenencia":
      navigate("/registropago");
      break;
    case "verificacion":
      navigate("/verificaciones");
      break;
    default:
      navigate("/alertas");
      break;
  }
};

  useEffect(() => {
    fetchAlertas();
  }, []);

  const fetchAlertas = async () => {
    setLoading(true);
    try {
      const usuarioId = localStorage.getItem("usuarioId");
      if (!usuarioId) throw new Error("No hay usuarioId en localStorage");

      const res = await fetch(`${API_URL}/alertas/usuario/${usuarioId}`);
      const data = await res.json();
      setAlertas(data.alertas || []);
    } catch (err) {
      console.error("Error al cargar alertas:", err);
      setAlertas([]);
    } finally {
      setLoading(false);
    }
  };

  const getEstadoReal = (a) =>
    a.estado === "completada" || a.fecha_resuelta ? "atendida" : a.estado;

  const alertasFiltradas = (() => {
    let base = alertas.filter(
      (a) => filtro === "todas" || getEstadoReal(a) === filtro
    );

    const agrupadas = {};
    base.forEach((a) => {
      const estado = getEstadoReal(a);
      if (estado === "atendida") {
        const u = a.id_unidad;
        if (
          !agrupadas[u] ||
          new Date(a.fecha_resuelta) > new Date(agrupadas[u].fecha_resuelta)
        ) {
          agrupadas[u] = a;
        }
      }
    });

    const atendidas = Object.values(agrupadas);
    const pendientesEnviadas = base.filter(
      (a) => getEstadoReal(a) !== "atendida"
    );

    if (filtro === "atendida") return atendidas;
    if (filtro === "todas") return [...pendientesEnviadas, ...atendidas];
    return base;
  })();

  const totalPaginas =
    porPagina === "all"
      ? 1
      : Math.ceil(alertasFiltradas.length / porPagina);

  const inicio =
    (pagina - 1) *
    (porPagina === "all" ? alertasFiltradas.length : porPagina);

  const fin =
    porPagina === "all" ? alertasFiltradas.length : inicio + porPagina;

  const mostrar = alertasFiltradas.slice(inicio, fin);

  const getStyle = (estado) => {
    switch (estado) {
      case "pendiente":
        return { color: "#e53e3e", bg: "#fff5f5", icon: "⚠️" };
      case "enviada":
        return { color: "#d69e2e", bg: "#fefcbf", icon: "✉️" };
      case "atendida":
        return { color: "#38a169", bg: "#f0fff4", icon: "✅" };
      default:
        return { color: "#1a202c", bg: "#f7fafc", icon: "" };
    }
  };

  return (
    <div className="alertas-container">
      <div className="alertas-header">
        <h2>
          <i className="fa-solid fa-bell"></i> Buzón de alertas
        </h2>
        <div className="alertas-controls">
          <select
            value={filtro}
            onChange={(e) => {
              setFiltro(e.target.value);
              setPagina(1);
            }}
          >
            <option value="todas">Todas</option>
            <option value="pendiente">Pendientes</option>
            <option value="atendida">Completadas</option>
          </select>

          <select
            value={porPagina}
            onChange={(e) => {
              setPorPagina(
                e.target.value === "all" ? "all" : parseInt(e.target.value)
              );
              setPagina(1);
            }}
          >
            <option value={5}>5</option>
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value="all">Todas</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="loader">Cargando...</div>
      ) : mostrar.length === 0 ? (
        <p className="alertas-mensaje">No hay alertas para mostrar.</p>
      ) : (
        <>
          <div className="alertas-grid">
            {mostrar.map((a) => {
              const estado = getEstadoReal(a);
              const style = getStyle(estado);
              return (
                <div
                  className="alerta-card clickable"
                  style={{
                    background: style.bg,
                    borderLeftColor: style.color
                  }}
                  key={a.id_alerta}
                  onClick={() => irASeccion(a)}
                >
                  <div className="alerta-header">
                    <span className="alerta-icon">{style.icon}</span>
                    <span className="alerta-tipo">{a.tipo_alerta}</span>
                  </div>

                  <p className="alerta-desc">{a.descripcion}</p>

                  <div className="alerta-footer">
                    <span>Unidad: {a.id_unidad}</span>
                    <span>
                      Generada:{" "}
                      {new Date(a.fecha_generada).toLocaleDateString()}
                    </span>
                  </div>

                  {a.fecha_resuelta && (
                    <div className="alerta-footer">
                      Resuelta:{" "}
                      {new Date(a.fecha_resuelta).toLocaleDateString()}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {porPagina !== "all" && (
            <div className="paginacion">
              <button
                disabled={pagina === 1}
                onClick={() => setPagina(pagina - 1)}
              >
                <i className="fa-solid fa-angle-left"></i>
              </button>

              <span>
                {pagina} / {totalPaginas}
              </span>

              <button
                disabled={pagina === totalPaginas}
                onClick={() => setPagina(pagina + 1)}
              >
                <i className="fa-solid fa-angle-right"></i>
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
